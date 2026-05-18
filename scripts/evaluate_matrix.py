from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.experiment_utils import resolve_model_path, write_json_file, write_text_file
from scripts.invocation_metadata import (
    argv_for_module,
    capture_invocation_metadata,
    reconstruct_command_for_display,
    write_invocation_files,
    write_resolved_config,
)
from scripts.runtime_config import parse_human_count


MATRIX_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
MODEL_CHOICES = {"best", "latest"}


@dataclass(frozen=True)
class MatrixEntry:
    label: str
    experiment: Path
    model: str


@dataclass
class EvalJob:
    eval_id: str
    index: int
    entry: MatrixEntry
    pressure_profile: str
    output_dir: Path
    report_name: str
    source_report_path: Path
    copied_report_path: Path
    stdout_log_path: Path
    stderr_log_path: Path
    command_path: Path
    metadata_path: Path
    parent_config_path: Path | None
    command: list[str]
    env_updates: dict[str, str]
    metadata: dict[str, Any]


def split_csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def slugify(value: str, *, max_length: int = 48) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value).strip())
    slug = slug.strip("-_.") or "item"
    return slug[:max_length].rstrip("-_.") or "item"


def short_hash(value: str, length: int = 8) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:length]


def parse_entry(value: str) -> MatrixEntry:
    fields: dict[str, str] = {}
    for chunk in value.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "=" not in chunk:
            raise argparse.ArgumentTypeError(f"Malformed --entry component without '=': {chunk!r}")
        key, field_value = chunk.split("=", 1)
        key = key.strip().lower()
        field_value = field_value.strip()
        if not key or not field_value:
            raise argparse.ArgumentTypeError(f"Malformed --entry component: {chunk!r}")
        if key in fields:
            raise argparse.ArgumentTypeError(f"Duplicate --entry key: {key}")
        fields[key] = field_value
    required = {"label", "experiment", "model"}
    missing = sorted(required - fields.keys())
    if missing:
        raise argparse.ArgumentTypeError(f"Missing --entry field(s): {', '.join(missing)}")
    extra = sorted(set(fields) - required)
    if extra:
        raise argparse.ArgumentTypeError(f"Unsupported --entry field(s): {', '.join(extra)}")
    return MatrixEntry(
        label=fields["label"],
        experiment=Path(fields["experiment"]),
        model=fields["model"],
    )


def validate_entries(entries: list[MatrixEntry]) -> None:
    if not entries:
        raise SystemExit("At least one --entry is required.")
    labels = [entry.label for entry in entries]
    duplicates = sorted({label for label in labels if labels.count(label) > 1})
    if duplicates:
        raise SystemExit(f"Duplicate --entry label(s) are ambiguous: {', '.join(duplicates)}")


def unique_matrix_dir(output_root: Path, matrix_name: str, timestamp: str | None = None) -> tuple[str, Path]:
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    base_id = f"{slugify(matrix_name)}_{timestamp or datetime.now().strftime(MATRIX_TIMESTAMP_FORMAT)}"
    candidate = output_root / base_id
    if not candidate.exists():
        return base_id, candidate
    index = 2
    while True:
        matrix_id = f"{base_id}_{index}"
        candidate = output_root / matrix_id
        if not candidate.exists():
            return matrix_id, candidate
        index += 1


def make_eval_id(index: int, label: str, model: str, pressure_profile: str, max_length: int = 96) -> str:
    base = (
        f"{index:03d}_"
        f"{slugify(label, max_length=24)}_"
        f"{slugify(model, max_length=16)}_"
        f"pressure-{slugify(pressure_profile, max_length=36)}"
    )
    if len(base) <= max_length:
        return base
    digest = short_hash(base)
    prefix = base[: max_length - len(digest) - 1].rstrip("-_.")
    return f"{prefix}-{digest}"


def load_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_entry_model_path(entry: MatrixEntry) -> tuple[str, Path]:
    if entry.model in MODEL_CHOICES:
        return entry.model, resolve_model_path(model=None, experiment=entry.experiment, model_choice=entry.model)
    return "path", Path(entry.model)


def build_jobs(
    *,
    entries: list[MatrixEntry],
    pressure_profiles: list[str],
    matrix_id: str,
    matrix_dir: Path,
    episodes: int,
    max_episode_steps: int,
    save_replays: bool,
    threads_per_job: int,
    overrides: dict[str, str | None],
    timeout_seconds: int | None,
) -> list[EvalJob]:
    jobs: list[EvalJob] = []
    used_ids: set[str] = set()
    job_index = 1
    for pressure_profile in pressure_profiles:
        for entry in entries:
            model_choice, model_path = resolve_entry_model_path(entry)
            eval_id = make_eval_id(job_index, entry.label, entry.model, pressure_profile)
            if eval_id in used_ids:
                eval_id = f"{eval_id}-{short_hash(str(entry) + pressure_profile)}"
            used_ids.add(eval_id)
            parent_config_path = entry.experiment / "config.json"
            parent_config = load_json_if_exists(parent_config_path)
            job_dir = matrix_dir / "jobs" / eval_id
            source_report_name = f"{matrix_id}_{eval_id}.json"
            source_report_path = entry.experiment / "reports" / source_report_name
            command = [
                sys.executable,
                "-m",
                "scripts.evaluate_model",
                "--experiment",
                str(entry.experiment),
                "--model-choice",
                model_choice,
                "--episodes",
                str(episodes),
                "--max-episode-steps",
                str(max_episode_steps),
                "--pressure-profile",
                pressure_profile,
                "--report-name",
                source_report_name,
            ]
            if model_choice == "path":
                command.extend(["--model", str(model_path)])
            for field, value in overrides.items():
                if value is not None:
                    command.extend([f"--{field.replace('_', '-')}", value])
            if save_replays:
                command.extend(
                    [
                        "--save-replays",
                        "--replay-dir",
                        str(job_dir / "replays"),
                        "--replay-prefix",
                        eval_id,
                    ]
                )
            env_updates = {
                "OMP_NUM_THREADS": str(threads_per_job),
                "MKL_NUM_THREADS": str(threads_per_job),
                "NUMEXPR_NUM_THREADS": str(threads_per_job),
                "HA2_TORCH_NUM_THREADS": str(threads_per_job),
            }
            metadata = {
                "eval_id": eval_id,
                "label": entry.label,
                "experiment_path": str(entry.experiment),
                "model_choice": model_choice,
                "entry_model": entry.model,
                "resolved_model_path": str(model_path),
                "resolved_config_path": str(parent_config_path) if parent_config_path.exists() else None,
                "source_experiment_runtime_config": {
                    key: parent_config.get(key)
                    for key in (
                        "training_profile",
                        "control_mode",
                        "reward_profile",
                        "pressure_profile",
                        "max_episode_steps",
                    )
                },
                "evaluation_overrides": {key: value for key, value in overrides.items() if value is not None},
                "pressure_profile": pressure_profile,
                "control_mode": overrides.get("control_mode") or parent_config.get("control_mode"),
                "reward_profile": overrides.get("reward_profile") or parent_config.get("reward_profile"),
                "training_profile": overrides.get("training_profile") or parent_config.get("training_profile"),
                "parent_pressure_profile": parent_config.get("pressure_profile"),
                "max_episode_steps": max_episode_steps,
                "episodes": episodes,
                "timeout_seconds": timeout_seconds,
                "report_path_inside_original_experiment": str(source_report_path),
                "copied_report_path": str(job_dir / "eval_report.json"),
                "stdout_log_path": str(job_dir / "stdout.log"),
                "stderr_log_path": str(job_dir / "stderr.log"),
                "command_path": str(job_dir / "command.txt"),
                "env_updates": env_updates,
                "exit_code": None,
                "start_time": None,
                "end_time": None,
                "duration_seconds": None,
            }
            jobs.append(
                EvalJob(
                    eval_id=eval_id,
                    index=job_index,
                    entry=entry,
                    pressure_profile=pressure_profile,
                    output_dir=job_dir,
                    report_name=source_report_name,
                    source_report_path=source_report_path,
                    copied_report_path=job_dir / "eval_report.json",
                    stdout_log_path=job_dir / "stdout.log",
                    stderr_log_path=job_dir / "stderr.log",
                    command_path=job_dir / "command.txt",
                    metadata_path=job_dir / "metadata.json",
                    parent_config_path=parent_config_path if parent_config_path.exists() else None,
                    command=command,
                    env_updates=env_updates,
                    metadata=metadata,
                )
            )
            job_index += 1
    return jobs


def prepare_output_tree(matrix_dir: Path, jobs: list[EvalJob]) -> None:
    (matrix_dir / "logs").mkdir(parents=True, exist_ok=True)
    (matrix_dir / "jobs").mkdir(parents=True, exist_ok=True)
    for job in jobs:
        job.output_dir.mkdir(parents=True, exist_ok=True)
        write_text_file(job.command_path, reconstruct_command_for_display(job.command) + "\n", allow_overwrite=True)
        if job.parent_config_path is not None:
            shutil.copy2(job.parent_config_path, job.output_dir / "parent_config.json")
        write_json_file(job.metadata_path, job.metadata, allow_overwrite=True)


def run_jobs(
    jobs: list[EvalJob],
    *,
    max_parallel: int,
    timeout_seconds: int | None,
    fail_fast: bool,
) -> list[EvalJob]:
    total = len(jobs)
    pending = list(jobs)
    running: list[dict[str, Any]] = []
    completed: list[EvalJob] = []
    failed = 0

    skipped = 0

    def print_progress() -> None:
        print(
            f"Progress: {len(completed)}/{total} complete, "
            f"{len(running)} running, {failed} failed, {skipped} skipped"
        )

    print_progress()
    while pending or running:
        while pending and len(running) < max_parallel and not (fail_fast and failed):
            job = pending.pop(0)
            env = os.environ.copy()
            env.update(job.env_updates)
            stdout_file = job.stdout_log_path.open("w", encoding="utf-8")
            stderr_file = job.stderr_log_path.open("w", encoding="utf-8")
            job.metadata["start_time"] = datetime.now().isoformat()
            start_tick = time.perf_counter()
            process = subprocess.Popen(
                job.command,
                stdout=stdout_file,
                stderr=stderr_file,
                cwd=Path.cwd(),
                env=env,
                text=True,
            )
            running.append(
                {
                    "job": job,
                    "process": process,
                    "stdout_file": stdout_file,
                    "stderr_file": stderr_file,
                    "start_tick": start_tick,
                }
            )
        changed = False
        for item in list(running):
            job = item["job"]
            process = item["process"]
            exit_code = process.poll()
            timed_out = False
            if exit_code is None and timeout_seconds is not None:
                if time.perf_counter() - item["start_tick"] > timeout_seconds:
                    process.kill()
                    exit_code = process.wait()
                    timed_out = True
            if exit_code is None:
                continue
            item["stdout_file"].close()
            item["stderr_file"].close()
            job.metadata["end_time"] = datetime.now().isoformat()
            job.metadata["duration_seconds"] = time.perf_counter() - item["start_tick"]
            job.metadata["exit_code"] = int(exit_code)
            if timed_out:
                job.metadata["exception"] = f"timeout after {timeout_seconds}s"
            if job.source_report_path.exists():
                shutil.copy2(job.source_report_path, job.copied_report_path)
            elif exit_code == 0:
                job.metadata["exception"] = f"expected report not found: {job.source_report_path}"
                job.metadata["exit_code"] = 2
                exit_code = 2
            write_json_file(job.metadata_path, job.metadata, allow_overwrite=True)
            running.remove(item)
            completed.append(job)
            if exit_code != 0:
                failed += 1
                print(f"FAILED {job.eval_id}; see {job.stderr_log_path}")
                if fail_fast and pending:
                    skipped_pending = list(pending)
                    pending.clear()
                    for skipped_job in skipped_pending:
                        skipped += 1
                        skipped_job.metadata["exit_code"] = None
                        skipped_job.metadata["skipped"] = True
                        skipped_job.metadata["skip_reason"] = "fail_fast"
                        skipped_job.metadata["end_time"] = datetime.now().isoformat()
                        write_json_file(skipped_job.metadata_path, skipped_job.metadata, allow_overwrite=True)
                        completed.append(skipped_job)
            changed = True
        if changed:
            print_progress()
        if pending or running:
            time.sleep(0.1)
    return completed


def dry_run_jobs(jobs: list[EvalJob]) -> list[EvalJob]:
    for job in jobs:
        job.metadata["dry_run"] = True
        job.metadata["exit_code"] = None
        write_json_file(job.metadata_path, job.metadata, allow_overwrite=True)
    return jobs


def metric_mean(report: dict[str, Any], key: str) -> Any:
    return report.get("metrics", {}).get(key, {}).get("mean")


def rate(report: dict[str, Any], key: str) -> Any:
    return report.get("rates", {}).get(key)


SUMMARY_COLUMNS = [
    "eval_id",
    "label",
    "pressure_profile",
    "model_choice",
    "experiment_path",
    "control_mode",
    "reward_profile",
    "training_profile",
    "mean_reward",
    "mean_episode_length",
    "mean_player_damage",
    "mean_damage_events",
    "death_rate",
    "fall_rate",
    "timeout_rate",
    "damage_free_episode_rate",
    "visible_bullet_hit_rate",
    "mean_heli_kills",
    "enemy_bullets_spawned",
    "time_to_first_damage",
    "longest_damage_free_streak",
    "boost_activations",
    "boost_pressed_frames",
    "frames_grounded",
    "frames_airborne",
    "sum_abs_player_dx",
    "left_edge_camping_rate",
    "right_edge_camping_rate",
    "input_motion_mismatch_rate",
    "exit_code",
    "duration_seconds",
]


def summary_row(job: EvalJob) -> dict[str, Any]:
    report = load_json_if_exists(job.copied_report_path)
    return {
        "eval_id": job.eval_id,
        "label": job.metadata.get("label"),
        "pressure_profile": job.metadata.get("pressure_profile"),
        "model_choice": job.metadata.get("model_choice"),
        "experiment_path": job.metadata.get("experiment_path"),
        "control_mode": report.get("control_mode") or job.metadata.get("control_mode"),
        "reward_profile": report.get("reward_profile") or job.metadata.get("reward_profile"),
        "training_profile": report.get("training_profile") or job.metadata.get("training_profile"),
        "mean_reward": metric_mean(report, "reward"),
        "mean_episode_length": metric_mean(report, "length"),
        "mean_player_damage": metric_mean(report, "player_damage"),
        "mean_damage_events": metric_mean(report, "damage_events"),
        "death_rate": rate(report, "death_rate"),
        "fall_rate": rate(report, "fall_rate"),
        "timeout_rate": rate(report, "timeout_rate"),
        "damage_free_episode_rate": rate(report, "damage_free_episode_rate"),
        "visible_bullet_hit_rate": rate(report, "visible_enemy_bullet_hit_rate_against_player"),
        "mean_heli_kills": metric_mean(report, "heli_kills"),
        "enemy_bullets_spawned": metric_mean(report, "engine_enemy_bullets_spawned"),
        "time_to_first_damage": metric_mean(report, "time_to_first_damage"),
        "longest_damage_free_streak": metric_mean(report, "longest_damage_free_streak"),
        "boost_activations": metric_mean(report, "boost_activations"),
        "boost_pressed_frames": metric_mean(report, "frames_boost_pressed"),
        "frames_grounded": metric_mean(report, "frames_grounded"),
        "frames_airborne": metric_mean(report, "frames_airborne"),
        "sum_abs_player_dx": metric_mean(report, "sum_abs_player_dx"),
        "left_edge_camping_rate": rate(report, "left_edge_camping_rate"),
        "right_edge_camping_rate": rate(report, "right_edge_camping_rate"),
        "input_motion_mismatch_rate": rate(report, "input_motion_mismatch_rate"),
        "exit_code": job.metadata.get("exit_code"),
        "duration_seconds": job.metadata.get("duration_seconds"),
    }


def write_summaries(
    matrix_dir: Path,
    matrix_id: str,
    jobs: list[EvalJob],
    matrix_stats: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    rows = [summary_row(job) for job in jobs]
    matrix_stats = matrix_stats or {}
    write_json_file(
        matrix_dir / "matrix_summary.json",
        {"matrix_id": matrix_id, **matrix_stats, "rows": rows},
        allow_overwrite=True,
    )
    with (matrix_dir / "matrix_summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        f"# Evaluation Matrix {matrix_id}",
        "",
        f"- Started: `{matrix_stats.get('matrix_start_time', 'n/a')}`",
        f"- Ended: `{matrix_stats.get('matrix_end_time', 'n/a')}`",
        f"- Duration seconds: `{matrix_stats.get('matrix_duration_seconds', 'n/a')}`",
        f"- Jobs total/succeeded/failed/skipped: `{matrix_stats.get('job_count', 'n/a')}` / `{matrix_stats.get('succeeded_count', 'n/a')}` / `{matrix_stats.get('failed_count', 'n/a')}` / `{matrix_stats.get('skipped_count', 'n/a')}`",
        "- Command: `command.txt`",
        "- Raw argv: `argv.json`",
        "- Resolved config: `resolved_config.json`",
        "- Note: `command.txt` is reconstructed from argv; original shell quoting is not recoverable.",
        "",
        "Each row maps one model/pressure evaluation to an unambiguous `eval_id`.",
        "",
        "| Eval ID | Label | Model | Pressure | Reward | Length | Damage | Death Rate | Timeout Rate | Report |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        report_path = f"jobs/{row['eval_id']}/eval_report.json"
        lines.append(
            "| {eval_id} | {label} | {model_choice} | {pressure_profile} | {mean_reward} | "
            "{mean_episode_length} | {mean_player_damage} | {death_rate} | {timeout_rate} | {report} |".format(
                **{key: "n/a" if value is None else value for key, value in row.items()},
                report=report_path,
            )
        )
    write_text_file(matrix_dir / "matrix_summary.md", "\n".join(lines) + "\n", allow_overwrite=True)
    return rows


def write_matrix_files(
    *,
    matrix_dir: Path,
    matrix_id: str,
    args: argparse.Namespace,
    entries: list[MatrixEntry],
    pressure_profiles: list[str],
    jobs: list[EvalJob],
) -> None:
    config = {
        "matrix_id": matrix_id,
        "matrix_name": args.matrix_name,
        "created_at": datetime.now().isoformat(),
        "entries": [asdict(entry) | {"experiment": str(entry.experiment)} for entry in entries],
        "pressure_profiles": pressure_profiles,
        "episodes": args.episodes,
        "max_episode_steps": args.max_episode_steps,
        "max_parallel": args.max_parallel,
        "threads_per_job": args.threads_per_job,
        "save_replays": bool(args.save_replays),
        "output_root": str(args.output_root),
        "dry_run": bool(args.dry_run),
        "overrides": {
            "training_profile": args.training_profile,
            "control_mode": args.control_mode,
            "reward_profile": args.reward_profile,
        },
        "timeout_seconds": args.timeout_seconds,
        "fail_fast": bool(args.fail_fast),
    }
    manifest = {
        "matrix_id": matrix_id,
        "jobs": {job.eval_id: job.metadata for job in jobs},
    }
    write_json_file(matrix_dir / "matrix_config.json", config, allow_overwrite=True)
    write_resolved_config(matrix_dir, config)
    write_json_file(matrix_dir / "matrix_manifest.json", manifest, allow_overwrite=True)


def create_bundle(matrix_dir: Path, matrix_id: str) -> Path:
    bundle_path = matrix_dir / f"{matrix_id}_bundle.zip"
    if bundle_path.exists():
        raise FileExistsError(f"Bundle already exists: {bundle_path}")
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(matrix_dir.rglob("*")):
            if path == bundle_path or path.is_dir():
                continue
            zf.write(path, path.relative_to(matrix_dir))
    return bundle_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a cross-evaluation matrix for HA2 experiment models.")
    parser.add_argument("--matrix-name", required=True)
    parser.add_argument("--entry", action="append", type=parse_entry, default=[])
    parser.add_argument("--pressure-profiles", type=split_csv, required=True)
    parser.add_argument("--episodes", type=parse_human_count, default=20)
    parser.add_argument("--max-episode-steps", type=parse_human_count, default=3600)
    parser.add_argument("--max-parallel", type=parse_human_count, default=6)
    parser.add_argument("--threads-per-job", type=parse_human_count, default=3)
    parser.add_argument("--save-replays", dest="save_replays", action="store_true", default=False)
    parser.add_argument("--no-save-replays", dest="save_replays", action="store_false")
    parser.add_argument("--output-root", type=Path, default=Path("experiments") / "eval_matrices")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--reward-profile", default=None)
    parser.add_argument("--control-mode", default=None)
    parser.add_argument("--training-profile", default=None)
    parser.add_argument("--timeout-seconds", type=parse_human_count, default=None)
    parser.add_argument("--fail-fast", action="store_true")
    return parser


def main(args_list: list[str] | None = None) -> Path:
    invocation_argv = argv_for_module("scripts.evaluate_matrix", args_list)
    parser = build_parser()
    args = parser.parse_args(args_list)
    validate_entries(args.entry)
    if args.max_parallel < 1:
        raise SystemExit("--max-parallel must be >= 1")
    if args.threads_per_job < 1:
        raise SystemExit("--threads-per-job must be >= 1")
    if not args.pressure_profiles:
        raise SystemExit("--pressure-profiles must contain at least one profile")

    matrix_start_dt = datetime.now()
    matrix_start_tick = time.perf_counter()
    matrix_id, matrix_dir = unique_matrix_dir(args.output_root, args.matrix_name)
    matrix_dir.mkdir(parents=True, exist_ok=False)
    invocation_metadata = capture_invocation_metadata(
        "scripts.evaluate_matrix",
        invocation_argv,
        Path.cwd(),
        repo_root=Path(__file__).resolve().parents[1],
    )
    write_invocation_files(matrix_dir, invocation_metadata)
    overrides = {
        "training_profile": args.training_profile,
        "control_mode": args.control_mode,
        "reward_profile": args.reward_profile,
    }
    jobs = build_jobs(
        entries=args.entry,
        pressure_profiles=args.pressure_profiles,
        matrix_id=matrix_id,
        matrix_dir=matrix_dir,
        episodes=args.episodes,
        max_episode_steps=args.max_episode_steps,
        save_replays=args.save_replays,
        threads_per_job=args.threads_per_job,
        overrides=overrides,
        timeout_seconds=args.timeout_seconds,
    )
    prepare_output_tree(matrix_dir, jobs)
    write_matrix_files(
        matrix_dir=matrix_dir,
        matrix_id=matrix_id,
        args=args,
        entries=args.entry,
        pressure_profiles=args.pressure_profiles,
        jobs=jobs,
    )

    print(f"Matrix: {matrix_id}")
    print(f"Total evals: {len(jobs)}")
    print(f"Running with max_parallel={args.max_parallel}, threads_per_job={args.threads_per_job}")
    if args.dry_run:
        completed = dry_run_jobs(jobs)
        print("Dry run: no evaluation subprocesses launched.")
    else:
        completed = run_jobs(
            jobs,
            max_parallel=args.max_parallel,
            timeout_seconds=args.timeout_seconds,
            fail_fast=args.fail_fast,
        )
    write_matrix_files(
        matrix_dir=matrix_dir,
        matrix_id=matrix_id,
        args=args,
        entries=args.entry,
        pressure_profiles=args.pressure_profiles,
        jobs=completed,
    )
    matrix_end_dt = datetime.now()
    matrix_stats = {
        "matrix_start_time": matrix_start_dt.isoformat(timespec="seconds"),
        "matrix_end_time": matrix_end_dt.isoformat(timespec="seconds"),
        "matrix_duration_seconds": time.perf_counter() - matrix_start_tick,
        "job_count": len(completed),
        "succeeded_count": sum(1 for job in completed if job.metadata.get("exit_code") == 0),
        "failed_count": sum(1 for job in completed if job.metadata.get("exit_code") not in (0, None)),
        "skipped_count": sum(1 for job in completed if job.metadata.get("skipped")),
        "dry_run_count": sum(1 for job in completed if job.metadata.get("dry_run")),
    }
    write_summaries(matrix_dir, matrix_id, completed, matrix_stats=matrix_stats)
    bundle_path = create_bundle(matrix_dir, matrix_id)
    print(f"Bundle: {bundle_path}")
    return matrix_dir


if __name__ == "__main__":
    main()
