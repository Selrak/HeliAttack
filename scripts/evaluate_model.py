from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from ha2_env import HeliAttack2Env
from ha2_replay import JsonlReplayWriter


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a trained HA2 model.")
    parser.add_argument("--model", type=Path, default=None)
    parser.add_argument("--episodes", type=int, default=5)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--save-replays", action="store_true")
    parser.add_argument("--out", type=Path, default=Path("reports/eval.json"))
    parser.add_argument("--training-profile", choices=["legacy", "combat_v1"], default="combat_v1")
    parser.add_argument("--max-episode-steps", type=int, default=1800)
    args = parser.parse_args()

    PPO = _load_ppo()
    model_path = args.model or default_model_path()
    if not model_path.exists():
        raise SystemExit(f"Model not found: {model_path}")

    model = PPO.load(model_path)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    stats = []

    for episode in range(args.episodes):
        env = HeliAttack2Env(
            render_mode=None,
            training_profile=args.training_profile,
            max_episode_steps=args.max_episode_steps,
        )
        obs, _info = env.reset(seed=args.seed + episode)
        writer = None
        if args.save_replays:
            writer = JsonlReplayWriter(
                Path("replays") / f"eval_ep{episode}.jsonl",
                env,
                args.seed + episode,
                obs,
            )

        total_reward = 0.0
        length = 0
        max_x = env._x
        actions = Counter()
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
                "action_frequencies": {"|".join(map(str, k)): v for k, v in actions.items()},
            }
        )

    mean_reward = sum(row["reward"] for row in stats) / len(stats)
    mean_length = sum(row["length"] for row in stats) / len(stats)
    report = {
        "model": str(model_path),
        "training_profile": args.training_profile,
        "max_episode_steps": args.max_episode_steps,
        "episodes": args.episodes,
        "mean_reward": mean_reward,
        "mean_episode_length": mean_length,
        "episodes_detail": stats,
    }
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
