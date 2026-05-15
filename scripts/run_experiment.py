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
    parser.add_argument("--train-eval", choices=["on", "off"], default="on")
    parser.add_argument("--eval-freq", type=int, default=None)
    parser.add_argument("--train-eval-episodes", type=int, default=5)
    parser.add_argument("--eval-vec-env", choices=["dummy", "subproc", "same"], default="dummy")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--wandb", choices=["off", "on"], default="off")
    parser.add_argument("--eval-episodes", type=int, default=5)
    parser.add_argument("--experiment-name", type=str, default=None)
    parser.add_argument("--save-replays", action="store_true")
    parser.add_argument("--training-profile", choices=["legacy", "combat_v1", "combat_bullets_v1"], default="combat_v1")
    parser.add_argument("--control-mode", choices=["full", "movement_scripted_attack_direct", "movement_no_boost_scripted_attack_direct"], default="full")
    parser.add_argument("--max-episode-steps", type=int, default=1800)
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--net-arch", type=str, default=None, help="Comma-separated list of hidden layer sizes (e.g. '128,128')")
    parser.add_argument("--timing-profile", choices=["on", "off"], default="off")
    parser.add_argument("--torch-num-threads", type=int, default=None)
    args = parser.parse_args()

    import time
    orchestration_start = time.perf_counter()

    train_args = [
        "--total-timesteps", str(args.total_timesteps),
        "--seed", str(args.seed),
        "--n-envs", str(args.n_envs),
        "--vec-env", args.vec_env,
        "--train-eval", args.train_eval,
        "--train-eval-episodes", str(args.train_eval_episodes),
        "--eval-vec-env", args.eval_vec_env,
        "--device", str(args.device),
        "--wandb", args.wandb,
        "--training-profile", args.training_profile,
        "--control-mode", args.control_mode,
        "--max-episode-steps", str(args.max_episode_steps),
        "--no-wandb-finish",
        "--timing-profile", args.timing_profile,
    ]
    if args.net_arch is not None:
        train_args.extend(["--net-arch", args.net_arch])
    if args.torch_num_threads is not None:
        train_args.extend(["--torch-num-threads", str(args.torch_num_threads)])
    if args.eval_freq is not None:
        train_args.extend(["--eval-freq", str(args.eval_freq)])
    if args.experiment_name is not None:
        train_args.extend(["--experiment-name", args.experiment_name])

    print("=== Phase 1: Training ===")
    train_start = time.perf_counter()
    layout = train_parkour.main(train_args)
    train_duration = time.perf_counter() - train_start

    print("\n=== Phase 2: Evaluation ===")
    eval_durations = {}
    
    def run_eval(model_choice: str):
        eval_args = [
            "--experiment", str(layout.path),
            "--model-choice", model_choice,
            "--episodes", str(args.eval_episodes),
            "--seed", str(args.seed + 1000),
            "--training-profile", args.training_profile,
            "--control-mode", args.control_mode,
            "--max-episode-steps", str(args.max_episode_steps),
        ]
        if args.save_replays:
            eval_args.append("--save-replays")
        print(f"\n--- Evaluating {model_choice} model ---")
        start = time.perf_counter()
        evaluate_model.main(eval_args)
        eval_durations[model_choice] = time.perf_counter() - start

    if (layout.models_dir / "best.zip").exists():
        run_eval("best")
    if (layout.models_dir / "latest.zip").exists():
        run_eval("latest")

    print("\n=== Phase 3: Updating Summary ===")
    summary_start = time.perf_counter()
    summary_path = layout.path / "summary.md"
    try:
        best_report_path = layout.report_path("best")
        latest_report_path = layout.report_path("latest")
        
        best_report = None
        if best_report_path.exists():
            with open(best_report_path, "r") as f:
                best_report = json.load(f)
                
        latest_report = None
        if latest_report_path.exists():
            with open(latest_report_path, "r") as f:
                latest_report = json.load(f)

        if best_report is None and latest_report is None:
            raise ValueError("No evaluation reports found.")
            
        ref_report = best_report if best_report is not None else latest_report

        summary_content = ""
        if summary_path.exists():
            with open(summary_path, "r") as f:
                summary_content = f.read()

        net_arch = ref_report.get("net_arch", "default")
        summary_content += f"\n\n## Evaluation Results ({args.eval_episodes} episodes) [net_arch: {net_arch}]\n\n"
        summary_content += "| Metric | Best Model | Latest Model |\n"
        summary_content += "|---|---|---|\n"

        def fmt_number(value):
            return "n/a" if value is None else f"{float(value):.2f}"

        def fmt_percent(value):
            return "n/a" if value is None else f"{float(value):.2%}"
        
        metrics = ["reward", "length", "heli_kills", "player_damage", "final_score"]
        for m in metrics:
            best_val = best_report["metrics"][m]["mean"] if best_report else None
            latest_val = latest_report["metrics"][m]["mean"] if latest_report else None
            summary_content += f"| Mean {m.replace('_', ' ').title()} | {fmt_number(best_val)} | {fmt_number(latest_val)} |\n"
            
        rates = ["hit_rate", "death_rate", "timeout_rate"]
        for r in rates:
            best_val = best_report["rates"].get(r) if best_report else None
            latest_val = latest_report["rates"].get(r) if latest_report else None
            summary_content += f"| {r.replace('_', ' ').title()} | {fmt_percent(best_val)} | {fmt_percent(latest_val)} |\n"

        movement_metrics = [
            ("frames_grounded", "Frames Grounded"),
            ("frames_airborne", "Frames Airborne"),
            ("frames_moving_left", "Frames Moving Left"),
            ("frames_moving_right", "Frames Moving Right"),
            ("frames_boost_pressed", "Frames Boost Pressed"),
            ("frames_boost_ready", "Frames Boost Ready"),
            ("boost_activations", "Boost Activations"),
            ("frames_jump_pressed", "Frames Jump Pressed"),
        ]
        for key, label in movement_metrics:
            best_val = best_report["metrics"].get(key, {}).get("mean") if best_report else None
            latest_val = latest_report["metrics"].get(key, {}).get("mean") if latest_report else None
            summary_content += f"| Mean {label} | {fmt_number(best_val)} | {fmt_number(latest_val)} |\n"

        defensive_metrics = [
            ("visible_enemy_bullets_seen_unique", "Visible Bullets Seen"),
            ("visible_enemy_bullets_max", "Max Visible Bullets"),
            ("visible_enemy_bullets_over_top10_frames", "Frames Over 10 Visible Bullets"),
            ("damage_events", "Mean Damage Events"),
            ("time_to_first_damage", "Mean Time To First Damage"),
            ("longest_damage_free_streak", "Mean Longest Damage-Free Streak"),
        ]
        for key, label in defensive_metrics:
            best_val = best_report["metrics"].get(key, {}).get("mean") if best_report else None
            latest_val = latest_report["metrics"].get(key, {}).get("mean") if latest_report else None
            summary_content += f"| {label} | {fmt_number(best_val)} | {fmt_number(latest_val)} |\n"

        defensive_rates = [
            ("visible_enemy_bullet_hit_rate_against_player", "Visible Bullet Hit Rate"),
            ("damage_free_episode_rate", "Damage-Free Episodes"),
        ]
        for key, label in defensive_rates:
            best_val = best_report["rates"].get(key) if best_report else None
            latest_val = latest_report["rates"].get(key) if latest_report else None
            summary_content += f"| {label} | {fmt_percent(best_val)} | {fmt_percent(latest_val)} |\n"

        with open(summary_path, "w") as f:
            f.write(summary_content)
        print(f"Updated {summary_path}")

    except Exception as e:
        print(f"Warning: Could not update summary.md: {e}")
    summary_duration = time.perf_counter() - summary_start

    wandb_duration = 0.0
    if args.wandb == "on":
        print("\n=== Phase 4: WandB Upload ===")
        wandb_start = time.perf_counter()
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
        wandb_duration = time.perf_counter() - wandb_start

    print("\n=== Phase 5: Diagnostic Bundle ===")
    bundle_start = time.perf_counter()
    bundle_name = f"{layout.path.name}_diagnostic_bundle.zip"
    bundle_path = layout.path / bundle_name
    
    files_to_bundle = [
        layout.path / "config.json",
        layout.path / "git_info.txt",
        layout.path / "summary.md",
        layout.path / "reports" / "eval_best.json",
        layout.path / "reports" / "eval_latest.json",
        layout.path / "replays" / "best_eval_ep0.jsonl",
        layout.path / "replays" / "latest_eval_ep0.jsonl",
        layout.path / "reports" / "timing" / "train_timing.json",
        layout.path / "reports" / "timing" / "train_timing.md",
    ]
    
    bundled_count = 0
    with zipfile.ZipFile(bundle_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for f in files_to_bundle:
            if f.exists():
                zipf.write(f, arcname=f.name)
                bundled_count += 1
                
    bundle_duration = time.perf_counter() - bundle_start
    orchestration_duration = time.perf_counter() - orchestration_start

    if args.timing_profile == "on":
        print("\n=== Phase 6: Orchestration Timing ===")
        timing_report = {
            "total_orchestration_seconds": orchestration_duration,
            "phases": {
                "training": train_duration,
                "eval_best": eval_durations.get("best", 0.0),
                "eval_latest": eval_durations.get("latest", 0.0),
                "summary_update": summary_duration,
                "wandb_upload": wandb_duration,
                "diagnostic_bundle": bundle_duration,
            }
        }
        timing_path = layout.path / "reports" / "timing" / "orchestration_timing.json"
        timing_path.parent.mkdir(parents=True, exist_ok=True)
        with open(timing_path, "w") as f:
            json.dump(timing_report, f, indent=2)
        
        md_lines = [
            "# Orchestration Timing Report",
            "",
            "| Phase | Seconds | % of Total |",
            "|---|---|---|",
            f"| Training | {train_duration:.2f} | {train_duration/orchestration_duration:.1%} |",
            f"| Eval Best | {eval_durations.get('best', 0.0):.2f} | {eval_durations.get('best', 0.0)/orchestration_duration:.1%} |",
            f"| Eval Latest | {eval_durations.get('latest', 0.0):.2f} | {eval_durations.get('latest', 0.0)/orchestration_duration:.1%} |",
            f"| Summary Update | {summary_duration:.2f} | {summary_duration/orchestration_duration:.1%} |",
            f"| WandB Upload | {wandb_duration:.2f} | {wandb_duration/orchestration_duration:.1%} |",
            f"| Bundle | {bundle_duration:.2f} | {bundle_duration/orchestration_duration:.1%} |",
            f"| **Total** | **{orchestration_duration:.2f}** | **100%** |",
        ]
        with open(timing_path.with_suffix(".md"), "w") as f:
            f.write("\n".join(md_lines) + "\n")
        print(f"Wrote orchestration timing report to {timing_path.parent}")
        
        # Append timing files to the bundle now that they are complete
        with zipfile.ZipFile(bundle_path, 'a', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(timing_path, arcname=timing_path.name)
            zipf.write(timing_path.with_suffix(".md"), arcname=timing_path.with_suffix(".md").name)
            bundled_count += 2

    print(f"Finalized {bundle_path} with {bundled_count} files.")

if __name__ == "__main__":
    main()
