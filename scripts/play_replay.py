from __future__ import annotations

import argparse
import os
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

from ha2_gui import (
    GuiSound,
    GuiState,
    add_common_gui_args,
    advance_post_death_visuals,
    handle_common_event,
    terminal_reason,
)
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
    parser.add_argument("--replay-env", choices=REPLAY_ENV_CHOICES, default="recorded")
    add_common_gui_args(parser)
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
    gui_state = GuiState(paused=args.start_paused)
    gui_sound = GuiSound(enabled=not args.no_sound, sound_debug=args.sound_debug)
    gui_sound.sync(env)
    clock = pygame.time.Clock()
    index = 0

    env.render(
        debug_overlay=gui_state.debug_overlay,
        debug_collision=gui_state.collision_overlay,
        debug_lines=[
            f"replay={args.replay.name} step=0/{len(steps)}",
            f"sim={replay_config.simulator_id} collision={replay_config.simulation_semantics['collision_model']}",
            f"intro={replay_config.simulation_semantics.get('intro_mode', 'legacy')}",
            f"pressure={header.get('pressure_profile', 'normal')}",
            *gui_state.common_debug_lines(),
        ],
    )

    try:
        while gui_state.running:
            for event in pygame.event.get():
                command = handle_common_event(gui_state, event, pygame)
                if command.restart and gui_state.terminal_hold:
                    gui_sound.stop_all()
                    env.reset(seed=int(header["seed"]))
                    gui_state.clear_terminal()
                    gui_state.paused = args.start_paused
                    index = 0
                    gui_sound.sync(env)
            if not gui_state.running:
                break

            if gui_state.terminal_hold:
                if (not gui_state.paused or gui_state.single_step) and gui_state.is_player_death_hold:
                    advance_post_death_visuals(env, gui_state, force_one=gui_state.single_step)
                gui_state.consume_single_step()
            elif index < len(steps) and gui_state.should_advance_logic():
                step = steps[index]
                _obs, _reward, terminated, truncated, info = env.step(step["action"])
                gui_sound.sync(env, play_events=True)
                index += 1
                reason = terminal_reason(terminated, truncated, info)
                if reason is not None:
                    gui_state.enter_terminal(reason)
                    gui_sound.sync(env)
                elif index >= len(steps):
                    gui_state.enter_terminal("replay_end")
                    gui_sound.sync(env)
                gui_state.consume_single_step()
            elif index >= len(steps) and not gui_state.terminal_hold:
                gui_state.enter_terminal("replay_end")

            extra = [
                f"replay={args.replay.name} step={index}/{len(steps)}",
                f"sim={replay_config.simulator_id} collision={replay_config.simulation_semantics['collision_model']}",
                f"intro={replay_config.simulation_semantics.get('intro_mode', 'legacy')}",
                f"pressure={header.get('pressure_profile', 'normal')}",
                f"fps={clock.get_fps():.1f} target={gui_state.target_fps(args.fps)}",
                *gui_state.common_debug_lines(),
                *gui_sound.debug_lines(),
            ]
            env.render(
                debug_overlay=gui_state.debug_overlay,
                debug_collision=gui_state.collision_overlay,
                debug_lines=extra,
            )
            gui_sound.sync(env)
            clock.tick(gui_state.target_fps(args.fps))
    finally:
        gui_sound.stop_all()
        env.close()


if __name__ == "__main__":
    main()
