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
    parser.add_argument("--training-profile", choices=["legacy", "combat_v1"], default="combat_v1")
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
        finally:
            if writer is not None:
                writer.close()
            env.close()

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
                "action_frequencies": {"|".join(map(str, k)): v for k, v in actions.items()},
            }
        )

    def agg_metric(key: str) -> dict[str, float]:
        if not stats:
            return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0, "sum": 0.0}
        vals = [float(row[key]) for row in stats]
        return {
            "mean": float(np.mean(vals)),
            "std": float(np.std(vals)),
            "min": float(np.min(vals)),
            "max": float(np.max(vals)),
            "sum": float(np.sum(vals)),
        }

    termination_reason_counts = Counter(row["termination_reason"] for row in stats)
    
    # Marginal Action Distributions
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
    hit_rate = 0.0
    if bullets_spawned_sum > 0:
        hit_rate = sum(row["heli_hits"] for row in stats) / float(bullets_spawned_sum)

    report = {
        "experiment": str(layout.path) if layout is not None else None,
        "model": str(model_path),
        "model_choice": effective_model_choice,
        "training_profile": args.training_profile,
        "max_episode_steps": args.max_episode_steps,
        "episodes": args.episodes,
        "metrics": {
            "reward": agg_metric("reward"),
            "length": agg_metric("length"),
            "heli_kills": agg_metric("heli_kills"),
            "heli_hits": agg_metric("heli_hits"),
            "player_shot_attempts": agg_metric("player_shot_attempts"),
            "player_bullets_spawned": agg_metric("player_bullets_spawned"),
            "player_shots_spawn_blocked": agg_metric("player_shots_spawn_blocked"),
            "player_damage": agg_metric("total_player_damage"),
            "enemy_bullet_hits": agg_metric("enemy_bullet_hits"),
            "final_score": agg_metric("final_score"),
            "max_score": agg_metric("max_score"),
        },
        "rates": {
            "hit_rate": hit_rate,
            "death_rate": sum(row["deaths"] for row in stats) / float(len(stats)) if stats else 0.0,
            "fall_rate": sum(row["falls"] for row in stats) / float(len(stats)) if stats else 0.0,
            "timeout_rate": sum(1 for row in stats if row["termination_reason"] == "time_limit") / float(len(stats)) if stats else 0.0,
        },
        "termination_reason_counts": dict(termination_reason_counts),
        "marginal_action_distributions": marginal_actions,
        "episodes_detail": stats,
        "replay_paths": replay_paths,
    }
    write_json_file(report_path, report)
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
