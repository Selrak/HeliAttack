from __future__ import annotations

import argparse
import json
from pathlib import Path
import zipfile

from scripts import train_parkour
from scripts import evaluate_model

def main() -> None:
    parser = argparse.ArgumentParser(description="Orchestrate HA2 PPO training and evaluation.")
    parser.add_argument("--total-timesteps", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--n-envs", type=int, default=1)
    parser.add_argument("--vec-env", choices=["dummy", "subproc"], default="dummy")
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
        "--vec-env", args.vec_env,
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
    
    def run_eval(model_choice: str):
        eval_args = [
            "--experiment", str(layout.path),
            "--model-choice", model_choice,
            "--episodes", str(args.eval_episodes),
            "--seed", str(args.seed + 1000),
            "--max-episode-steps", str(args.max_episode_steps),
        ]
        if args.save_replays:
            eval_args.append("--save-replays")
        print(f"\n--- Evaluating {model_choice} model ---")
        evaluate_model.main(eval_args)

    run_eval("best")
    run_eval("latest")

    print("\n=== Phase 3: Updating Summary ===")
    summary_path = layout.path / "summary.md"
    try:
        best_report_path = layout.report_path("best")
        latest_report_path = layout.report_path("latest")
        
        with open(best_report_path, "r") as f:
            best_report = json.load(f)
        with open(latest_report_path, "r") as f:
            latest_report = json.load(f)

        summary_content = ""
        if summary_path.exists():
            with open(summary_path, "r") as f:
                summary_content = f.read()

        summary_content += f"\n\n## Evaluation Results ({args.eval_episodes} episodes)\n\n"
        summary_content += "| Metric | Best Model | Latest Model |\n"
        summary_content += "|---|---|---|\n"
        
        metrics = ["reward", "length", "heli_kills", "player_damage", "final_score"]
        for m in metrics:
            best_val = best_report["metrics"][m]["mean"]
            latest_val = latest_report["metrics"][m]["mean"]
            summary_content += f"| Mean {m.replace('_', ' ').title()} | {best_val:.2f} | {latest_val:.2f} |\n"
            
        rates = ["hit_rate", "death_rate", "timeout_rate"]
        for r in rates:
            best_val = best_report["rates"].get(r, 0.0)
            latest_val = latest_report["rates"].get(r, 0.0)
            summary_content += f"| {r.replace('_', ' ').title()} | {best_val:.2%} | {latest_val:.2%} |\n"

        with open(summary_path, "w") as f:
            f.write(summary_content)
        print(f"Updated {summary_path}")

    except Exception as e:
        print(f"Warning: Could not update summary.md: {e}")

    if args.wandb == "on":
        print("\n=== Phase 4: WandB Upload ===")
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

    print("\n=== Phase 5: Diagnostic Bundle ===")
    bundle_name = f"{layout.path.name}_diagnostic_bundle.zip"
    bundle_path = layout.path / bundle_name
    
    files_to_bundle = [
        layout.path / "config.json",
        layout.path / "git_info.txt",
        layout.path / "summary.md",
        layout.path / "reports" / "eval_best.json",
        layout.path / "replays" / "best_eval_ep0.jsonl"
    ]
    
    bundled_count = 0
    with zipfile.ZipFile(bundle_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for f in files_to_bundle:
            if f.exists():
                # Store in zip with the file's name only, or keep a minimal structure
                zipf.write(f, arcname=f.name)
                bundled_count += 1
                
    print(f"Created {bundle_path} with {bundled_count} files.")

if __name__ == "__main__":
    main()
