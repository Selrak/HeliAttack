from __future__ import annotations

import argparse
import os
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

from ha2_env import HeliAttack2Env
from ha2_replay import JsonlReplayWriter


def action_from_keys(keys, env: HeliAttack2Env) -> list[int]:
    left = keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_q]
    right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
    move = 1
    if left and not right:
        move = 0
    elif right and not left:
        move = 2

    jump = keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_z]
    duck = keys[pygame.K_DOWN] or keys[pygame.K_s]
    boost = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
    try:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        fire = pygame.mouse.get_pressed(num_buttons=3)[0]
    except pygame.error:
        mouse_x = env.window_size[0] // 2
        mouse_y = env.window_size[1] // 2
        fire = 0
    mouse_x = max(0, min(mouse_x, env.window_size[0] - 1))
    mouse_y = max(0, min(mouse_y, env.window_size[1] - 1))
    cam_x, cam_y = env.get_camera()
    aim_bin = env.aim_bin_for_world_target(mouse_x - cam_x, mouse_y - cam_y)
    return [move, int(jump), int(duck), int(boost), aim_bin, int(fire)]


def save_screenshot(surface: pygame.Surface, out_dir: Path, frame_index: int) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"frame_{frame_index:06d}.png"
    pygame.image.save(surface, str(path))
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Play/debug HA2 directly.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--slow-fps", type=int, default=8)
    parser.add_argument("--save-replay", type=Path)
    parser.add_argument("--record-gif", type=Path)
    parser.add_argument("--screenshot-dir", type=Path, default=Path("screenshots"))
    args = parser.parse_args()

    env = HeliAttack2Env(render_mode="human", auto_render=False)
    obs, _info = env.reset(seed=args.seed)
    writer = (
        JsonlReplayWriter(args.save_replay, env, args.seed, obs)
        if args.save_replay is not None
        else None
    )

    clock = pygame.time.Clock()
    paused = False
    debug_overlay = True
    collision_overlay = False
    slow_motion = False
    single_step = False
    frames = []
    screenshot_index = 1
    running = True

    print(
        "Controls: A/D or Q/D or Left/Right move, W/Z/Up jump, S/Down duck, Shift hyperjump, "
        "Left mouse aim/fire, P/Space pause, N step, R reset, F1 debug, F2 slow, Esc quit."
    )

    env.render(
        debug_overlay=debug_overlay,
        debug_collision=collision_overlay,
        debug_lines=[
            "initializing",
            "controls: mouse aim/fire F1 debug F2 slow F3 hitboxes P/Space pause N step R reset Esc quit",
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
                    elif event.key == pygame.K_F1:
                        debug_overlay = not debug_overlay
                    elif event.key == pygame.K_F2:
                        slow_motion = not slow_motion
                    elif event.key == pygame.K_F3:
                        collision_overlay = not collision_overlay
                    elif event.key == pygame.K_F12 and env.window is not None:
                        path = save_screenshot(env.window, args.screenshot_dir, screenshot_index)
                        screenshot_index += 1
                        print(f"Saved screenshot: {path}")
                    elif event.key == pygame.K_r:
                        obs, _info = env.reset(seed=args.seed)
                        if writer is not None:
                            print("Replay recording stopped because reset events are not in schema v1.")
                            writer.close()
                            writer = None

            action = action_from_keys(pygame.key.get_pressed(), env)
            should_step = not paused or single_step
            if should_step:
                obs, reward, terminated, truncated, info = env.step(action)
                if writer is not None:
                    writer.append_step(env, action, obs, reward, terminated, truncated, info)
                if terminated or truncated:
                    obs, _info = env.reset(seed=args.seed)
                single_step = False

            fps = args.slow_fps if slow_motion else args.fps
            extra = [
                f"fps={clock.get_fps():.1f} target={fps} paused={paused} slow={slow_motion}",
                "controls: mouse aim/fire F1 debug F2 slow F3 hitboxes F12 screenshot P/Space pause N step R reset Esc quit",
            ]
            env.render(
                debug_overlay=debug_overlay,
                debug_collision=collision_overlay,
                debug_lines=extra,
            )

            if args.record_gif is not None and env.window is not None:
                import numpy as np

                frame3d = pygame.surfarray.array3d(env.window)
                frames.append(np.transpose(frame3d, (1, 0, 2)))

            clock.tick(fps)
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
