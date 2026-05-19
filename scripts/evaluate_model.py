from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import numpy as np

from ha2_env import (
    CONTROL_MODE_FULL,
    FULL_SIM_ACTION_NVEC,
    action_space_nvec,
    get_full_action,
    get_policy_action,
    make_controlled_env,
    policy_action_space_nvec,
    sim_action_space_nvec,
)
from ha2_replay import JsonlReplayWriter
from scripts.experiment_utils import (
    ExperimentLayout,
    resolve_model_path,
    resolve_experiment_layout_and_config,
    write_json_file,
)
from scripts.damage_forensics import DamageForensicsCollector, write_forensics_report
from scripts.runtime_config import (
    add_runtime_config_args,
    explicit_runtime_overrides,
    resolve_runtime_config,
    runtime_env_kwargs,
)


def _load_ppo():
    try:
        from stable_baselines3 import PPO
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "stable-baselines3 is not installed. Install requirements before evaluation."
        ) from exc
    return PPO


def default_model_path() -> Path:
    best = Path("models/best.zip")
    latest = Path("models/latest.zip")
    return best if best.exists() else latest


def aggregate_metric(stats: list[dict], key: str) -> dict[str, object]:
    values = [row.get(key) for row in stats]
    numeric_values = [float(value) for value in values if value is not None]
    if not numeric_values:
        return {"mean": None, "std": None, "min": None, "max": None, "sum": None, "values": values}
    return {
        "mean": float(np.mean(numeric_values)),
        "std": float(np.std(numeric_values)),
        "min": float(np.min(numeric_values)),
        "max": float(np.max(numeric_values)),
        "sum": float(np.sum(numeric_values)),
        "values": values,
    }


def aggregate_reward_breakdowns(stats: list[dict]) -> dict[str, dict[str, object]]:
    terms = sorted(
        {
            term
            for row in stats
            for term in row.get("reward_breakdown", {})
        }
    )
    return {
        term: aggregate_metric(
            [{"value": row.get("reward_breakdown", {}).get(term, 0.0)} for row in stats],
            "value",
        )
        for term in terms
    }


def ratio_or_none(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return float(numerator) / float(denominator)


def marginal_action_distributions(
    stats: list[dict],
    *,
    frequency_key: str,
    action_names: list[str],
) -> dict:
    total_actions = sum(row["length"] for row in stats)
    distributions: dict[str, dict[str, float]] = {}
    if total_actions <= 0:
        return distributions
    for action_idx, name in enumerate(action_names):
        distributions[name] = {}
        for row in stats:
            for action_tuple_str, count in row.get(frequency_key, row.get("action_frequencies", {})).items():
                parts = action_tuple_str.split("|")
                if action_idx >= len(parts):
                    continue
                val = parts[action_idx]
                distributions[name][val] = distributions[name].get(val, 0) + count
        for val in distributions[name]:
            distributions[name][val] = float(distributions[name][val]) / total_actions
    return distributions


def build_evaluation_report(
    *,
    layout: ExperimentLayout | None,
    model_path: Path,
    effective_model_choice: str,
    training_profile: str,
    max_episode_steps: int,
    episodes: int,
    stats: list[dict],
    replay_paths: list[str],
    experiment_config: dict | None = None,
) -> dict:
    termination_reason_counts = Counter(row["termination_reason"] for row in stats)

    total_actions = sum(row["length"] for row in stats)
    full_action_names = ["move", "jump", "duck", "boost", "aim", "fire"]
    control_mode = experiment_config.get("control_mode", CONTROL_MODE_FULL) if experiment_config else CONTROL_MODE_FULL
    if control_mode == "movement_no_boost_scripted_attack_direct":
        policy_action_names = ["move", "jump", "duck"]
    elif control_mode == "movement_scripted_attack_direct":
        policy_action_names = ["move", "jump", "duck", "boost"]
    else:
        policy_action_names = full_action_names
    full_action_distributions = marginal_action_distributions(
        stats,
        frequency_key="full_action_frequencies",
        action_names=full_action_names,
    )
    policy_action_distributions = marginal_action_distributions(
        stats,
        frequency_key="policy_action_frequencies",
        action_names=policy_action_names,
    )

    bullets_spawned_sum = sum(row["player_bullets_spawned"] for row in stats)
    visible_seen_sum = sum(row["visible_enemy_bullets_seen_unique"] for row in stats)
    visible_hits_sum = sum(row["visible_enemy_bullets_hit_player"] for row in stats)
    over_top10_frames_sum = sum(row["visible_enemy_bullets_over_top10_frames"] for row in stats)

    if experiment_config is None:
        experiment_config = {}

    report = {
        "experiment": str(layout.path) if layout is not None else None,
        "model": str(model_path),
        "model_choice": effective_model_choice,
        "training_profile": training_profile,
        "reward_profile": experiment_config.get("reward_profile", "combat_default"),
        "pressure_profile": experiment_config.get("pressure_profile", "normal"),
        "control_mode": control_mode,
        "policy_action_space_nvec": experiment_config.get("policy_action_space_nvec"),
        "sim_action_space_nvec": experiment_config.get("sim_action_space_nvec", FULL_SIM_ACTION_NVEC),
        "max_episode_steps": max_episode_steps,
        "episodes": episodes,
        "net_arch": experiment_config.get("net_arch"),
        "activation_fn": experiment_config.get("activation_fn"),
        "trainable_parameters": experiment_config.get("trainable_parameters"),
        "metrics": {
            "reward": aggregate_metric(stats, "reward"),
            "length": aggregate_metric(stats, "length"),
            "heli_kills": aggregate_metric(stats, "heli_kills"),
            "heli_hits": aggregate_metric(stats, "heli_hits"),
            "player_shot_attempts": aggregate_metric(stats, "player_shot_attempts"),
            "player_bullets_spawned": aggregate_metric(stats, "player_bullets_spawned"),
            "player_shots_spawn_blocked": aggregate_metric(stats, "player_shots_spawn_blocked"),
            "player_damage": aggregate_metric(stats, "total_player_damage"),
            "enemy_bullet_hits": aggregate_metric(stats, "enemy_bullet_hits"),
            "frames_grounded": aggregate_metric(stats, "frames_grounded"),
            "frames_airborne": aggregate_metric(stats, "frames_airborne"),
            "frames_boost_ready": aggregate_metric(stats, "frames_boost_ready"),
            "frames_boost_pressed": aggregate_metric(stats, "frames_boost_pressed"),
            "frames_boost_pressed_ready": aggregate_metric(stats, "frames_boost_pressed_ready"),
            "frames_boost_pressed_not_ready": aggregate_metric(stats, "frames_boost_pressed_not_ready"),
            "boost_activations": aggregate_metric(stats, "boost_activations"),
            "frames_jump_pressed": aggregate_metric(stats, "frames_jump_pressed"),
            "jump_presses_grounded": aggregate_metric(stats, "jump_presses_grounded"),
            "jump_presses_airborne": aggregate_metric(stats, "jump_presses_airborne"),
            "frames_pressing_left": aggregate_metric(stats, "frames_pressing_left"),
            "frames_pressing_right": aggregate_metric(stats, "frames_pressing_right"),
            "frames_pressing_neutral": aggregate_metric(stats, "frames_pressing_neutral"),
            "frames_actual_moving_left": aggregate_metric(stats, "frames_actual_moving_left"),
            "frames_actual_moving_right": aggregate_metric(stats, "frames_actual_moving_right"),
            "frames_actual_not_moving_horizontally": aggregate_metric(stats, "frames_actual_not_moving_horizontally"),
            "sum_abs_player_dx": aggregate_metric(stats, "sum_abs_player_dx"),
            "player_x_range": aggregate_metric(stats, "player_x_range"),
            "frames_at_left_edge": aggregate_metric(stats, "frames_at_left_edge"),
            "frames_at_right_edge": aggregate_metric(stats, "frames_at_right_edge"),
            "max_consecutive_frames_at_left_edge": aggregate_metric(stats, "max_consecutive_frames_at_left_edge"),
            "max_consecutive_frames_at_right_edge": aggregate_metric(stats, "max_consecutive_frames_at_right_edge"),
            "frames_pressing_left_at_left_edge": aggregate_metric(stats, "frames_pressing_left_at_left_edge"),
            "frames_pressing_right_at_right_edge": aggregate_metric(stats, "frames_pressing_right_at_right_edge"),
            "min_player_x": aggregate_metric(stats, "min_player_x"),
            "max_player_x": aggregate_metric(stats, "max_player_x"),
            "final_score": aggregate_metric(stats, "final_score"),
            "max_score": aggregate_metric(stats, "max_score"),
            "visible_enemy_bullets_seen_unique": aggregate_metric(stats, "visible_enemy_bullets_seen_unique"),
            "visible_enemy_bullets_hit_player": aggregate_metric(stats, "visible_enemy_bullets_hit_player"),
            "visible_enemy_bullets_removed_without_hit": aggregate_metric(stats, "visible_enemy_bullets_removed_without_hit"),
            "visible_enemy_bullets_max": aggregate_metric(stats, "visible_enemy_bullets_max"),
            "visible_enemy_bullets_mean": aggregate_metric(stats, "visible_enemy_bullets_mean"),
            "visible_enemy_bullets_p95": aggregate_metric(stats, "visible_enemy_bullets_p95"),
            "visible_enemy_bullets_over_top10_frames": aggregate_metric(stats, "visible_enemy_bullets_over_top10_frames"),
            "max_visible_enemy_bullets_over_top10_excess": aggregate_metric(stats, "max_visible_enemy_bullets_over_top10_excess"),
            "damage_events": aggregate_metric(stats, "damage_events"),
            "time_to_first_damage": aggregate_metric(stats, "time_to_first_damage"),
            "mean_frames_between_damage": aggregate_metric(stats, "mean_frames_between_damage"),
            "min_frames_between_damage": aggregate_metric(stats, "min_frames_between_damage"),
            "max_frames_between_damage": aggregate_metric(stats, "max_frames_between_damage"),
            "frames_since_last_damage": aggregate_metric(stats, "frames_since_last_damage"),
            "longest_damage_free_streak": aggregate_metric(stats, "longest_damage_free_streak"),
            "damage_free_episode": aggregate_metric(stats, "damage_free_episode"),
            "engine_enemy_bullets_spawned": aggregate_metric(stats, "engine_enemy_bullets_spawned"),
            "engine_enemy_bullets_active": aggregate_metric(stats, "engine_enemy_bullets_active"),
            "enemy_bullet_hits_not_visible": aggregate_metric(stats, "enemy_bullet_hits_not_visible"),
        },
        "rates": {
            "hit_rate": ratio_or_none(sum(row["heli_hits"] for row in stats), bullets_spawned_sum),
            "death_rate": sum(row["deaths"] for row in stats) / float(len(stats)) if stats else 0.0,
            "fall_rate": sum(row["falls"] for row in stats) / float(len(stats)) if stats else 0.0,
            "timeout_rate": sum(1 for row in stats if row["termination_reason"] == "time_limit") / float(len(stats)) if stats else 0.0,
            "input_motion_mismatch_rate": ratio_or_none(
                sum(row["frames_pressing_left"] + row["frames_pressing_right"] for row in stats)
                - sum(row["frames_actual_moving_left"] + row["frames_actual_moving_right"] for row in stats),
                total_actions
            ),
            "left_edge_camping_rate": ratio_or_none(sum(row["frames_at_left_edge"] for row in stats), total_actions),
            "right_edge_camping_rate": ratio_or_none(sum(row["frames_at_right_edge"] for row in stats), total_actions),
            "left_edge_blocked_press_rate": ratio_or_none(
                sum(row["frames_pressing_left_at_left_edge"] for row in stats),
                sum(row["frames_at_left_edge"] for row in stats)
            ),
            "right_edge_blocked_press_rate": ratio_or_none(
                sum(row["frames_pressing_right_at_right_edge"] for row in stats),
                sum(row["frames_at_right_edge"] for row in stats)
            ),
            "visible_enemy_bullet_hit_rate_against_player": ratio_or_none(visible_hits_sum, visible_seen_sum),
            "damage_free_episode_rate": sum(1 for row in stats if row["damage_free_episode"]) / float(len(stats)) if stats else 0.0,
            "visible_enemy_bullets_over_top10_frame_rate": ratio_or_none(over_top10_frames_sum, total_actions),
        },
        "termination_reason_counts": dict(termination_reason_counts),
        "reward_breakdown": aggregate_reward_breakdowns(stats),
        "policy_action_distributions": policy_action_distributions,
        "full_action_distributions": full_action_distributions,
        "marginal_action_distributions": full_action_distributions,
        "episodes_detail": stats,
        "replay_paths": replay_paths,
    }
    return report


def main(args_list: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Evaluate a trained HA2 model.")
    parser.add_argument("--model", type=Path, default=None)
    parser.add_argument("--experiment", type=Path, default=None)
    parser.add_argument("--model-choice", choices=["best", "latest", "path"], default="best")
    parser.add_argument("--episodes", type=int, default=5)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--save-replays", action="store_true")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--replay-dir", type=Path, default=None)
    parser.add_argument("--report-name", type=str, default=None)
    parser.add_argument("--replay-prefix", type=str, default=None)
    parser.add_argument("--damage-forensics", choices=["on", "off"], default="off")
    parser.add_argument("--damage-forensics-window", type=int, default=60)
    add_runtime_config_args(parser)
    args = parser.parse_args(args_list)

    PPO = _load_ppo()
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

    model = PPO.load(model_path)
    if args.out is not None:
        report_path = args.out
    elif layout is not None:
        report_path = layout.report_path(effective_model_choice, args.report_name)
    else:
        report_path = Path("reports") / (args.report_name or "eval.json")
    if report_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing report: {report_path}")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    stats = []
    replay_paths: list[str] = []
    planned_replay_paths: list[Path] = []
    runtime_policy_action_space_nvec = None
    runtime_sim_action_space_nvec = None
    if args.save_replays:
        if args.replay_dir is not None:
            replay_dir = Path(args.replay_dir)
        elif layout is not None:
            replay_dir = layout.replays_dir
        else:
            replay_dir = Path("replays")
        replay_dir.mkdir(parents=True, exist_ok=True)
        replay_prefix = args.replay_prefix
        if replay_prefix is None:
            replay_prefix = {
                "best": "best_eval",
                "latest": "latest_eval",
            }.get(effective_model_choice, "eval")
        for episode in range(args.episodes):
            replay_path = replay_dir / f"{replay_prefix}_ep{episode}.jsonl"
            if replay_path.exists():
                raise FileExistsError(f"Refusing to overwrite existing replay: {replay_path}")
            planned_replay_paths.append(replay_path)

    damage_forensics_enabled = args.damage_forensics == "on"
    forensics_collector = None
    if damage_forensics_enabled:
        forensics_collector = DamageForensicsCollector(
            window=args.damage_forensics_window,
            runtime_context={
                "training_profile": runtime_config.training_profile,
                "control_mode": runtime_config.control_mode,
                "reward_profile": runtime_config.reward_profile,
                "pressure_profile": runtime_config.pressure_profile,
                "model_choice": effective_model_choice,
                "experiment": str(layout.path) if layout is not None else None,
                "max_episode_steps": runtime_config.max_episode_steps,
            },
        )

    for episode in range(args.episodes):
        env = make_controlled_env(
            render_mode=None,
            **runtime_env_kwargs(runtime_config),
        )
        if runtime_policy_action_space_nvec is None:
            runtime_policy_action_space_nvec = policy_action_space_nvec(env)
            runtime_sim_action_space_nvec = sim_action_space_nvec(env)
        obs, _info = env.reset(seed=args.seed + episode)
        base_env = env.unwrapped
        writer = None
        if args.save_replays:
            replay_path = planned_replay_paths[episode]
            writer = JsonlReplayWriter(
                replay_path,
                env,
                args.seed + episode,
                obs,
            )
            replay_paths.append(str(replay_path))

        total_reward = 0.0
        reward_breakdown_total: dict[str, float] = {}
        final_reward_breakdown: dict[str, float] | None = None
        length = 0
        max_x = base_env._x
        actions = Counter()
        visible_enemy_bullet_counts: list[int] = []
        max_score = int(base_env.score)
        final_score = int(base_env.score)
        policy_actions = Counter()
        full_actions = Counter()
        terminated = truncated = False
        try:
            while not (terminated or truncated):
                action, _state = model.predict(obs, deterministic=True)
                action_list = [int(v) for v in action]
                obs, reward, terminated, truncated, info = env.step(action_list)
                policy_action = get_policy_action(env, action_list)
                full_action = get_full_action(env, action_list)
                if writer is not None:
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
                total_reward += float(reward)
                step_reward_breakdown = info.get("reward_breakdown")
                if step_reward_breakdown is not None:
                    final_reward_breakdown = {
                        str(key): float(value)
                        for key, value in step_reward_breakdown.items()
                    }
                    for key, value in final_reward_breakdown.items():
                        reward_breakdown_total[key] = reward_breakdown_total.get(key, 0.0) + value
                length += 1
                max_x = max(max_x, base_env._x)
                final_score = int(info.get("combat", {}).get("score", base_env.score))
                max_score = max(max_score, final_score)
                actions[tuple(full_action)] += 1
                policy_actions[tuple(policy_action)] += 1
                full_actions[tuple(full_action)] += 1
                visible_enemy_bullet_counts.append(int(info.get("visible_enemy_bullets_current", 0)))
                if forensics_collector is not None:
                    forensics_collector.record_step(
                        episode=episode,
                        policy_action=policy_action,
                        full_action=full_action,
                        info=info,
                        terminated=terminated,
                        truncated=truncated,
                    )
        finally:
            if writer is not None:
                writer.close()
            env.close()

        defensive = info.get("defensive_diagnostics", {})
        movement = info.get("movement_diagnostics", {})
        stats.append(
            {
                "episode": episode,
                "reward": total_reward,
                "reward_profile": runtime_config.reward_profile,
                "pressure_profile": runtime_config.pressure_profile,
                "reward_breakdown": reward_breakdown_total,
                "final_reward_breakdown": final_reward_breakdown,
                "length": length,
                "terminated": terminated,
                "truncated": truncated,
                "termination_reason": info.get(
                    "termination_reason",
                    "fall" if terminated else "time_limit" if truncated else "none",
                ),
                "falls": int(info.get("termination_reason") == "fall"),
                "deaths": int(info.get("termination_reason") == "player_death"),
                "max_x": max_x,
                "final_score": final_score,
                "max_score": max_score,
                "total_player_damage": info.get("total_player_damage", 0),
                "heli_kills": info.get("heli_kills", 0),
                "heli_hits": info.get("heli_hits", 0),
                "player_shot_attempts": info.get("player_shot_attempts", 0),
                "player_bullets_spawned": info.get("player_bullets_spawned", 0),
                "player_shots_spawn_blocked": info.get("player_shots_spawn_blocked", 0),
                "enemy_bullet_hits": info.get("enemy_bullet_hits", 0),
                "frames_grounded": movement.get("frames_grounded", info.get("frames_grounded", 0)),
                "frames_airborne": movement.get("frames_airborne", info.get("frames_airborne", 0)),
                "frames_boost_ready": movement.get("frames_boost_ready", info.get("frames_boost_ready", 0)),
                "frames_boost_pressed": movement.get("frames_boost_pressed", info.get("frames_boost_pressed", 0)),
                "frames_boost_pressed_ready": movement.get("frames_boost_pressed_ready", info.get("frames_boost_pressed_ready", 0)),
                "frames_boost_pressed_not_ready": movement.get("frames_boost_pressed_not_ready", info.get("frames_boost_pressed_not_ready", 0)),
                "boost_activations": movement.get("boost_activations", info.get("boost_activations", 0)),
                "frames_jump_pressed": movement.get("frames_jump_pressed", info.get("frames_jump_pressed", 0)),
                "jump_presses_grounded": movement.get("jump_presses_grounded", info.get("jump_presses_grounded", 0)),
                "jump_presses_airborne": movement.get("jump_presses_airborne", info.get("jump_presses_airborne", 0)),
                "frames_pressing_left": movement.get("frames_pressing_left", 0),
                "frames_pressing_right": movement.get("frames_pressing_right", 0),
                "frames_pressing_neutral": movement.get("frames_pressing_neutral", 0),
                "frames_actual_moving_left": movement.get("frames_actual_moving_left", 0),
                "frames_actual_moving_right": movement.get("frames_actual_moving_right", 0),
                "frames_actual_not_moving_horizontally": movement.get("frames_actual_not_moving_horizontally", 0),
                "sum_abs_player_dx": movement.get("sum_abs_player_dx", 0.0),
                "frames_at_left_edge": movement.get("frames_at_left_edge", 0),
                "frames_at_right_edge": movement.get("frames_at_right_edge", 0),
                "max_consecutive_frames_at_left_edge": movement.get("max_consecutive_frames_at_left_edge", 0),
                "max_consecutive_frames_at_right_edge": movement.get("max_consecutive_frames_at_right_edge", 0),
                "frames_pressing_left_at_left_edge": movement.get("frames_pressing_left_at_left_edge", 0),
                "frames_pressing_right_at_right_edge": movement.get("frames_pressing_right_at_right_edge", 0),
                "min_player_x": movement.get("min_player_x", info.get("min_player_x", 0.0)),
                "max_player_x": movement.get("max_player_x", info.get("max_player_x", 0.0)),
                "visible_enemy_bullets_current": defensive.get("visible_enemy_bullets_current", 0),
                "visible_enemy_bullets_max": defensive.get("visible_enemy_bullets_max", 0),
                "visible_enemy_bullets_mean": defensive.get("visible_enemy_bullets_mean", 0.0),
                "visible_enemy_bullets_p95": (
                    float(np.percentile(visible_enemy_bullet_counts, 95))
                    if visible_enemy_bullet_counts
                    else 0.0
                ),
                "visible_enemy_bullets_seen_unique": defensive.get("visible_enemy_bullets_seen_unique", 0),
                "visible_enemy_bullets_hit_player": defensive.get("visible_enemy_bullets_hit_player", 0),
                "visible_enemy_bullets_removed_without_hit": defensive.get("visible_enemy_bullets_removed_without_hit", 0),
                "visible_enemy_bullet_hit_rate_against_player": defensive.get("visible_enemy_bullet_hit_rate_against_player"),
                "visible_enemy_bullets_over_top10_frames": defensive.get("visible_enemy_bullets_over_top10_frames", 0),
                "visible_enemy_bullets_over_top10_fraction": defensive.get("visible_enemy_bullets_over_top10_fraction", 0.0),
                "max_visible_enemy_bullets_over_top10_excess": defensive.get("max_visible_enemy_bullets_over_top10_excess", 0),
                "engine_enemy_bullets_spawned": defensive.get("engine_enemy_bullets_spawned", 0),
                "engine_enemy_bullets_active": defensive.get("engine_enemy_bullets_active", 0),
                "enemy_bullet_hits_not_visible": defensive.get("enemy_bullet_hits_not_visible", 0),
                "damage_event_frames": defensive.get("damage_event_frames", []),
                "damage_events": defensive.get("damage_events", 0),
                "time_to_first_damage": defensive.get("time_to_first_damage"),
                "frames_between_damage_events": defensive.get("frames_between_damage_events", []),
                "mean_frames_between_damage": defensive.get("mean_frames_between_damage"),
                "min_frames_between_damage": defensive.get("min_frames_between_damage"),
                "max_frames_between_damage": defensive.get("max_frames_between_damage"),
                "frames_since_last_damage": defensive.get("frames_since_last_damage", length),
                "longest_damage_free_streak": defensive.get("longest_damage_free_streak", length),
                "damage_free_episode": defensive.get("damage_free_episode", True),
                "policy_action_frequencies": {"|".join(map(str, k)): v for k, v in policy_actions.items()},
                "full_action_frequencies": {"|".join(map(str, k)): v for k, v in full_actions.items()},
                "action_frequencies": {"|".join(map(str, k)): v for k, v in actions.items()},
            }
        )

    config = dict(config)
    config["training_profile"] = runtime_config.training_profile
    config["reward_profile"] = runtime_config.reward_profile
    config["pressure_profile"] = runtime_config.pressure_profile
    config["control_mode"] = runtime_config.control_mode
    config["max_episode_steps"] = runtime_config.max_episode_steps
    config.setdefault("policy_action_space_nvec", runtime_policy_action_space_nvec)
    config.setdefault("sim_action_space_nvec", runtime_sim_action_space_nvec or FULL_SIM_ACTION_NVEC)

    report = build_evaluation_report(
        layout=layout,
        model_path=model_path,
        effective_model_choice=effective_model_choice,
        training_profile=runtime_config.training_profile,
        max_episode_steps=runtime_config.max_episode_steps,
        episodes=args.episodes,
        stats=stats,
        replay_paths=replay_paths,
        experiment_config=config,
    )
    if forensics_collector is not None:
        stem = report_path.stem
        forensics_json_path = report_path.parent / f"damage_forensics_{stem}.json"
        forensics_md_path = report_path.parent / f"damage_forensics_{stem}.md"
        forensics_report = forensics_collector.build_report(episodes=args.episodes)
        write_forensics_report(forensics_json_path, forensics_md_path, forensics_report)
        report["damage_forensics"] = {
            "enabled": True,
            "window": int(args.damage_forensics_window),
            "json_path": str(forensics_json_path),
            "markdown_path": str(forensics_md_path),
            "aggregate": forensics_report["aggregate"],
        }
    else:
        report["damage_forensics"] = {"enabled": False}
    write_json_file(report_path, report)
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
