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


Action = list[int]

IDLE: Action = [1, 0, 0, 0]
LEFT: Action = [0, 0, 0, 0]
RIGHT: Action = [2, 0, 0, 0]
JUMP: Action = [1, 1, 0, 0]
DUCK: Action = [1, 0, 1, 0]
BOOST: Action = [1, 0, 0, 1]

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
) -> None:
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
        "selected_frames:",
    ]
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
    env = HeliAttack2Env(render_mode="rgb_array" if needs_render else None, auto_render=False)
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
                maybe_capture(int(state["tick"]))
                if terminated or truncated:
                    break
        final_state = snapshot(env)
        final_hash = env.state_hash()
    finally:
        env.close()

    replay_verified = verify_replay_file(replay_path) == steps_written
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
    parser.add_argument("--frames", type=int, help="Override scenario frame count.")
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
        )
        print(
            f"{result.scenario}: replay={result.replay_path} "
            f"summary={result.summary_path} verified={result.replay_verified}"
        )


if __name__ == "__main__":
    main()
