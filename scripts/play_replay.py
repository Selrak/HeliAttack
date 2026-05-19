from __future__ import annotations

import argparse
import os
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

from ha2_replay import (
    REPLAY_ENV_CHOICES,
    load_replay,
    make_replay_env,
    replay_env_override_warning,
    resolve_replay_simulator_config,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Watch a deterministic HA2 replay in GUI mode.")
    parser.add_argument("replay", type=Path)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--start-paused", action="store_true")
    parser.add_argument("--fast-fps-multiplier", type=int, default=4)
    parser.add_argument("--replay-env", choices=REPLAY_ENV_CHOICES, default="recorded")
    args = parser.parse_args()

    header, steps = load_replay(args.replay)
    replay_config = resolve_replay_simulator_config(header, replay_env=args.replay_env)
    warning = replay_env_override_warning(replay_config)
    if warning:
        print(f"WARNING: {warning}")
    env = make_replay_env(
        header,
        render_mode="human",
        auto_render=False,
        replay_env=args.replay_env,
    )
    env.reset(seed=int(header["seed"]))
    clock = pygame.time.Clock()
    paused = args.start_paused
    fast_forward = False
    single_step = False
    debug_overlay = True
    index = 0
    running = True

    env.render(
        debug_overlay=debug_overlay,
        debug_collision=False,
        debug_lines=[
            f"replay={args.replay.name} step=0/{len(steps)} paused={paused}",
            f"sim={replay_config.simulator_id} collision={replay_config.simulation_semantics['collision_model']}",
            f"intro={replay_config.simulation_semantics.get('intro_mode', 'legacy')}",
            f"pressure={header.get('pressure_profile', 'normal')}",
        ],
    )

    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key in (pygame.K_p, pygame.K_SPACE):
                        paused = not paused
                    elif event.key == pygame.K_n:
                        single_step = True
                    elif event.key == pygame.K_f:
                        fast_forward = not fast_forward
                    elif event.key == pygame.K_F1:
                        debug_overlay = not debug_overlay

            if index < len(steps) and (not paused or single_step):
                step = steps[index]
                _obs, _reward, terminated, truncated, _info = env.step(step["action"])
                index += 1
                single_step = False
                if terminated or truncated:
                    paused = True

            extra = [
                f"replay={args.replay.name} step={index}/{len(steps)} paused={paused} fast={fast_forward}",
                f"sim={replay_config.simulator_id} collision={replay_config.simulation_semantics['collision_model']}",
                f"intro={replay_config.simulation_semantics.get('intro_mode', 'legacy')}",
                f"pressure={header.get('pressure_profile', 'normal')}",
                "controls: F1 debug F fast-forward P/Space pause N step Esc quit",
            ]
            env.render(debug_overlay=debug_overlay, debug_collision=False, debug_lines=extra)
            target_fps = args.fps * args.fast_fps_multiplier if fast_forward else args.fps
            clock.tick(target_fps)
    finally:
        env.close()


if __name__ == "__main__":
    main()
