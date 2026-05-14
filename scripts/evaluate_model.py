from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import numpy as np

from ha2_env import HeliAttack2Env
from ha2_replay import JsonlReplayWriter
from scripts.experiment_utils import (
    ExperimentLayout,
    resolve_model_path,
    write_json_file,
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


def ratio_or_none(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return float(numerator) / float(denominator)


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
) -> dict:
    termination_reason_counts = Counter(row["termination_reason"] for row in stats)

    total_actions = sum(row["length"] for row in stats)
    marginal_actions = {}
    if total_actions > 0:
        action_names = ["move", "jump", "duck", "boost", "aim", "fire"]
        for action_idx, name in enumerate(action_names):
            marginal_actions[name] = {}
            for row in stats:
                for action_tuple_str, count in row["action_frequencies"].items():
                    val = action_tuple_str.split("|")[action_idx]
                    marginal_actions[name][val] = marginal_actions[name].get(val, 0) + count
            for val in marginal_actions[name]:
                marginal_actions[name][val] = float(marginal_actions[name][val]) / total_actions

    bullets_spawned_sum = sum(row["player_bullets_spawned"] for row in stats)
    visible_seen_sum = sum(row["visible_enemy_bullets_seen_unique"] for row in stats)
    visible_hits_sum = sum(row["visible_enemy_bullets_hit_player"] for row in stats)
    over_top10_frames_sum = sum(row["visible_enemy_bullets_over_top10_frames"] for row in stats)

    return {
        "experiment": str(layout.path) if layout is not None else None,
        "model": str(model_path),
        "model_choice": effective_model_choice,
        "training_profile": training_profile,
        "max_episode_steps": max_episode_steps,
        "episodes": episodes,
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
            "visible_enemy_bullet_hit_rate_against_player": ratio_or_none(visible_hits_sum, visible_seen_sum),
            "damage_free_episode_rate": sum(1 for row in stats if row["damage_free_episode"]) / float(len(stats)) if stats else 0.0,
            "visible_enemy_bullets_over_top10_frame_rate": ratio_or_none(over_top10_frames_sum, total_actions),
        },
        "termination_reason_counts": dict(termination_reason_counts),
        "marginal_action_distributions": marginal_actions,
        "episodes_detail": stats,
        "replay_paths": replay_paths,
    }


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
    parser.add_argument("--training-profile", choices=["legacy", "combat_v1", "combat_bullets_v1"], default="combat_v1")
    parser.add_argument("--max-episode-steps", type=int, default=1800)
    args = parser.parse_args(args_list)

    PPO = _load_ppo()
    effective_model_choice = "path" if args.model is not None else args.model_choice
    layout = None
    if args.experiment is not None:
        experiment_path = Path(args.experiment)
        if not experiment_path.exists():
            raise SystemExit(f"Experiment not found: {experiment_path}")
        layout = ExperimentLayout(experiment_path.parent, experiment_path)
        if layout.config_path.exists():
            import json
            with open(layout.config_path, "r") as f:
                config = json.load(f)
                if "training_profile" in config:
                    args.training_profile = config["training_profile"]

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

    for episode in range(args.episodes):
        env = HeliAttack2Env(
            render_mode=None,
            training_profile=args.training_profile,
            max_episode_steps=args.max_episode_steps,
        )
        obs, _info = env.reset(seed=args.seed + episode)
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
        length = 0
        max_x = env._x
        actions = Counter()
        visible_enemy_bullet_counts: list[int] = []
        max_score = int(env.score)
        final_score = int(env.score)
        terminated = truncated = False
        try:
            while not (terminated or truncated):
                action, _state = model.predict(obs, deterministic=True)
                action_list = [int(v) for v in action]
                obs, reward, terminated, truncated, info = env.step(action_list)
                if writer is not None:
                    writer.append_step(env, action_list, obs, reward, terminated, truncated, info)
                total_reward += float(reward)
                length += 1
                max_x = max(max_x, env._x)
                final_score = int(info.get("combat", {}).get("score", env.score))
                max_score = max(max_score, final_score)
                actions[tuple(action_list)] += 1
                visible_enemy_bullet_counts.append(int(info.get("visible_enemy_bullets_current", 0)))
        finally:
            if writer is not None:
                writer.close()
            env.close()

        defensive = info.get("defensive_diagnostics", {})
        stats.append(
            {
                "episode": episode,
                "reward": total_reward,
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
                "action_frequencies": {"|".join(map(str, k)): v for k, v in actions.items()},
            }
        )

    report = build_evaluation_report(
        layout=layout,
        model_path=model_path,
        effective_model_choice=effective_model_choice,
        training_profile=args.training_profile,
        max_episode_steps=args.max_episode_steps,
        episodes=args.episodes,
        stats=stats,
        replay_paths=replay_paths,
    )
    write_json_file(report_path, report)
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
