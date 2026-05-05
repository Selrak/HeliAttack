from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pygame

from ha2_env import HeliAttack2Env
from ha2_replay import JsonlReplayWriter
from scripts.evaluate_model import default_model_path


def _load_ppo():
    try:
        from stable_baselines3 import PPO
    except ModuleNotFoundError as exc:
        raise SystemExit("stable-baselines3 is not installed. Install requirements first.") from exc
    return PPO


def main() -> None:
    parser = argparse.ArgumentParser(description="Watch a trained HA2 model in GUI mode.")
    parser.add_argument("--model", type=Path, default=None)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--stochastic", action="store_true")
    parser.add_argument("--save-replay", type=Path)
    parser.add_argument("--record-gif", type=Path)
    parser.add_argument("--training-profile", choices=["legacy", "combat_v1"], default="combat_v1")
    parser.add_argument("--max-episode-steps", type=int, default=1800)
    args = parser.parse_args()

    PPO = _load_ppo()
    model_path = args.model or default_model_path()
    if not model_path.exists():
        raise SystemExit(f"Model not found: {model_path}")

    model = PPO.load(model_path)
    env = HeliAttack2Env(
        render_mode="human",
        auto_render=False,
        training_profile=args.training_profile,
        max_episode_steps=args.max_episode_steps,
    )
    obs, _info = env.reset(seed=args.seed)
    writer = (
        JsonlReplayWriter(args.save_replay, env, args.seed, obs)
        if args.save_replay is not None
        else None
    )
    clock = pygame.time.Clock()
    frames = []
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

            action, _state = model.predict(obs, deterministic=not args.stochastic)
            action_list = [int(v) for v in action]
            obs, reward, terminated, truncated, info = env.step(action_list)
            if writer is not None:
                writer.append_step(env, action_list, obs, reward, terminated, truncated, info)
            env.render(
                debug_overlay=True,
                debug_collision=False,
                debug_lines=[f"model={model_path.name}", "Esc quit"],
            )

            if args.record_gif is not None and env.window is not None:
                frame3d = pygame.surfarray.array3d(env.window)
                frames.append(np.transpose(frame3d, (1, 0, 2)))

            if terminated or truncated:
                obs, _info = env.reset(seed=args.seed)
            clock.tick(args.fps)
    finally:
        if writer is not None:
            writer.close()
        env.close()

    if args.record_gif is not None and frames:
        import imageio

        args.record_gif.parent.mkdir(parents=True, exist_ok=True)
        imageio.mimsave(args.record_gif, frames, fps=args.fps)
        print(f"Wrote {args.record_gif}")


if __name__ == "__main__":
    main()
