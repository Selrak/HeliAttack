from __future__ import annotations

import argparse
import os
from pathlib import Path

from scripts.experiment_utils import (
    ExperimentLayout,
    resolve_model_path,
    resolve_experiment_layout_and_config,
    unique_timestamped_path,
)
from scripts.runtime_config import (
    add_runtime_config_args,
    explicit_runtime_overrides,
    resolve_runtime_config,
    runtime_env_kwargs,
)
from ha2_gui import (
    GuiSound,
    GuiState,
    add_common_gui_args,
    advance_post_death_visuals,
    handle_common_event,
    terminal_reason,
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
    parser.add_argument("--stochastic", action="store_true")
    parser.add_argument("--save-replay", nargs="?", const=DEFAULT_OUTPUT, default=None, type=str)
    parser.add_argument("--record-gif", nargs="?", const=DEFAULT_OUTPUT, default=None, type=str)
    add_common_gui_args(parser)
    add_runtime_config_args(parser)
    args = parser.parse_args(args_list)

    effective_model_choice = "path" if args.model is not None else args.model_choice
    layout, config = resolve_experiment_layout_and_config(
        experiment=args.experiment,
        model=args.model,
    )
    runtime_config = resolve_runtime_config(args, config)
    for field, (config_value, cli_value) in explicit_runtime_overrides(args, config, runtime_config).items():
        print(f"Runtime override: {field} {config_value!r} -> {cli_value!r}")
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

    from ha2_env import get_full_action, get_policy_action, make_controlled_env
    from ha2_high_score import update_high_score
    from ha2_replay import JsonlReplayWriter

    env = make_controlled_env(
        render_mode="human",
        auto_render=False,
        **runtime_env_kwargs(runtime_config),
    )
    base_env = env.unwrapped
    obs, _info = env.reset(seed=args.seed)
    gui_state = GuiState()
    gui_sound = GuiSound(enabled=not args.no_sound, sound_debug=args.sound_debug)
    gui_sound.sync(base_env)
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
    episode_max_score = int(base_env.score)
    session_max_score = int(base_env.score)

    base_env.render(
        debug_overlay=gui_state.debug_overlay,
        debug_collision=gui_state.collision_overlay,
        debug_lines=[
            f"model={model_path.name}",
            f"pressure={runtime_config.pressure_profile}",
            "initializing",
            *gui_state.common_debug_lines(),
        ],
    )

    try:
        while gui_state.running:
            for event in pygame.event.get():
                command = handle_common_event(gui_state, event, pygame)
                if command.restart and gui_state.terminal_hold:
                    gui_sound.stop_all()
                    obs, _info = env.reset(seed=args.seed)
                    gui_state.clear_terminal()
                    episode_max_score = int(base_env.score)
                    gui_sound.sync(base_env)
            if not gui_state.running:
                break

            if gui_state.terminal_hold:
                if (not gui_state.paused or gui_state.single_step) and gui_state.is_player_death_hold:
                    advance_post_death_visuals(base_env, gui_state, force_one=gui_state.single_step)
                gui_state.consume_single_step()
            elif gui_state.should_advance_logic():
                action, _state = model.predict(obs, deterministic=not args.stochastic)
                action_list = [int(v) for v in action]
                obs, reward, terminated, truncated, info = env.step(action_list)
                gui_sound.sync(base_env, play_events=True)
                episode_max_score = max(episode_max_score, int(base_env.score))
                session_max_score = max(session_max_score, episode_max_score)
                if writer is not None:
                    policy_action = get_policy_action(env, action_list)
                    full_action = get_full_action(env, action_list)
                    writer.append_step(
                        env,
                        full_action,
                        obs,
                        reward,
                        terminated,
                        truncated,
                        info,
                        policy_action=policy_action,
                        full_action=full_action,
                        control_mode=runtime_config.control_mode,
                    )
                reason = terminal_reason(terminated, truncated, info)
                if reason is not None:
                    update_high_score(episode_max_score)
                    gui_state.enter_terminal(reason)
                    gui_sound.sync(base_env)
                gui_state.consume_single_step()
            gui_sound.sync(base_env)
            base_env.render(
                debug_overlay=gui_state.debug_overlay,
                debug_collision=gui_state.collision_overlay,
                debug_lines=[
                    f"model={model_path.name}",
                    f"pressure={runtime_config.pressure_profile}",
                    f"fps={clock.get_fps():.1f} target={gui_state.target_fps(args.fps)}",
                    *gui_state.common_debug_lines(),
                    *gui_sound.debug_lines(),
                ],
            )

            if gif_path is not None and base_env.window is not None:
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

    if gif_path is not None and frames:
        import imageio

        gif_path.parent.mkdir(parents=True, exist_ok=True)
        imageio.mimsave(gif_path, frames, fps=args.fps)
        print(f"Wrote {gif_path}")


if __name__ == "__main__":
    main()
