from __future__ import annotations

from collections import Counter, deque
from pathlib import Path
from statistics import mean
from typing import Any

from scripts.experiment_utils import write_json_file, write_text_file


def _as_float(value: Any, default: float | None = None) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _nearest_bullets(info: dict[str, Any], limit: int = 10) -> list[dict[str, Any]]:
    state = info.get("state") or {}
    player_x = _as_float(state.get("x"), 0.0) or 0.0
    player_y = _as_float(state.get("y"), 0.0) or 0.0
    bullets = []
    for bullet in info.get("enemy_bullets", []) or []:
        bx = _as_float(bullet.get("x"), 0.0) or 0.0
        by = _as_float(bullet.get("y"), 0.0) or 0.0
        vx = _as_float(bullet.get("xspeed"), 0.0) or 0.0
        vy = _as_float(bullet.get("yspeed"), 0.0) or 0.0
        rel_x = bx - player_x
        rel_y = by - player_y
        distance = (rel_x * rel_x + rel_y * rel_y) ** 0.5
        speed_sq = vx * vx + vy * vy
        time_to_closest = None
        closest_distance = None
        if speed_sq > 0:
            t = max(0.0, -((rel_x * vx) + (rel_y * vy)) / speed_sq)
            closest_x = rel_x + vx * t
            closest_y = rel_y + vy * t
            time_to_closest = t
            closest_distance = (closest_x * closest_x + closest_y * closest_y) ** 0.5
        bullets.append(
            {
                "id": _as_int(bullet.get("id")),
                "rel_x": rel_x,
                "rel_y": rel_y,
                "xspeed": vx,
                "yspeed": vy,
                "distance": distance,
                "approx_time_to_closest": time_to_closest,
                "approx_closest_distance": closest_distance,
            }
        )
    bullets.sort(key=lambda item: item["distance"])
    return bullets[:limit]


def compact_step_snapshot(
    *,
    episode: int,
    policy_action: list[int],
    full_action: list[int],
    info: dict[str, Any],
    previous_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    state = info.get("state") or {}
    movement = info.get("movement_diagnostics") or {}
    nearest = _nearest_bullets(info, limit=1)
    x = _as_float(state.get("x"), 0.0) or 0.0
    prev_x = None if previous_snapshot is None else _as_float(previous_snapshot.get("hero", {}).get("x"))
    return {
        "episode": episode,
        "frame": _as_int(info.get("episode_step_count", info.get("tick"))),
        "hero": {
            "x": x,
            "y": _as_float(state.get("y"), 0.0),
            "vx": _as_float(state.get("xspeed"), 0.0),
            "vy": _as_float(state.get("yspeed"), 0.0),
            "health": _as_int(info.get("player_health", state.get("health", 0))),
            "grounded": bool(info.get("grounded", False)),
            "airborne": not bool(info.get("grounded", False)),
            "ducking": bool(info.get("ducking", False)),
            "jumping": bool(info.get("jumping", False)),
            "boost_ready": bool(info.get("hyperjump_ready", False)),
            "boost_active": bool(state.get("hjump", 0)),
            "boost_cooldown_or_charge": _as_int(state.get("hyperjump", 0)),
        },
        "input": {
            "policy_action": list(policy_action),
            "full_action": list(full_action),
            "horizontal": _as_int(full_action[0]) if len(full_action) > 0 else None,
            "jump": _as_int(full_action[1]) if len(full_action) > 1 else None,
            "duck": _as_int(full_action[2]) if len(full_action) > 2 else None,
            "boost": _as_int(full_action[3]) if len(full_action) > 3 else None,
        },
        "motion": {
            "actual_dx": None if prev_x is None else x - prev_x,
            "frames_pressing_left_at_left_edge": movement.get("frames_pressing_left_at_left_edge"),
            "frames_pressing_right_at_right_edge": movement.get("frames_pressing_right_at_right_edge"),
            "input_motion_mismatch_fields_available": True,
        },
        "edge_terrain": {
            "hero_x": x,
            "distance_to_world_left_edge": None,
            "world_left_edge_available": False,
            "distance_to_world_right_edge": None,
            "world_right_edge_available": False,
            "frames_at_left_edge": movement.get("frames_at_left_edge"),
            "frames_at_right_edge": movement.get("frames_at_right_edge"),
            "at_left_edge_this_frame": None,
            "at_right_edge_this_frame": None,
            "edge_contact_this_frame_available": False,
            "max_consecutive_frames_at_left_edge": movement.get("max_consecutive_frames_at_left_edge"),
            "max_consecutive_frames_at_right_edge": movement.get("max_consecutive_frames_at_right_edge"),
            "obstacle_blockage": None,
            "terrain_blockage_available": False,
            "limitation": "terrain blockage, current-frame edge contact, and canonical world-edge diagnostics require a future simulator-diagnostics task",
        },
        "bullets": {
            "visible_enemy_bullet_count": _as_int(info.get("visible_enemy_bullets_current", len(info.get("enemy_bullets", []) or []))),
            "nearest_enemy_bullet": nearest[0] if nearest else None,
        },
        "damage": {
            "total_player_damage": _as_int(info.get("total_player_damage", 0)),
            "last_player_damage_amount": _as_int(info.get("last_player_damage_amount", 0)),
            "last_player_damage_tick": info.get("last_player_damage_tick"),
        },
    }


class DamageForensicsCollector:
    def __init__(self, *, window: int, runtime_context: dict[str, Any]) -> None:
        self.window = max(1, int(window))
        self.runtime_context = dict(runtime_context)
        self._windows: dict[int, deque[dict[str, Any]]] = {}
        self._last_damage: dict[int, int] = {}
        self._last_boost_frame: dict[int, int | None] = {}
        self._last_grounded_frame: dict[int, int | None] = {}
        self._episode_event_counts: Counter[int] = Counter()
        self.events: list[dict[str, Any]] = []

    def record_step(
        self,
        *,
        episode: int,
        policy_action: list[int],
        full_action: list[int],
        info: dict[str, Any],
        terminated: bool,
        truncated: bool,
    ) -> None:
        window = self._windows.setdefault(episode, deque(maxlen=self.window))
        previous = window[-1] if window else None
        snapshot = compact_step_snapshot(
            episode=episode,
            policy_action=policy_action,
            full_action=full_action,
            info=info,
            previous_snapshot=previous,
        )
        frame = _as_int(snapshot["frame"])
        if snapshot["input"].get("boost") == 1:
            self._last_boost_frame[episode] = frame
        if snapshot["hero"].get("grounded"):
            self._last_grounded_frame[episode] = frame

        previous_total = self._last_damage.get(episode, 0)
        current_total = _as_int(info.get("total_player_damage", previous_total))
        damage_delta = max(0, current_total - previous_total)
        if damage_delta > 0:
            self._episode_event_counts[episode] += 1
            self.events.append(
                self._build_event(
                    episode=episode,
                    event_index=self._episode_event_counts[episode],
                    damage_delta=damage_delta,
                    snapshot=snapshot,
                    pre_window=list(window),
                    info=info,
                    terminated=terminated,
                    truncated=truncated,
                )
            )
        self._last_damage[episode] = current_total
        window.append(snapshot)

    def _build_event(
        self,
        *,
        episode: int,
        event_index: int,
        damage_delta: int,
        snapshot: dict[str, Any],
        pre_window: list[dict[str, Any]],
        info: dict[str, Any],
        terminated: bool,
        truncated: bool,
    ) -> dict[str, Any]:
        frame = _as_int(snapshot["frame"])
        hero = snapshot["hero"]
        bullets = _nearest_bullets(info, limit=10)
        removed_ids = set((info.get("enemy_event") or {}).get("removed_enemy_bullet_ids", []) or [])
        candidate = next((bullet for bullet in bullets if bullet["id"] in removed_ids), None)
        candidate_source = "removed_enemy_bullet_ids" if candidate is not None else "unknown"
        candidate_confidence = "high" if candidate is not None and len(removed_ids) == 1 else "ambiguous" if candidate is not None else "low"
        if candidate is None and pre_window:
            previous_nearest = (pre_window[-1].get("bullets") or {}).get("nearest_enemy_bullet")
            if previous_nearest:
                candidate = dict(previous_nearest)
                candidate_source = "nearest_pre_impact"
                candidate_confidence = "medium"
        candidate_in_observation = None
        last_boost = self._last_boost_frame.get(episode)
        last_grounded = self._last_grounded_frame.get(episode)
        hints = self._avoidability_hints(
            snapshot=snapshot,
            pre_window=pre_window,
            candidate_in_observation=candidate_in_observation,
            last_boost=last_boost,
            last_grounded=last_grounded,
        )
        tags = heuristic_tags(hints, snapshot)
        health_after = _as_int(hero.get("health"))
        return {
            "event_identity": {
                "episode": episode,
                "impact_frame": frame,
                "event_index_in_episode": event_index,
                "damage_delta": damage_delta,
                "health_before": health_after + damage_delta,
                "health_after": health_after,
                "termination_reason": info.get("termination_reason") if terminated or truncated else None,
            },
            "runtime_config": self.runtime_context,
            "hero_state_at_impact": {
                **hero,
                "frames_since_last_boost_activation": None if last_boost is None else frame - last_boost,
                "frames_since_last_landing": None if last_grounded is None else frame - last_grounded,
                "frames_since_last_grounded_state_change": None,
                "frames_since_last_damage": (info.get("defensive_diagnostics") or {}).get("frames_since_last_damage"),
                "exact_boost_cooldown_available": False,
                "approximate_boost_charge": hero.get("boost_cooldown_or_charge"),
                "approximate_boost_charge_confidence": "medium",
            },
            "input_motion": {
                **snapshot["input"],
                **snapshot["motion"],
            },
            "edge_terrain_hints": snapshot["edge_terrain"],
            "bullets": {
                "visible_enemy_bullet_count_at_impact": snapshot["bullets"]["visible_enemy_bullet_count"],
                "top_visible_enemy_bullets": bullets,
                "nearest_bullet_by_distance": bullets[0] if bullets else None,
                "candidate_bullet": candidate,
                "candidate_bullet_source": candidate_source,
                "candidate_bullet_confidence": candidate_confidence,
                "candidate_bullet_in_observation": candidate_in_observation,
                "candidate_bullet_in_observation_basis": "pre_impact_window",
                "candidate_bullet_observation_confidence": "medium" if candidate_in_observation is not None else "low",
                "max_visible_bullet_count_in_window": max(
                    [snapshot["bullets"]["visible_enemy_bullet_count"]]
                    + [(step.get("bullets") or {}).get("visible_enemy_bullet_count", 0) for step in pre_window]
                ),
            },
            "pre_impact_window": pre_window[-self.window :],
            "avoidability_hints": hints,
            "heuristic_tags": tags,
            "heuristic_tags_note": "Heuristic tags are diagnostic hints only, not ground truth.",
        }

    def _avoidability_hints(
        self,
        *,
        snapshot: dict[str, Any],
        pre_window: list[dict[str, Any]],
        candidate_in_observation: bool | None,
        last_boost: int | None,
        last_grounded: int | None,
    ) -> dict[str, Any]:
        recent = pre_window[-15:] + [snapshot]
        frame = _as_int(snapshot.get("frame"))
        boost_ready_recent = any((step.get("hero") or {}).get("boost_ready") for step in recent)
        boost_pressed_recent = any((step.get("input") or {}).get("boost") == 1 for step in recent)
        boost_pressed_not_ready = any(
            (step.get("input") or {}).get("boost") == 1 and not (step.get("hero") or {}).get("boost_ready")
            for step in recent
        )
        grounded_recent = any((step.get("hero") or {}).get("grounded") for step in recent)
        pressing_edge = False
        edge_confidence = "unavailable"
        if any((step.get("edge_terrain") or {}).get("edge_contact_this_frame_available") for step in recent):
            edge_confidence = "medium"
            pressing_edge = any(
                ((step.get("edge_terrain") or {}).get("at_left_edge_this_frame") and (step.get("input") or {}).get("horizontal") == 0)
                or ((step.get("edge_terrain") or {}).get("at_right_edge_this_frame") and (step.get("input") or {}).get("horizontal") == 2)
                for step in recent
            )
        bullet_count = _as_int((snapshot.get("bullets") or {}).get("visible_enemy_bullet_count"))
        return {
            "heuristic_only": True,
            "boost_ready_within_15_frames_before_impact": boost_ready_recent,
            "boost_pressed_when_not_ready_before_impact": boost_pressed_not_ready,
            "boost_available_but_not_pressed_near_impact": boost_ready_recent and not boost_pressed_recent,
            "grounded_with_jump_available_before_impact": grounded_recent,
            "jump_not_pressed_in_recent_window": not any((step.get("input") or {}).get("jump") == 1 for step in recent),
            "duck_available_before_impact": True,
            "duck_relevance_known": False,
            "duck_avoidability_heuristic_available": False,
            "horizontal_escape_room_left": None,
            "world_left_edge_available": False,
            "horizontal_escape_room_right": None,
            "world_right_edge_available": False,
            "pressing_into_edge_near_impact": bool(pressing_edge),
            "pressing_into_edge_confidence": edge_confidence,
            "low_visible_bullet_count_but_hit_anyway": bullet_count <= 2,
            "high_visible_bullet_count_at_impact": bullet_count >= 8,
            "candidate_bullet_in_observation": candidate_in_observation,
            "candidate_bullet_missing_from_observation": candidate_in_observation is False,
            "candidate_bullet_observation_confidence": "medium" if candidate_in_observation is not None else "low",
            "impact_while_boost_active_or_recent": (snapshot.get("hero") or {}).get("boost_active") or (last_boost is not None and frame - last_boost <= 15),
            "impact_shortly_after_landing": last_grounded is not None and frame - last_grounded <= 15,
            "impact_during_long_airborne_streak": not (snapshot.get("hero") or {}).get("grounded") and not grounded_recent,
        }

    def build_report(self, *, episodes: int) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "window": self.window,
            "runtime_config": self.runtime_context,
            "limitations": [
                "Heuristic tags are diagnostic hints, not counterfactual avoidability proof.",
                "Terrain blockage, current-frame edge contact, and canonical world-edge distances are null because current eval info does not expose them.",
                "Candidate bullet inference uses removed bullet ids and nearest pre-impact bullet fallback.",
            ],
            "availability": {
                "terrain_blockage_available": False,
                "world_left_edge_available": False,
                "world_right_edge_available": False,
                "edge_contact_this_frame_available": False,
                "exact_boost_cooldown_available": False,
                "exact_grounded_state_change_available": False,
                "candidate_bullet_identity_is_best_effort": True,
            },
            "aggregate": aggregate_forensics(self.events, episodes=episodes),
            "events": self.events,
        }


def heuristic_tags(hints: dict[str, Any], snapshot: dict[str, Any]) -> list[str]:
    tags = []
    if hints.get("high_visible_bullet_count_at_impact"):
        tags.append("high_bullet_density")
    if hints.get("boost_pressed_when_not_ready_before_impact") or snapshot.get("hero", {}).get("boost_active"):
        tags.append("boost_related_or_cooldown")
    if hints.get("boost_available_but_not_pressed_near_impact"):
        tags.append("possible_missed_boost")
    if hints.get("grounded_with_jump_available_before_impact") and hints.get("jump_not_pressed_in_recent_window"):
        tags.append("possible_missed_jump")
    if hints.get("pressing_into_edge_near_impact") and hints.get("pressing_into_edge_confidence") != "unavailable":
        tags.append("edge_or_blockage")
    if hints.get("low_visible_bullet_count_but_hit_anyway"):
        tags.append("low_density_reading_failure")
    if hints.get("candidate_bullet_missing_from_observation"):
        tags.append("observation_candidate_missing")
    return tags or ["unclear"]


def aggregate_forensics(events: list[dict[str, Any]], *, episodes: int) -> dict[str, Any]:
    tag_counts = Counter(tag for event in events for tag in event.get("heuristic_tags", []))
    state_counts = Counter()
    visible_counts = []
    nearest_distances = []
    nearest_times = []
    candidate_known = 0
    candidate_in_obs = 0
    per_episode = Counter(event["event_identity"]["episode"] for event in events)
    for event in events:
        hero = event.get("hero_state_at_impact", {})
        hints = event.get("avoidability_hints", {})
        bullets = event.get("bullets", {})
        if hero.get("grounded"):
            state_counts["grounded"] += 1
        if hero.get("airborne"):
            state_counts["airborne"] += 1
        if hero.get("ducking"):
            state_counts["ducking"] += 1
        if hints.get("impact_while_boost_active_or_recent"):
            state_counts["boost_active_or_recent"] += 1
        if hints.get("boost_available_but_not_pressed_near_impact"):
            state_counts["boost_ready_but_not_used"] += 1
        if hints.get("pressing_into_edge_near_impact"):
            state_counts["pressing_into_edge"] += 1
        if hints.get("pressing_into_edge_near_impact"):
            state_counts["near_edge"] += 1
        visible_counts.append(_as_float(bullets.get("visible_enemy_bullet_count_at_impact"), 0.0) or 0.0)
        nearest = bullets.get("nearest_bullet_by_distance")
        if nearest:
            nearest_distances.append(_as_float(nearest.get("distance"), 0.0) or 0.0)
            tti = _as_float(nearest.get("approx_time_to_closest"))
            if tti is not None:
                nearest_times.append(tti)
        if bullets.get("candidate_bullet_in_observation") is not None:
            candidate_known += 1
            if bullets.get("candidate_bullet_in_observation"):
                candidate_in_obs += 1
    damage_free = max(0, int(episodes) - len(per_episode))
    return {
        "total_damage_events": len(events),
        "damage_events_per_episode": {str(k): int(v) for k, v in sorted(per_episode.items())},
        "damage_free_episode_count": damage_free,
        "damage_free_episode_rate": damage_free / float(episodes) if episodes else 0.0,
        "damage_events_by_pressure_profile": dict(Counter(event.get("runtime_config", {}).get("pressure_profile", "unknown") for event in events)),
        "damage_events_by_hero_state": dict(state_counts),
        "average_visible_bullets_at_impact": mean(visible_counts) if visible_counts else None,
        "average_nearest_bullet_distance": mean(nearest_distances) if nearest_distances else None,
        "average_nearest_bullet_approx_time_to_impact": mean(nearest_times) if nearest_times else None,
        "candidate_bullet_in_observation_fraction": candidate_in_obs / float(candidate_known) if candidate_known else None,
        "impacts_within_15_frames_after_boost_activation": sum(1 for event in events if event.get("avoidability_hints", {}).get("impact_while_boost_active_or_recent")),
        "impacts_while_boost_not_ready": sum(1 for event in events if not event.get("hero_state_at_impact", {}).get("boost_ready")),
        "impacts_shortly_after_landing": sum(1 for event in events if event.get("avoidability_hints", {}).get("impact_shortly_after_landing")),
        "impacts_during_high_bullet_density": tag_counts.get("high_bullet_density", 0),
        "impacts_during_low_bullet_density": tag_counts.get("low_density_reading_failure", 0),
        "heuristic_tag_counts": dict(tag_counts),
        "heuristic_only": True,
    }


def write_forensics_report(json_path: Path, md_path: Path, report: dict[str, Any]) -> None:
    write_json_file(json_path, report, allow_overwrite=False)
    aggregate = report["aggregate"]
    lines = [
        "# Damage Forensics",
        "",
        "Heuristic tags are diagnostic hints only, not counterfactual avoidability proof.",
        "",
        f"- Total damage events: `{aggregate['total_damage_events']}`",
        f"- Damage-free episodes: `{aggregate['damage_free_episode_count']}` / rate `{aggregate['damage_free_episode_rate']:.3f}`",
        f"- Average visible bullets at impact: `{aggregate['average_visible_bullets_at_impact']}`",
        f"- Average nearest bullet distance: `{aggregate['average_nearest_bullet_distance']}`",
        "",
        "## Heuristic Tags",
        "",
    ]
    for tag, count in sorted(aggregate["heuristic_tag_counts"].items()):
        lines.append(f"- `{tag}`: `{count}`")
    lines.extend(["", "## Limitations", ""])
    availability = report.get("availability", {})
    for key, value in availability.items():
        lines.append(f"- `{key}`: `{value}`")
    for limitation in report.get("limitations", []):
        lines.append(f"- {limitation}")
    lines.append("- Terrain, blockage, current-frame edge contact, and world-bound diagnostics require a future simulator-diagnostics task.")
    lines.extend(["", "## Events", ""])
    for event in report["events"]:
        ident = event["event_identity"]
        tags = ", ".join(event.get("heuristic_tags", []))
        lines.append(
            f"- Episode `{ident['episode']}` frame `{ident['impact_frame']}` "
            f"damage `{ident['damage_delta']}` tags `{tags}`"
        )
    write_text_file(md_path, "\n".join(lines) + "\n", allow_overwrite=False)
