from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
import io
import json
from pathlib import Path
import re
import time
import warnings

from scripts import train_parkour


DEFAULT_MATRIX = {
    "dummy": [1, 4, 8],
    "subproc": [2, 4, 8],
}


def parse_last_sb3_fps(output: str) -> int | None:
    matches = re.findall(r"\|\s*fps\s*\|\s*(\d+)\s*\|", output)
    return int(matches[-1]) if matches else None


def parse_last_sb3_total_timesteps(output: str) -> int | None:
    matches = re.findall(r"\|\s*total_timesteps\s*\|\s*(\d+)\s*\|", output)
    return int(matches[-1]) if matches else None


def matrix_cases(vec_envs: list[str], n_envs: list[int] | None) -> list[tuple[str, int]]:
    cases: list[tuple[str, int]] = []
    for vec_env in vec_envs:
        values = n_envs if n_envs is not None else DEFAULT_MATRIX[vec_env]
        for n_env in values:
            cases.append((vec_env, int(n_env)))
    return cases


def benchmark_modes(mode: str) -> list[str]:
    if mode == "both":
        return ["train-only", "workflow"]
    return [mode]


def effective_eval_vec_env(vec_env: str, eval_vec_env: str) -> str:
    if eval_vec_env == "same":
        return vec_env
    return eval_vec_env


def _base_row(args, *, mode: str, vec_env: str, n_envs: int, repeat: int) -> dict:
    train_eval_enabled = mode == "workflow"
    effective_eval = effective_eval_vec_env(vec_env, args.eval_vec_env) if train_eval_enabled else None
    return {
        "mode": mode,
        "vec_env": vec_env,
        "eval_vec_env": args.eval_vec_env if train_eval_enabled else None,
        "effective_eval_vec_env": effective_eval,
        "n_envs": int(n_envs),
        "repeat": int(repeat),
        "requested_timesteps": int(args.total_timesteps),
        "actual_total_timesteps": None,
        "wall_clock_seconds": None,
        "computed_requested_steps_per_second": None,
        "computed_actual_steps_per_second": None,
        "sb3_reported_fps": None,
        "train_eval_enabled": train_eval_enabled,
        "eval_freq": int(args.eval_freq) if args.eval_freq is not None else None,
        "train_eval_episodes": int(args.train_eval_episodes) if train_eval_enabled else None,
        "train_eval_vec_env_match": effective_eval == vec_env if train_eval_enabled else None,
        "sb3_wrapper_mismatch_warning": False,
        "experiment_path": None,
        "success": False,
        "exception": None,
    }


def run_one(args, *, mode: str, vec_env: str, n_envs: int, repeat: int, timestamp: str) -> dict:
    row = _base_row(args, mode=mode, vec_env=vec_env, n_envs=n_envs, repeat=repeat)
    experiment_name = f"bench_{timestamp}_{mode}_{vec_env}_{n_envs}env_r{repeat}"
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
    if mode == "train-only":
        train_args.extend(["--train-eval", "off"])
    else:
        train_args.extend(
            [
                "--train-eval",
                "on",
                "--train-eval-episodes",
                str(args.train_eval_episodes),
                "--eval-vec-env",
                args.eval_vec_env,
            ]
        )
        if args.eval_freq is not None:
            train_args.extend(["--eval-freq", str(args.eval_freq)])
    stdout = io.StringIO()
    stderr = io.StringIO()
    started = time.perf_counter()
    caught_warnings = []
    try:
        with warnings.catch_warnings(record=True) as records:
            warnings.simplefilter("always")
            with redirect_stdout(stdout), redirect_stderr(stderr):
                layout = train_parkour.main(train_args)
        caught_warnings = [str(record.message) for record in records]
        row["success"] = True
        row["experiment_path"] = str(layout.path)
    except Exception as exc:
        row["exception"] = f"{exc.__class__.__name__}: {exc}"
    ended = time.perf_counter()
    output = stdout.getvalue()
    warning_text = "\n".join(caught_warnings + [stderr.getvalue(), output])
    wall_seconds = ended - started
    actual_timesteps = parse_last_sb3_total_timesteps(output)
    row["wall_clock_seconds"] = wall_seconds
    row["actual_total_timesteps"] = actual_timesteps
    row["computed_requested_steps_per_second"] = float(args.total_timesteps) / wall_seconds if wall_seconds > 0 else 0.0
    row["computed_actual_steps_per_second"] = (
        float(actual_timesteps) / wall_seconds if actual_timesteps is not None and wall_seconds > 0 else None
    )
    row["sb3_reported_fps"] = parse_last_sb3_fps(output)
    row["sb3_wrapper_mismatch_warning"] = "not of the same type" in warning_text.lower()
    return row


def _successful_rows(report: dict) -> list[dict]:
    return [row for row in report["results"] if row.get("success") and row.get("wall_clock_seconds") is not None]


def _best_row(rows: list[dict], *, key: str, value: str) -> dict | None:
    matching = [row for row in rows if row.get(key) == value]
    if not matching:
        return None
    return min(matching, key=lambda row: float(row["wall_clock_seconds"]))


def _average_steps_by_group(rows: list[dict]) -> list[tuple[str, str, int, float]]:
    groups: dict[tuple[str, str, int], list[float]] = {}
    for row in rows:
        steps = row.get("computed_requested_steps_per_second")
        if steps is None:
            continue
        key = (row["mode"], row["vec_env"], int(row["n_envs"]))
        groups.setdefault(key, []).append(float(steps))
    return [
        (mode, vec_env, n_envs, sum(values) / len(values))
        for (mode, vec_env, n_envs), values in sorted(groups.items())
    ]


def write_markdown_report(path: Path, report: dict) -> None:
    lines = [
        "# HA2 VecEnv Benchmark",
        "",
        f"- created_at: `{report['created_at']}`",
        f"- total_timesteps: `{report['total_timesteps']}`",
        f"- mode: `{report['mode']}`",
        f"- device: `{report['device']}`",
        f"- wandb: `{report['wandb']}`",
        "",
        "Wall-clock time and measured steps/s are the primary metrics; SB3 fps is reported for reference only.",
        "",
        "## Results",
        "",
        "| mode | vec_env | eval_vec_env | n_envs | repeat | success | wall_s | requested steps/s | actual steps/s | SB3 fps | eval | wrapper match | mismatch warning | experiment | error |",
        "|---|---|---|---:|---:|---|---:|---:|---:|---:|---|---|---|---|---|",
    ]
    for row in report["results"]:
        lines.append(
            "| {mode} | {vec_env} | {eval_vec_env} | {n_envs} | {repeat} | {success} | {wall:.2f} | {requested_steps:.1f} | {actual_steps} | {fps} | {eval_enabled} | {wrapper_match} | {mismatch} | {experiment} | {error} |".format(
                mode=row["mode"],
                vec_env=row["vec_env"],
                eval_vec_env=row.get("effective_eval_vec_env") or "",
                n_envs=row["n_envs"],
                repeat=row["repeat"],
                success="yes" if row["success"] else "no",
                wall=float(row.get("wall_clock_seconds") or 0.0),
                requested_steps=float(row.get("computed_requested_steps_per_second") or 0.0),
                actual_steps=(
                    f"{float(row['computed_actual_steps_per_second']):.1f}"
                    if row.get("computed_actual_steps_per_second") is not None
                    else ""
                ),
                fps=row.get("sb3_reported_fps") if row.get("sb3_reported_fps") is not None else "",
                eval_enabled="yes" if row.get("train_eval_enabled") else "no",
                wrapper_match=(
                    "yes"
                    if row.get("train_eval_vec_env_match") is True
                    else "no"
                    if row.get("train_eval_vec_env_match") is False
                    else ""
                ),
                mismatch="yes" if row.get("sb3_wrapper_mismatch_warning") else "no",
                experiment=row.get("experiment_path") or "",
                error=(row.get("exception") or "").replace("|", "\\|"),
            )
        )
    rows = _successful_rows(report)
    lines.extend(["", "## Summary", ""])
    lines.append("| mode | best wall_s | vec_env | n_envs | requested steps/s |")
    lines.append("|---|---:|---|---:|---:|")
    for mode in sorted({row["mode"] for row in rows}):
        best = _best_row(rows, key="mode", value=mode)
        if best is not None:
            lines.append(
                f"| {mode} | {float(best['wall_clock_seconds']):.2f} | {best['vec_env']} | {best['n_envs']} | {float(best['computed_requested_steps_per_second']):.1f} |"
            )
    lines.extend(["", "| vec_env | best mode | best wall_s | n_envs | requested steps/s |", "|---|---|---:|---:|---:|"])
    for vec_env in sorted({row["vec_env"] for row in rows}):
        best = _best_row(rows, key="vec_env", value=vec_env)
        if best is not None:
            lines.append(
                f"| {vec_env} | {best['mode']} | {float(best['wall_clock_seconds']):.2f} | {best['n_envs']} | {float(best['computed_requested_steps_per_second']):.1f} |"
            )
    lines.extend(["", "| mode | vec_env | n_envs | avg requested steps/s |", "|---|---|---:|---:|"])
    for mode, vec_env, n_envs, avg_steps in _average_steps_by_group(rows):
        lines.append(f"| {mode} | {vec_env} | {n_envs} | {avg_steps:.1f} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(args_list: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark DummyVecEnv vs SubprocVecEnv using short HA2 PPO runs. Default mode is train-only for speed."
    )
    parser.add_argument("--mode", choices=["train-only", "workflow", "both"], default="train-only")
    parser.add_argument("--total-timesteps", type=int, default=4096)
    parser.add_argument("--n-envs", nargs="+", type=int, default=None)
    parser.add_argument("--vec-envs", nargs="+", choices=["dummy", "subproc"], default=["dummy", "subproc"])
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--wandb", choices=["off", "on"], default="off")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--eval-vec-env", choices=["dummy", "subproc", "same"], default="dummy")
    parser.add_argument("--eval-freq", type=int, default=None)
    parser.add_argument("--train-eval-episodes", type=int, default=1)
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
    if args.eval_freq is not None and args.eval_freq <= 0:
        raise SystemExit("--eval-freq must be positive")
    if args.train_eval_episodes <= 0:
        raise SystemExit("--train-eval-episodes must be positive")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = []
    for mode in benchmark_modes(args.mode):
        for vec_env, n_envs in matrix_cases(args.vec_envs, args.n_envs):
            for repeat in range(args.repeats):
                print(f"Benchmarking mode={mode} vec_env={vec_env} n_envs={n_envs} repeat={repeat}...")
                results.append(run_one(args, mode=mode, vec_env=vec_env, n_envs=n_envs, repeat=repeat, timestamp=timestamp))

    report = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "total_timesteps": int(args.total_timesteps),
        "mode": args.mode,
        "device": args.device,
        "wandb": args.wandb,
        "eval_vec_env": args.eval_vec_env,
        "eval_freq": int(args.eval_freq) if args.eval_freq is not None else None,
        "train_eval_episodes": int(args.train_eval_episodes),
        "results": results,
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / f"{timestamp}_vec_env_benchmark.json"
    md_path = args.out_dir / f"{timestamp}_vec_env_benchmark.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown_report(md_path, report)

    print("\nmode        vec_env  n_envs  repeat  success  wall_s  req_steps/s  actual_steps/s  sb3_fps  mismatch")
    for row in results:
        print(
            f"{row['mode']:11} {row['vec_env']:7} {row['n_envs']:6} {row['repeat']:7} "
            f"{str(row['success']):7} "
            f"{(row.get('wall_clock_seconds') or 0.0):6.2f} "
            f"{(row.get('computed_requested_steps_per_second') or 0.0):11.1f} "
            f"{(row.get('computed_actual_steps_per_second') or 0.0):14.1f} "
            f"{row.get('sb3_reported_fps') or '-':>7} "
            f"{str(row.get('sb3_wrapper_mismatch_warning'))}"
        )
        if not row["success"]:
            print(f"  error: {row['exception']}")
    print(f"\nWrote {json_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
