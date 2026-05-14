from __future__ import annotations

import argparse
import os
from pathlib import Path

from scripts.experiment_utils import (
    ExperimentLayout,
    resolve_model_path,
    unique_timestamped_path,
)


def default_model_path() -> Path:
    best = Path("models/best.zip")
    latest = Path("models/latest.zip")
    return best if best.exists() else latest


def _load_ppo():
    try:
        from stable_baselines3 import PPO
    except ModuleNotFoundError as exc:
        raise SystemExit("stable-baselines3 is not installed. Install requirements first.") from exc
    return PPO


DEFAULT_OUTPUT = "__default__"


def main(args_list: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Watch a trained HA2 model in GUI mode.")
    parser.add_argument("--model", type=Path, default=None)
    parser.add_argument("--experiment", type=Path, default=None)
    parser.add_argument("--model-choice", choices=["best", "latest", "path"], default="best")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--fast-fps-multiplier", type=int, default=4)
    parser.add_argument("--stochastic", action="store_true")
    parser.add_argument("--save-replay", nargs="?", const=DEFAULT_OUTPUT, default=None, type=str)
    parser.add_argument("--record-gif", nargs="?", const=DEFAULT_OUTPUT, default=None, type=str)
    parser.add_argument("--training-profile", choices=["legacy", "combat_v1"], default="combat_v1")
    parser.add_argument("--max-episode-steps", type=int, default=1800)
    args = parser.parse_args(args_list)

    effective_model_choice = "path" if args.model is not None else args.model_choice
    layout = None
    if args.experiment is not None:
        experiment_path = Path(args.experiment)
        if not experiment_path.exists():
            raise SystemExit(f"Experiment not found: {experiment_path}")
        layout = ExperimentLayout(experiment_path.parent, experiment_path)
    model_path = resolve_model_path(
        model=args.model,
        experiment=None if layout is None else layout.path,
        model_choice=args.model_choice,
    )
    if args.model is None and layout is None:
        model_path = default_model_path()
    if not model_path.exists():
        raise SystemExit(f"Model not found: {model_path}")

    PPO = _load_ppo()
    model = PPO.load(model_path)
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import pygame

    from ha2_env import HeliAttack2Env
    from ha2_replay import JsonlReplayWriter

    env = HeliAttack2Env(
        render_mode="human",
        auto_render=False,
        training_profile=args.training_profile,
        max_episode_steps=args.max_episode_steps,
    )
    obs, _info = env.reset(seed=args.seed)
    writer = None
    replay_path = None
    if args.save_replay is not None:
        if args.save_replay == DEFAULT_OUTPUT:
            replay_path = (
                unique_timestamped_path(layout.replays_dir, f"watch_{effective_model_choice}", ".jsonl")
                if layout is not None
                else unique_timestamped_path(Path("replays"), f"watch_{effective_model_choice}", ".jsonl")
            )
        else:
            replay_path = Path(args.save_replay)
            if replay_path.exists():
                raise FileExistsError(f"Refusing to overwrite existing replay: {replay_path}")
        writer = JsonlReplayWriter(replay_path, env, args.seed, obs)
        print(f"Saving replay to {replay_path}")
    gif_path = None
    if args.record_gif is not None:
        if args.record_gif == DEFAULT_OUTPUT:
            gif_path = (
                unique_timestamped_path(layout.recordings_dir, f"watch_{effective_model_choice}", ".gif")
                if layout is not None
                else unique_timestamped_path(Path("recordings"), f"watch_{effective_model_choice}", ".gif")
            )
        else:
            gif_path = Path(args.record_gif)
            if gif_path.exists():
                raise FileExistsError(f"Refusing to overwrite existing GIF: {gif_path}")
    clock = pygame.time.Clock()
    frames = []
    fast_forward = False
    running = True

    env.render(
        debug_overlay=True,
        debug_collision=False,
        debug_lines=[f"model={model_path.name}", "initializing", "Esc quit"],
    )

    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_f:
                    fast_forward = not fast_forward

            action, _state = model.predict(obs, deterministic=not args.stochastic)
            action_list = [int(v) for v in action]
            obs, reward, terminated, truncated, info = env.step(action_list)
            if writer is not None:
                writer.append_step(env, action_list, obs, reward, terminated, truncated, info)
            env.render(
                debug_overlay=True,
                debug_collision=False,
                debug_lines=[
                    f"model={model_path.name}",
                    f"fast={fast_forward}",
                    "controls: F fast-forward Esc quit",
                ],
            )

            if gif_path is not None and env.window is not None:
                import numpy as np

                frame3d = pygame.surfarray.array3d(env.window)
                frames.append(np.transpose(frame3d, (1, 0, 2)))

            if terminated or truncated:
                obs, _info = env.reset(seed=args.seed)
            target_fps = args.fps * args.fast_fps_multiplier if fast_forward else args.fps
            clock.tick(target_fps)
    finally:
        if writer is not None:
            writer.close()
        env.close()

    if gif_path is not None and frames:
        import imageio

        gif_path.parent.mkdir(parents=True, exist_ok=True)
        imageio.mimsave(gif_path, frames, fps=args.fps)
        print(f"Wrote {gif_path}")


if __name__ == "__main__":
    main()
