from __future__ import annotations

import json
from pathlib import Path

from scripts.damage_forensics import DamageForensicsCollector, write_forensics_report


def step_info(*, frame: int, damage: int, health: int = 100, grounded: bool = True, boost_ready: bool = True, bullets: list[dict] | None = None) -> dict:
    return {
        "tick": frame,
        "episode_step_count": frame,
        "player_health": health,
        "grounded": grounded,
        "jumping": not grounded,
        "ducking": False,
        "hyperjump_ready": boost_ready,
        "total_player_damage": damage,
        "last_player_damage_amount": 10 if damage else 0,
        "last_player_damage_tick": frame if damage else None,
        "visible_enemy_bullets_current": len(bullets or []),
        "enemy_bullets": bullets or [],
        "enemy_event": {"removed_enemy_bullet_ids": [1]} if damage else {"removed_enemy_bullet_ids": []},
        "state": {
            "x": 50.0 + frame,
            "y": 20.0,
            "xspeed": 1.0,
            "yspeed": 0.0,
            "health": health,
            "hjump": 0,
            "hyperjump": 150 if boost_ready else 20,
        },
        "movement_diagnostics": {
            "frames_at_left_edge": 0,
            "frames_at_right_edge": 0,
            "max_consecutive_frames_at_left_edge": 0,
            "max_consecutive_frames_at_right_edge": 0,
            "frames_pressing_left_at_left_edge": 0,
            "frames_pressing_right_at_right_edge": 0,
        },
        "defensive_diagnostics": {"frames_since_last_damage": 0 if damage else frame},
    }


def test_damage_forensics_no_damage_has_empty_events(tmp_path):
    collector = DamageForensicsCollector(window=3, runtime_context={"pressure_profile": "normal"})
    for frame in range(5):
        collector.record_step(
            episode=0,
            policy_action=[1, 0, 0, 0],
            full_action=[1, 0, 0, 0, 16, 1],
            info=step_info(frame=frame, damage=0),
            terminated=False,
            truncated=False,
        )
    report = collector.build_report(episodes=1)
    assert report["events"] == []
    assert report["aggregate"]["total_damage_events"] == 0
    assert report["aggregate"]["damage_free_episode_count"] == 1
    assert report["availability"]["terrain_blockage_available"] is False


def test_damage_forensics_records_multiple_damage_events_and_window_limit():
    collector = DamageForensicsCollector(window=2, runtime_context={"pressure_profile": "normal"})
    bullets = [{"id": 1, "x": 60.0, "y": 20.0, "xspeed": -2.0, "yspeed": 0.0}]
    damages = [0, 0, 10, 10, 20]
    for frame, damage in enumerate(damages):
        collector.record_step(
            episode=0,
            policy_action=[1, 0, 0, 0],
            full_action=[1, 0, 0, 0, 16, 1],
            info=step_info(frame=frame, damage=damage, health=100 - damage, bullets=bullets),
            terminated=False,
            truncated=False,
        )
    report = collector.build_report(episodes=1)
    assert len(report["events"]) == 2
    assert all(len(event["pre_impact_window"]) <= 2 for event in report["events"])
    first = report["events"][0]
    assert first["avoidability_hints"]["heuristic_only"] is True
    assert first["bullets"]["candidate_bullet_source"] == "removed_enemy_bullet_ids"
    assert first["bullets"]["candidate_bullet_confidence"] == "high"
    assert first["bullets"]["candidate_bullet_in_observation"] is None
    assert first["avoidability_hints"]["duck_available_before_impact"] is True
    assert first["avoidability_hints"]["duck_relevance_known"] is False
    assert first["avoidability_hints"]["duck_avoidability_heuristic_available"] is False
    assert "possible_missed_jump_or_duck" not in first["heuristic_tags"]
    assert first["edge_terrain_hints"]["terrain_blockage_available"] is False
    assert first["edge_terrain_hints"]["distance_to_world_left_edge"] is None
    assert first["edge_terrain_hints"]["world_left_edge_available"] is False
    assert first["edge_terrain_hints"]["hero_x"] is not None
    assert first["hero_state_at_impact"]["exact_boost_cooldown_available"] is False
    assert "edge_or_blockage" not in first["heuristic_tags"]


def test_damage_forensics_markdown_lists_limitations(tmp_path):
    collector = DamageForensicsCollector(window=1, runtime_context={"pressure_profile": "normal"})
    report = collector.build_report(episodes=1)
    json_path = tmp_path / "damage_forensics.json"
    md_path = tmp_path / "damage_forensics.md"
    write_forensics_report(json_path, md_path, report)
    assert json.loads(json_path.read_text(encoding="utf-8"))["availability"]["world_right_edge_available"] is False
    md = md_path.read_text(encoding="utf-8")
    assert "## Limitations" in md
    assert "future simulator-diagnostics task" in md
