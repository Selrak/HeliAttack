from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pygame

from ha2_env import HeliAttack2Env
from ha2_replay import JsonlReplayWriter, verify_replay_file
from scripts.runtime_config import parse_human_count


Action = list[int]

RIGHT_AIM = 0
HELI_AIM = 28
IDLE: Action = [1, 0, 0, 0, RIGHT_AIM, 0]
LEFT: Action = [0, 0, 0, 0, RIGHT_AIM, 0]
RIGHT: Action = [2, 0, 0, 0, RIGHT_AIM, 0]
JUMP: Action = [1, 1, 0, 0, RIGHT_AIM, 0]
DUCK: Action = [1, 0, 1, 0, RIGHT_AIM, 0]
BOOST: Action = [1, 0, 0, 1, RIGHT_AIM, 0]
FIRE_RIGHT: Action = [1, 0, 0, 0, RIGHT_AIM, 1]
AIM_HELI_IDLE: Action = [1, 0, 0, 0, HELI_AIM, 0]
FIRE_HELI: Action = [1, 0, 0, 0, HELI_AIM, 1]

DEFAULT_SELECTED_FRAMES = (0, 1, 2, 10, 30, 60, 70, 80, 119)


@dataclass(frozen=True)
class Scenario:
    name: str
    frame_count: int
    description: str
    actions: tuple[Action, ...]


@dataclass(frozen=True)
class TraceResult:
    scenario: str
    replay_path: Path
    summary_path: Path
    screenshot_paths: tuple[Path, ...]
    frame_count: int
    final_hash: str
    replay_verified: bool


def repeated(action: Action, count: int) -> list[Action]:
    return [list(action) for _ in range(count)]


def build_scenarios() -> dict[str, Scenario]:
    scenarios = {
        "idle_120": Scenario(
            name="idle_120",
            frame_count=120,
            description="No movement input for 120 frames.",
            actions=tuple(repeated(IDLE, 120)),
        ),
        "walk_right_120": Scenario(
            name="walk_right_120",
            frame_count=120,
            description="Hold right for 120 frames.",
            actions=tuple(repeated(RIGHT, 120)),
        ),
        "jump_hold": Scenario(
            name="jump_hold",
            frame_count=120,
            description="Wait for spawn fall to settle, then hold jump for 20 frames.",
            actions=tuple(repeated(IDLE, 60) + repeated(JUMP, 20) + repeated(IDLE, 40)),
        ),
        "double_jump": Scenario(
            name="double_jump",
            frame_count=120,
            description="Wait for spawn fall to settle, jump, release, then trigger second jump.",
            actions=tuple(
                repeated(IDLE, 60)
                + repeated(JUMP, 6)
                + repeated(IDLE, 6)
                + repeated(JUMP, 6)
                + repeated(IDLE, 42)
            ),
        ),
        "duck_stand": Scenario(
            name="duck_stand",
            frame_count=120,
            description="Wait for spawn fall to settle, duck for 30 frames, then stand idle.",
            actions=tuple(repeated(IDLE, 60) + repeated(DUCK, 30) + repeated(IDLE, 30)),
        ),
        "hyperjump": Scenario(
            name="hyperjump",
            frame_count=120,
            description="Wait for spawn fall to settle, then use charged hyperjump.",
            actions=tuple(repeated(IDLE, 60) + repeated(BOOST, 3) + repeated(IDLE, 57)),
        ),
        "fire_right_60": Scenario(
            name="fire_right_60",
            frame_count=120,
            description="Wait for spawn fall to settle, then aim right and hold MachineGun fire for 60 frames.",
            actions=tuple(repeated(IDLE, 60) + repeated(FIRE_RIGHT, 60)),
        ),
        "fire_at_heli_180": Scenario(
            name="fire_at_heli_180",
            frame_count=240,
            description="Aim at the default Heli during spawn settle, then fire for 180 frames.",
            actions=tuple(repeated(AIM_HELI_IDLE, 60) + repeated(FIRE_HELI, 180)),
        ),
        "heli_shoots_hero_240": Scenario(
            name="heli_shoots_hero_240",
            frame_count=240,
            description="Keep the hero exposed while the default Heli aims and fires enemy bullets.",
            actions=tuple(repeated(IDLE, 240)),
        ),
        "kill_heli_respawn_600": Scenario(
            name="kill_heli_respawn_600",
            frame_count=600,
            description="Fire at the default Heli long enough to kill it and observe a replacement spawn.",
            actions=tuple(repeated(AIM_HELI_IDLE, 60) + repeated(FIRE_HELI, 540)),
        ),
    }
    return scenarios


SCENARIOS = build_scenarios()


def clipped_actions(scenario: Scenario, frame_count: int | None) -> list[Action]:
    if frame_count is None:
        return [list(action) for action in scenario.actions]
    if frame_count < 0:
        raise ValueError("frame_count must be non-negative")
    actions = list(scenario.actions)
    if frame_count <= len(actions):
        return [list(action) for action in actions[:frame_count]]
    return [list(action) for action in actions] + repeated(IDLE, frame_count - len(actions))


def capture_png(env: HeliAttack2Env, path: Path) -> Path:
    frame = env.render(debug_overlay=True, debug_collision=True)
    if frame is None:
        raise RuntimeError("rgb_array render returned no frame")
    path.parent.mkdir(parents=True, exist_ok=True)
    surface = pygame.surfarray.make_surface(np.transpose(frame, (1, 0, 2)))
    pygame.image.save(surface, str(path))
    return path


def state_line(state: dict) -> str:
    return json.dumps(state, sort_keys=True, separators=(",", ":"))


def snapshot(env: HeliAttack2Env) -> dict:
    state = env.get_state()
    state["state_hash"] = env.state_hash()
    return state


def write_summary(
    path: Path,
    *,
    scenario: Scenario,
    frame_count: int,
    initial_state: dict,
    final_state: dict,
    min_x: float,
    max_x: float,
    min_y: float,
    max_y: float,
    selected_states: dict[int, dict],
    replay_verified: bool,
    bullet_trace: dict | None = None,
    enemy_damage_trace: dict | None = None,
    combat_trace: dict | None = None,
) -> None:
    gun = final_state.get("gun", {})
    combat = final_state.get("combat", {})
    enemy_damage_trace = enemy_damage_trace or {}
    combat_trace = combat_trace or {}
    lines = [
        f"scenario={scenario.name}",
        f"description={scenario.description}",
        f"frame_count={frame_count}",
        f"replay_verified={replay_verified}",
        f"initial_state={state_line(initial_state)}",
        f"final_state={state_line(final_state)}",
        f"min_x={min_x:.8f}",
        f"max_x={max_x:.8f}",
        f"min_y={min_y:.8f}",
        f"max_y={max_y:.8f}",
        f"player_shot_attempts={gun.get('player_shot_attempts', 0)}",
        f"player_bullets_spawned={gun.get('player_bullets_spawned', 0)}",
        f"total_bullets_spawned={gun.get('total_bullets_spawned', 0)}",
        f"active_bullets={len(final_state.get('bullets', []))}",
        f"initial_player_health={initial_state.get('health', 0)}",
        f"final_player_health={final_state.get('health', 0)}",
        f"player_health={final_state.get('health', 0)}",
        f"enemy_bullets_spawned={combat.get('total_enemy_bullets_spawned', 0)}",
        f"enemy_bullet_hits={combat.get('enemy_bullet_hits', 0)}",
        f"first_enemy_damage_frame={enemy_damage_trace.get('frame')}",
        f"first_enemy_damage_bullet_id={enemy_damage_trace.get('bullet_id')}",
        f"first_enemy_damage_amount={enemy_damage_trace.get('amount')}",
        f"active_enemy_bullets={len(final_state.get('enemy_bullets', []))}",
        f"score={combat.get('score', 0)}",
        f"hits={combat.get('hits', 0)}",
        f"helis_counter={combat.get('helis', 0)}",
        f"helis_killed={combat.get('rthelis', 0)}",
        f"total_enemies_spawned={combat.get('total_enemies_spawned', 0)}",
        f"spawned_enemy_ids={state_line(combat_trace.get('spawned_enemy_ids', []))}",
        f"killed_enemy_ids={state_line(combat_trace.get('killed_enemy_ids', []))}",
        f"first_heli_death_frame={combat_trace.get('first_heli_death_frame')}",
        f"replacement_heli_spawn_frame={combat_trace.get('replacement_heli_spawn_frame')}",
        f"active_enemies={len(final_state.get('enemies', []))}",
    ]
    if bullet_trace is not None:
        lines.extend(
            [
                f"first_bullet_id={bullet_trace.get('id')}",
                f"first_bullet_initial={state_line(bullet_trace.get('initial'))}",
                f"first_bullet_final={state_line(bullet_trace.get('final'))}",
                f"first_bullet_removed_frame={bullet_trace.get('removed_frame')}",
            ]
        )
    lines.append("selected_frames:")
    for frame in sorted(selected_states):
        lines.append(f"  frame_{frame:04d}={state_line(selected_states[frame])}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def record_scenario(
    scenario_name: str,
    out_dir: str | Path = Path("reports/parity_traces"),
    *,
    seed: int = 0,
    frame_count: int | None = None,
    selected_frames: Iterable[int] = DEFAULT_SELECTED_FRAMES,
    write_screenshots: bool = True,
    write_gif: bool = False,
    skip_intro: bool = False,
) -> TraceResult:
    scenario = SCENARIOS[scenario_name]
    actions = clipped_actions(scenario, frame_count)
    selected = {int(frame) for frame in selected_frames if int(frame) >= 0}
    selected.add(len(actions))

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    replay_path = out_path / f"{scenario.name}.jsonl"
    summary_path = out_path / f"{scenario.name}_summary.txt"
    screenshot_dir = out_path / "screenshots"
    gif_path = out_path / f"{scenario.name}.gif"

    needs_render = write_screenshots or write_gif
    env = HeliAttack2Env(
        render_mode="rgb_array" if needs_render else None,
        auto_render=False,
        skip_intro=skip_intro,
    )
    obs, _info = env.reset(seed=seed)
    initial_state = snapshot(env)
    selected_states: dict[int, dict] = {0: initial_state}
    screenshot_paths: list[Path] = []
    gif_frames: list[np.ndarray] = []

    def maybe_capture(frame_index: int) -> None:
        if frame_index not in selected:
            return
        selected_states[frame_index] = snapshot(env)
        if write_screenshots:
            screenshot_paths.append(
                capture_png(
                    env,
                    screenshot_dir / f"{scenario.name}_frame_{frame_index:04d}.png",
                )
            )
        if write_gif:
            frame = env.render(debug_overlay=True, debug_collision=True)
            if frame is not None:
                gif_frames.append(frame)

    xs = [float(initial_state["x"])]
    ys = [float(initial_state["y"])]
    steps_written = 0
    first_bullet_id = None
    first_bullet_initial = None
    first_bullet_final = None
    first_bullet_removed_frame = None
    first_enemy_damage_trace = None
    spawned_enemy_ids: list[int] = []
    killed_enemy_ids: list[int] = []
    first_heli_death_frame = None
    replacement_heli_spawn_frame = None

    try:
        maybe_capture(0)
        with JsonlReplayWriter(replay_path, env, seed, obs) as writer:
            for action in actions:
                obs, reward, terminated, truncated, info = env.step(action)
                writer.append_step(env, action, obs, reward, terminated, truncated, info)
                steps_written += 1
                state = snapshot(env)
                xs.append(float(state["x"]))
                ys.append(float(state["y"]))
                enemy_event = info.get("enemy_event", {})
                step_spawned_enemy_ids = [
                    int(enemy_id) for enemy_id in enemy_event.get("spawned_enemy_ids", [])
                ]
                step_killed_enemy_ids = [
                    int(enemy_id) for enemy_id in enemy_event.get("killed_enemy_ids", [])
                ]
                spawned_enemy_ids.extend(step_spawned_enemy_ids)
                killed_enemy_ids.extend(step_killed_enemy_ids)
                if first_heli_death_frame is None and step_killed_enemy_ids:
                    first_heli_death_frame = int(state["tick"])
                if (
                    first_heli_death_frame is not None
                    and replacement_heli_spawn_frame is None
                    and step_spawned_enemy_ids
                ):
                    replacement_heli_spawn_frame = int(state["tick"])
                if (
                    first_enemy_damage_trace is None
                    and int(enemy_event.get("player_damage", 0)) > 0
                ):
                    removed = enemy_event.get("removed_enemy_bullet_ids", [])
                    first_enemy_damage_trace = {
                        "frame": int(state["tick"]),
                        "bullet_id": int(removed[0]) if removed else None,
                        "amount": int(enemy_event["player_damage"]),
                    }
                current_bullets = state.get("bullets", [])
                if first_bullet_id is None and current_bullets:
                    first_bullet_id = current_bullets[0]["id"]
                    first_bullet_initial = dict(current_bullets[0])
                if first_bullet_id is not None:
                    first_match = next(
                        (bullet for bullet in current_bullets if bullet["id"] == first_bullet_id),
                        None,
                    )
                    if first_match is not None:
                        first_bullet_final = dict(first_match)
                    elif first_bullet_removed_frame is None:
                        first_bullet_removed_frame = int(state["tick"])
                maybe_capture(int(state["tick"]))
                if terminated or truncated:
                    break
        final_state = snapshot(env)
        final_hash = env.state_hash()
    finally:
        env.close()

    replay_verified = verify_replay_file(replay_path) == steps_written
    bullet_trace = None
    if first_bullet_id is not None:
        bullet_trace = {
            "id": first_bullet_id,
            "initial": first_bullet_initial,
            "final": first_bullet_final,
            "removed_frame": first_bullet_removed_frame,
        }
    combat_trace = {
        "spawned_enemy_ids": spawned_enemy_ids,
        "killed_enemy_ids": killed_enemy_ids,
        "first_heli_death_frame": first_heli_death_frame,
        "replacement_heli_spawn_frame": replacement_heli_spawn_frame,
    }
    write_summary(
        summary_path,
        scenario=scenario,
        frame_count=steps_written,
        initial_state=initial_state,
        final_state=final_state,
        min_x=min(xs),
        max_x=max(xs),
        min_y=min(ys),
        max_y=max(ys),
        selected_states=selected_states,
        replay_verified=replay_verified,
        bullet_trace=bullet_trace,
        enemy_damage_trace=first_enemy_damage_trace,
        combat_trace=combat_trace,
    )

    if write_gif and gif_frames:
        import imageio

        imageio.mimsave(gif_path, gif_frames, fps=30)

    return TraceResult(
        scenario=scenario.name,
        replay_path=replay_path,
        summary_path=summary_path,
        screenshot_paths=tuple(screenshot_paths),
        frame_count=steps_written,
        final_hash=final_hash,
        replay_verified=replay_verified,
    )


def scenario_names(value: str) -> list[str]:
    if value == "all":
        return list(SCENARIOS)
    if value not in SCENARIOS:
        raise argparse.ArgumentTypeError(
            f"unknown scenario {value!r}; choose one of: all, {', '.join(SCENARIOS)}"
        )
    return [value]


def main() -> None:
    parser = argparse.ArgumentParser(description="Record deterministic HA2 scripted player traces.")
    parser.add_argument("--scenario", type=scenario_names, default=list(SCENARIOS))
    parser.add_argument("--out-dir", type=Path, default=Path("reports/parity_traces"))
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--frames", type=parse_human_count, help="Override scenario frame count.")
    parser.add_argument("--skip-intro", dest="skip_intro", action="store_true", default=False)
    parser.add_argument("--no-skip-intro", dest="skip_intro", action="store_false")
    parser.add_argument("--no-screenshots", action="store_true")
    parser.add_argument("--gif", action="store_true", help="Also write selected-frame GIFs.")
    args = parser.parse_args()

    for name in args.scenario:
        result = record_scenario(
            name,
            args.out_dir,
            seed=args.seed,
            frame_count=args.frames,
            write_screenshots=not args.no_screenshots,
            write_gif=args.gif,
            skip_intro=args.skip_intro,
        )
        print(
            f"{result.scenario}: replay={result.replay_path} "
            f"summary={result.summary_path} verified={result.replay_verified}"
        )


if __name__ == "__main__":
    main()
