from __future__ import annotations

import argparse
from pathlib import Path

from scripts import train_parkour
from scripts import evaluate_model

def main() -> None:
    parser = argparse.ArgumentParser(description="Orchestrate HA2 PPO training and evaluation.")
    parser.add_argument("--total-timesteps", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--n-envs", type=int, default=1)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--wandb", choices=["off", "on"], default="off")
    parser.add_argument("--eval-episodes", type=int, default=5)
    parser.add_argument("--experiment-name", type=str, default=None)
    parser.add_argument("--save-replays", action="store_true")
    parser.add_argument("--max-episode-steps", type=int, default=1800)
    parser.add_argument("--watch", action="store_true")
    args = parser.parse_args()

    train_args = [
        "--total-timesteps", str(args.total_timesteps),
        "--seed", str(args.seed),
        "--n-envs", str(args.n_envs),
        "--device", str(args.device),
        "--wandb", args.wandb,
        "--max-episode-steps", str(args.max_episode_steps),
        "--no-wandb-finish"
    ]
    if args.experiment_name is not None:
        train_args.extend(["--experiment-name", args.experiment_name])

    print("=== Phase 1: Training ===")
    layout = train_parkour.main(train_args)

    print("\n=== Phase 2: Evaluation ===")
    eval_args = [
        "--experiment", str(layout.path),
        "--model-choice", "best",
        "--episodes", str(args.eval_episodes),
        "--seed", str(args.seed + 1000),
        "--max-episode-steps", str(args.max_episode_steps),
    ]
    if args.save_replays:
        eval_args.append("--save-replays")
    evaluate_model.main(eval_args)

    if args.wandb == "on":
        print("\n=== Phase 3: WandB Upload ===")
        import wandb
        print(f"Uploading experiment artifacts to wandb...")
        artifact = wandb.Artifact(
            name=layout.path.name,
            type="experiment",
            metadata=dict(wandb.config) if wandb.run else None,
        )
        for item in layout.path.iterdir():
            if item.name == "wandb":
                continue
            if item.is_dir():
                artifact.add_dir(str(item), name=item.name)
            else:
                artifact.add_file(str(item), name=item.name)
        wandb.log_artifact(artifact)
        wandb.finish()

if __name__ == "__main__":
    main()
