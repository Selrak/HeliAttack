from __future__ import annotations

import argparse
from contextlib import redirect_stdout
from datetime import datetime
import io
import json
from pathlib import Path
import re
import time

from scripts import train_parkour


DEFAULT_MATRIX = {
    "dummy": [1, 4, 8],
    "subproc": [2, 4, 8],
}


def parse_last_sb3_fps(output: str) -> int | None:
    matches = re.findall(r"\|\s*fps\s*\|\s*(\d+)\s*\|", output)
    return int(matches[-1]) if matches else None


def matrix_cases(vec_envs: list[str], n_envs: list[int] | None) -> list[tuple[str, int]]:
    cases: list[tuple[str, int]] = []
    for vec_env in vec_envs:
        values = n_envs if n_envs is not None else DEFAULT_MATRIX[vec_env]
        for n_env in values:
            cases.append((vec_env, int(n_env)))
    return cases


def run_one(args, *, vec_env: str, n_envs: int, repeat: int, timestamp: str) -> dict:
    experiment_name = f"bench_{timestamp}_{vec_env}_{n_envs}env_r{repeat}"
    train_args = [
        "--total-timesteps",
        str(args.total_timesteps),
        "--seed",
        str(args.seed + repeat),
        "--n-envs",
        str(n_envs),
        "--vec-env",
        vec_env,
        "--device",
        args.device,
        "--wandb",
        args.wandb,
        "--max-episode-steps",
        str(args.max_episode_steps),
        "--experiment-name",
        experiment_name,
        "--experiments-root",
        str(args.experiments_root),
        "--no-wandb-finish",
    ]
    stdout = io.StringIO()
    started = time.perf_counter()
    with redirect_stdout(stdout):
        layout = train_parkour.main(train_args)
    ended = time.perf_counter()
    output = stdout.getvalue()
    wall_seconds = ended - started
    return {
        "vec_env": vec_env,
        "n_envs": int(n_envs),
        "repeat": int(repeat),
        "success": True,
        "requested_timesteps": int(args.total_timesteps),
        "wall_clock_seconds": wall_seconds,
        "computed_steps_per_second": float(args.total_timesteps) / wall_seconds if wall_seconds > 0 else 0.0,
        "sb3_reported_fps": parse_last_sb3_fps(output),
        "experiment_path": str(layout.path),
        "exception": None,
    }


def write_markdown_report(path: Path, report: dict) -> None:
    lines = [
        "# HA2 VecEnv Benchmark",
        "",
        f"- created_at: `{report['created_at']}`",
        f"- total_timesteps: `{report['total_timesteps']}`",
        f"- device: `{report['device']}`",
        f"- wandb: `{report['wandb']}`",
        "",
        "| vec_env | n_envs | repeat | success | wall_s | computed steps/s | SB3 fps | experiment | error |",
        "|---|---:|---:|---|---:|---:|---:|---|---|",
    ]
    for row in report["results"]:
        lines.append(
            "| {vec_env} | {n_envs} | {repeat} | {success} | {wall:.2f} | {steps:.1f} | {fps} | {experiment} | {error} |".format(
                vec_env=row["vec_env"],
                n_envs=row["n_envs"],
                repeat=row["repeat"],
                success="yes" if row["success"] else "no",
                wall=float(row.get("wall_clock_seconds") or 0.0),
                steps=float(row.get("computed_steps_per_second") or 0.0),
                fps=row.get("sb3_reported_fps") if row.get("sb3_reported_fps") is not None else "",
                experiment=row.get("experiment_path") or "",
                error=(row.get("exception") or "").replace("|", "\\|"),
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(args_list: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Benchmark DummyVecEnv vs SubprocVecEnv using short HA2 PPO runs.")
    parser.add_argument("--total-timesteps", type=int, default=4096)
    parser.add_argument("--n-envs", nargs="+", type=int, default=None)
    parser.add_argument("--vec-envs", nargs="+", choices=["dummy", "subproc"], default=["dummy", "subproc"])
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--wandb", choices=["off", "on"], default="off")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-episode-steps", type=int, default=1800)
    parser.add_argument("--out-dir", type=Path, default=Path("reports/vec_env_benchmarks"))
    parser.add_argument("--experiments-root", type=Path, default=Path("experiments"))
    args = parser.parse_args(args_list)

    if args.total_timesteps <= 0:
        raise SystemExit("--total-timesteps must be positive")
    if args.repeats <= 0:
        raise SystemExit("--repeats must be positive")
    if args.n_envs is not None and any(value <= 0 for value in args.n_envs):
        raise SystemExit("--n-envs values must be positive")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = []
    for vec_env, n_envs in matrix_cases(args.vec_envs, args.n_envs):
        for repeat in range(args.repeats):
            print(f"Benchmarking vec_env={vec_env} n_envs={n_envs} repeat={repeat}...")
            try:
                row = run_one(args, vec_env=vec_env, n_envs=n_envs, repeat=repeat, timestamp=timestamp)
            except Exception as exc:
                row = {
                    "vec_env": vec_env,
                    "n_envs": int(n_envs),
                    "repeat": int(repeat),
                    "success": False,
                    "requested_timesteps": int(args.total_timesteps),
                    "wall_clock_seconds": None,
                    "computed_steps_per_second": None,
                    "sb3_reported_fps": None,
                    "experiment_path": None,
                    "exception": f"{exc.__class__.__name__}: {exc}",
                }
            results.append(row)

    report = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "total_timesteps": int(args.total_timesteps),
        "device": args.device,
        "wandb": args.wandb,
        "results": results,
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / f"{timestamp}_vec_env_benchmark.json"
    md_path = args.out_dir / f"{timestamp}_vec_env_benchmark.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown_report(md_path, report)

    print("\nvec_env  n_envs  repeat  success  wall_s  steps/s  sb3_fps")
    for row in results:
        print(
            f"{row['vec_env']:7} {row['n_envs']:6} {row['repeat']:7} "
            f"{str(row['success']):7} "
            f"{(row.get('wall_clock_seconds') or 0.0):6.2f} "
            f"{(row.get('computed_steps_per_second') or 0.0):8.1f} "
            f"{row.get('sb3_reported_fps') or '-'}"
        )
        if not row["success"]:
            print(f"  error: {row['exception']}")
    print(f"\nWrote {json_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
