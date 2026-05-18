from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import os
import re
import subprocess
from pathlib import Path


TIMESTAMP_FORMAT = "%Y%m%d_%H%M"
WATCH_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
EXPERIMENT_PREFIX = "ha2"


def compact_timesteps(total_timesteps: int) -> str:
    total_timesteps = int(total_timesteps)
    if total_timesteps >= 1_000_000 and total_timesteps % 1_000_000 == 0:
        return f"{total_timesteps // 1_000_000}m"
    if total_timesteps >= 1_000 and total_timesteps % 1_000 == 0:
        return f"{total_timesteps // 1_000}k"
    return str(total_timesteps)


def slugify_training_profile(training_profile: str) -> str:
    return str(training_profile).replace("_", "-")


def _now_string(now: datetime | None = None, fmt: str = TIMESTAMP_FORMAT) -> str:
    return (now or datetime.now()).strftime(fmt)


def _safe_root_name(experiments_root: Path) -> str:
    return experiments_root.resolve().name


def default_experiment_name(
    experiments_root: Path,
    training_profile: str,
    total_timesteps: int,
    now: datetime | None = None,
) -> str:
    experiments_root = Path(experiments_root)
    experiments_root.mkdir(parents=True, exist_ok=True)
    highest = 0
    pattern = re.compile(rf"^{re.escape(EXPERIMENT_PREFIX)}_(\d{{6}})_")
    for child in experiments_root.iterdir():
        if not child.is_dir():
            continue
        match = pattern.match(child.name)
        if match:
            highest = max(highest, int(match.group(1)))
    number = highest + 1
    timestamp = _now_string(now)
    profile = slugify_training_profile(training_profile)
    timesteps = compact_timesteps(total_timesteps)
    return f"{EXPERIMENT_PREFIX}_{number:06d}_{timestamp}_{profile}_{timesteps}"


@dataclass(frozen=True)
class ExperimentLayout:
    root: Path
    path: Path

    @property
    def models_dir(self) -> Path:
        return self.path / "models"

    @property
    def checkpoints_dir(self) -> Path:
        return self.models_dir / "checkpoints"

    @property
    def reports_dir(self) -> Path:
        return self.path / "reports"

    @property
    def replays_dir(self) -> Path:
        return self.path / "replays"

    @property
    def recordings_dir(self) -> Path:
        return self.path / "recordings"

    @property
    def tensorboard_dir(self) -> Path:
        return self.path / "tensorboard"

    @property
    def config_path(self) -> Path:
        return self.path / "config.json"

    @property
    def summary_path(self) -> Path:
        return self.path / "summary.md"

    @property
    def git_info_path(self) -> Path:
        return self.path / "git_info.txt"

    def ensure_directories(self) -> None:
        for directory in (
            self.path,
            self.models_dir,
            self.checkpoints_dir,
            self.reports_dir,
            self.replays_dir,
            self.recordings_dir,
            self.tensorboard_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    def model_path(self, model_choice: str) -> Path:
        if model_choice == "latest":
            return self.models_dir / "latest.zip"
        if model_choice == "best":
            best = self.models_dir / "best.zip"
            if best.exists():
                return best
            legacy_best = self.models_dir / "best_model.zip"
            if legacy_best.exists():
                return legacy_best
            return best
        raise ValueError(f"Unsupported model choice: {model_choice}")

    def report_path(self, model_choice: str, report_name: str | None = None) -> Path:
        if report_name is not None:
            return self.reports_dir / report_name
        if model_choice in {"best", "latest"}:
            return self.reports_dir / f"eval_{model_choice}.json"
        return self.reports_dir / "eval.json"

    def replay_path(
        self,
        model_choice: str,
        episode: int,
        replay_prefix: str | None = None,
    ) -> Path:
        if replay_prefix is None:
            replay_prefix = {
                "best": "best_eval",
                "latest": "latest_eval",
            }.get(model_choice, "eval")
        return self.replays_dir / f"{replay_prefix}_ep{episode}.jsonl"

    def watch_replay_path(self, model_choice: str, timestamp: str | None = None) -> Path:
        timestamp = timestamp or _now_string(fmt=WATCH_TIMESTAMP_FORMAT)
        return self.replays_dir / f"watch_{model_choice}_{timestamp}.jsonl"

    def watch_gif_path(self, model_choice: str, timestamp: str | None = None) -> Path:
        timestamp = timestamp or _now_string(fmt=WATCH_TIMESTAMP_FORMAT)
        return self.recordings_dir / f"watch_{model_choice}_{timestamp}.gif"


def create_experiment_layout(
    *,
    experiments_root: Path,
    experiment_dir: Path | None = None,
    experiment_name: str | None = None,
    training_profile: str,
    total_timesteps: int,
    now: datetime | None = None,
) -> ExperimentLayout:
    experiments_root = Path(experiments_root)
    if experiment_dir is not None:
        path = Path(experiment_dir)
        if path.exists():
            raise FileExistsError(f"Experiment directory already exists: {path}")
        path.mkdir(parents=True, exist_ok=False)
        layout = ExperimentLayout(experiments_root, path)
        layout.ensure_directories()
        return layout

    experiments_root.mkdir(parents=True, exist_ok=True)
    if experiment_name is None:
        experiment_name = default_experiment_name(
            experiments_root,
            training_profile=training_profile,
            total_timesteps=total_timesteps,
            now=now,
        )
    path = experiments_root / experiment_name
    if path.exists():
        raise FileExistsError(f"Experiment directory already exists: {path}")
    path.mkdir(parents=True, exist_ok=False)

    # Update latest_experiment symlink (or copy on Windows if symlink fails)
    latest_link = experiments_root / "latest_experiment"
    try:
        if latest_link.exists():
            if latest_link.is_symlink():
                latest_link.unlink()
            elif latest_link.is_dir():
                # If it's a real directory for some reason, don't delete it
                latest_link = None

        if latest_link:
            # On Windows, symlinks might require admin privileges.
            # We try to create a directory junction or a symlink.
            # If it fails, we just skip it or log a warning.
            try:
                os.symlink(path.relative_to(experiments_root), latest_link, target_is_directory=True)
            except (OSError, NotImplementedError):
                # Fallback: create a small text file with the path if symlink fails
                (experiments_root / "latest_experiment.txt").write_text(str(path), encoding="utf-8")
    except Exception as e:
        print(f"Warning: Could not update latest_experiment link: {e}")

    layout = ExperimentLayout(experiments_root, path)
    layout.ensure_directories()
    return layout


def write_json_file(path: Path, data, *, allow_overwrite: bool = False) -> None:
    path = Path(path)
    if path.exists() and not allow_overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text_file(path: Path, text: str, *, allow_overwrite: bool = False) -> None:
    path = Path(path)
    if path.exists() and not allow_overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def collect_git_info(repo_root: Path) -> dict[str, str]:
    repo_root = Path(repo_root)
    safe_root = str(repo_root.resolve())
    commands = [
        ("top_level", ["git", "-c", f"safe.directory={safe_root}", "rev-parse", "--show-toplevel"]),
        ("head", ["git", "-c", f"safe.directory={safe_root}", "rev-parse", "HEAD"]),
        ("status", ["git", "-c", f"safe.directory={safe_root}", "status", "--short"]),
        ("diff_stat", ["git", "-c", f"safe.directory={safe_root}", "diff", "--stat"]),
    ]
    info: dict[str, str] = {
        "repo_root": str(repo_root.resolve()),
        "available": "false",
    }
    for key, command in commands:
        try:
            completed = subprocess.run(
                command,
                cwd=repo_root,
                check=True,
                capture_output=True,
                text=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            info["note"] = f"git unavailable: {exc}"
            return info
        info[key] = completed.stdout.strip()
    info["available"] = "true"
    return info


def git_info_text(repo_root: Path) -> str:
    info = collect_git_info(repo_root)
    if info.get("available") != "true":
        return f"git unavailable\n{info.get('note', '')}\n"
    return (
        f"repo_root: {info['repo_root']}\n"
        f"top_level: {info['top_level']}\n"
        f"head: {info['head']}\n"
        f"status:\n{info['status'] or '  (clean)'}\n"
        f"diff_stat:\n{info['diff_stat'] or '  (clean)'}\n"
    )


def resolve_model_path(
    *,
    model: Path | None,
    experiment: Path | None,
    model_choice: str,
) -> Path:
    if model is not None:
        return Path(model)
    if model_choice == "path":
        raise ValueError("--model-choice path requires --model")
    if experiment is None:
        best = Path("models/best.zip")
        latest = Path("models/latest.zip")
        if model_choice == "best":
            return best if best.exists() else latest
        if model_choice == "latest":
            return latest
        raise ValueError(f"Unsupported model choice: {model_choice}")
    layout = ExperimentLayout(Path(experiment).parent, Path(experiment))
    return layout.model_path(model_choice)


def resolve_experiment_layout_and_config(
    *,
    experiment: Path | None,
    model: Path | None,
) -> tuple[ExperimentLayout | None, dict[str, object]]:
    layout = None
    config: dict[str, object] = {}
    experiment_path: Path | None = None
    if experiment is not None:
        experiment_path = Path(experiment)
    elif model is not None:
        model_path = Path(model)
        candidate_experiment = model_path.parent.parent
        if model_path.parent.name == "models" and (candidate_experiment / "config.json").exists():
            experiment_path = candidate_experiment

    if experiment_path is None:
        return None, config
    if not experiment_path.exists():
        raise SystemExit(f"Experiment not found: {experiment_path}")

    layout = ExperimentLayout(experiment_path.parent, experiment_path)
    if layout.config_path.exists():
        config = json.loads(layout.config_path.read_text(encoding="utf-8"))
    return layout, config


def resume_lineage(
    *,
    resume_from: Path | None,
    reset_num_timesteps: bool,
    fine_tune_timesteps: int | None,
) -> dict[str, object]:
    lineage: dict[str, object] = {
        "resume_from": str(resume_from) if resume_from is not None else None,
        "parent_model_path": str(resume_from) if resume_from is not None else None,
        "parent_experiment_dir": None,
        "parent_config_path": None,
        "parent_training_profile": None,
        "parent_control_mode": None,
        "parent_reward_profile": None,
        "parent_pressure_profile": None,
        "reset_num_timesteps": bool(reset_num_timesteps),
        "fine_tune_timesteps": int(fine_tune_timesteps) if fine_tune_timesteps is not None else None,
        "parent_config_inferred": False,
    }
    if resume_from is None:
        return lineage

    layout, config = resolve_experiment_layout_and_config(experiment=None, model=resume_from)
    if layout is None:
        return lineage

    lineage.update(
        {
            "parent_experiment_dir": str(layout.path),
            "parent_config_path": str(layout.config_path) if layout.config_path.exists() else None,
            "parent_training_profile": config.get("training_profile"),
            "parent_control_mode": config.get("control_mode"),
            "parent_reward_profile": config.get("reward_profile"),
            "parent_pressure_profile": config.get("pressure_profile"),
            "parent_config_inferred": bool(config),
        }
    )
    return lineage


def unique_timestamped_path(directory: Path, stem: str, suffix: str, timestamp: str | None = None) -> Path:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    timestamp = timestamp or _now_string(fmt=WATCH_TIMESTAMP_FORMAT)
    candidate = directory / f"{stem}_{timestamp}{suffix}"
    if not candidate.exists():
        return candidate
    index = 2
    while True:
        candidate = directory / f"{stem}_{timestamp}_{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1
