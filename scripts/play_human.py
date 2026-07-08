from __future__ import annotations

import argparse
import os
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

from ha2_env import (
    CONTROL_MODE_FULL,
    CONTROL_MODE_MOVEMENT_NO_BOOST_SCRIPTED_ATTACK_DIRECT,
    CONTROL_MODE_MOVEMENT_SCRIPTED_ATTACK_DIRECT,
    HeliAttack2Env,
    make_controlled_env,
)
from ha2_gui import (
    GuiSound,
    GuiState,
    add_common_gui_args,
    advance_post_death_visuals,
    handle_common_event,
    terminal_reason,
)
from ha2_high_score import update_high_score
from ha2_replay import JsonlReplayWriter
from scripts.runtime_config import add_runtime_config_args, resolve_runtime_config, runtime_env_kwargs


def action_from_keys(keys, env) -> list[int]:
    base_env: HeliAttack2Env = env.unwrapped
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
    control_mode = getattr(env, "control_mode", CONTROL_MODE_FULL)
    if control_mode == CONTROL_MODE_MOVEMENT_NO_BOOST_SCRIPTED_ATTACK_DIRECT:
        return [move, int(jump), int(duck)]
    if control_mode == CONTROL_MODE_MOVEMENT_SCRIPTED_ATTACK_DIRECT:
        return [move, int(jump), int(duck), int(boost)]

    try:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        fire = pygame.mouse.get_pressed(num_buttons=3)[0]
    except pygame.error:
        mouse_x = base_env.window_size[0] // 2
        mouse_y = base_env.window_size[1] // 2
        fire = 0
    mouse_x = max(0, min(mouse_x, base_env.window_size[0] - 1))
    mouse_y = max(0, min(mouse_y, base_env.window_size[1] - 1))
    cam_x, cam_y = base_env.get_camera()
    aim_bin = base_env.aim_bin_for_world_target(mouse_x - cam_x, mouse_y - cam_y)
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
    parser.add_argument("--save-replay", type=Path)
    parser.add_argument("--record-gif", type=Path)
    parser.add_argument("--screenshot-dir", type=Path, default=Path("screenshots"))
    add_common_gui_args(parser)
    add_runtime_config_args(
        parser,
        training_profile_default="legacy",
        max_episode_steps_default=None,
        skip_intro_default=False,
    )
    args = parser.parse_args()
    runtime_config = resolve_runtime_config(args)

    env = make_controlled_env(
        render_mode="human",
        auto_render=False,
        **runtime_env_kwargs(runtime_config),
    )
    base_env: HeliAttack2Env = env.unwrapped
    obs, _info = env.reset(seed=args.seed)
    gui_state = GuiState()
    gui_sound = GuiSound(enabled=not args.no_sound, sound_debug=args.sound_debug)
    gui_sound.sync(base_env)
    writer = (
        JsonlReplayWriter(args.save_replay, env, args.seed, obs)
        if args.save_replay is not None
        else None
    )

    clock = pygame.time.Clock()
    frames = []
    screenshot_index = 1
    session_max_score = int(base_env.score)

    print(
        "Controls: A/D or Q/D or Left/Right move, W/Z/Up jump, S/Down duck, Shift hyperjump, "
        "Left mouse aim/fire, common GUI keys: Esc quit Enter/R restart F speed+ Shift+F speed- "
        "1 reset speed P/Space pause N step F1 debug F3 hitboxes."
    )
    print(f"Pressure profile: {runtime_config.pressure_profile}")

    base_env.render(
        debug_overlay=gui_state.debug_overlay,
        debug_collision=gui_state.collision_overlay,
        debug_lines=[
            "initializing",
            "controls: mouse aim/fire " + " ".join(gui_state.common_debug_lines()),
        ],
    )

    try:
        while gui_state.running:
            for event in pygame.event.get():
                command = handle_common_event(gui_state, event, pygame)
                if command.screenshot and base_env.window is not None:
                    path = save_screenshot(base_env.window, args.screenshot_dir, screenshot_index)
                    screenshot_index += 1
                    print(f"Saved screenshot: {path}")
                if command.restart:
                    session_max_score = max(session_max_score, int(base_env.score))
                    update_high_score(session_max_score)
                    gui_sound.stop_all()
                    obs, _info = env.reset(seed=args.seed)
                    gui_state.clear_terminal()
                    gui_sound.sync(base_env)
                    if writer is not None:
                        print("Replay recording stopped because reset events are not in schema v1.")
                        writer.close()
                        writer = None
            if not gui_state.running:
                break

            action = action_from_keys(pygame.key.get_pressed(), env)
            if gui_state.terminal_hold:
                if (not gui_state.paused or gui_state.single_step) and gui_state.is_player_death_hold:
                    advance_post_death_visuals(base_env, gui_state, force_one=gui_state.single_step)
                gui_state.consume_single_step()
            elif gui_state.should_advance_logic():
                obs, reward, terminated, truncated, info = env.step(action)
                gui_sound.sync(base_env, play_events=True)
                session_max_score = max(session_max_score, int(base_env.score))
                if writer is not None:
                    writer.append_step(env, action, obs, reward, terminated, truncated, info)
                reason = terminal_reason(terminated, truncated, info)
                if reason is not None:
                    update_high_score(session_max_score)
                    gui_state.enter_terminal(reason)
                    gui_sound.sync(base_env)
                    print(f"Terminal state ({reason}). Press R or Enter to restart, Esc to quit.")
                gui_state.consume_single_step()

            gui_sound.sync(base_env)
            extra = [
                f"fps={clock.get_fps():.1f} target={gui_state.target_fps(args.fps)}",
                f"pressure={runtime_config.pressure_profile}",
                "controls: mouse aim/fire F12 screenshot",
                *gui_state.common_debug_lines(),
                *gui_sound.debug_lines(),
            ]
            base_env.render(
                debug_overlay=gui_state.debug_overlay,
                debug_collision=gui_state.collision_overlay,
                debug_lines=extra,
            )

            if args.record_gif is not None and base_env.window is not None:
                import numpy as np

                frame3d = pygame.surfarray.array3d(base_env.window)
                frames.append(np.transpose(frame3d, (1, 0, 2)))

            clock.tick(gui_state.target_fps(args.fps))
    finally:
        gui_sound.stop_all()
        update_high_score(session_max_score)
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
