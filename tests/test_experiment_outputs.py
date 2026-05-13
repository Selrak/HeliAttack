from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path

import pytest

from scripts.experiment_utils import (
    ExperimentLayout,
    create_experiment_layout,
    git_info_text,
    resolve_model_path,
    write_json_file,
)


def test_default_experiment_name_increments_and_creates_layout(tmp_path):
    root = tmp_path / "experiments"
    root.mkdir()
    fixed = datetime(2026, 5, 5, 15, 30)
    (root / "ha2_000001_20260505_1530_combat-v1_100k").mkdir()
    (root / "ha2_000002_20260505_1530_combat-v1_100k").mkdir()

    layout = create_experiment_layout(
        experiments_root=root,
        training_profile="combat_v1",
        total_timesteps=100_000,
        now=fixed,
    )

    assert layout.path.name == "ha2_000003_20260505_1530_combat-v1_100k"
    assert layout.models_dir.exists()
    assert layout.checkpoints_dir.exists()
    assert layout.reports_dir.exists()
    assert layout.replays_dir.exists()
    assert layout.recordings_dir.exists()
    assert layout.tensorboard_dir.exists()


def test_explicit_existing_experiment_dir_fails(tmp_path):
    existing = tmp_path / "existing_experiment"
    existing.mkdir()

    with pytest.raises(FileExistsError):
        create_experiment_layout(
            experiments_root=tmp_path / "experiments",
            experiment_dir=existing,
            training_profile="combat_v1",
            total_timesteps=1_000,
        )


def test_config_and_git_info_writing(tmp_path):
    config_path = tmp_path / "config.json"
    write_json_file(config_path, {"seed": 7, "profile": "combat_v1"})
    assert json.loads(config_path.read_text(encoding="utf-8")) == {
        "profile": "combat_v1",
        "seed": 7,
    }

    git_text = git_info_text(Path.cwd())
    assert "repo_root:" in git_text or "git unavailable" in git_text


def test_layout_paths_and_model_resolution(tmp_path):
    layout = ExperimentLayout(tmp_path, tmp_path / "exp")
    layout.ensure_directories()

    latest = layout.models_dir / "latest.zip"
    best_model = layout.models_dir / "best_model.zip"
    latest.write_text("latest", encoding="utf-8")
    best_model.write_text("best", encoding="utf-8")

    assert layout.report_path("best") == layout.reports_dir / "eval_best.json"
    assert layout.report_path("latest") == layout.reports_dir / "eval_latest.json"
    assert layout.replay_path("best", 0) == layout.replays_dir / "best_eval_ep0.jsonl"
    assert layout.replay_path("latest", 1) == layout.replays_dir / "latest_eval_ep1.jsonl"
    assert layout.watch_replay_path("latest", "20260505_153000").name == "watch_latest_20260505_153000.jsonl"
    assert layout.watch_gif_path("best", "20260505_153000").name == "watch_best_20260505_153000.gif"

    assert resolve_model_path(model=None, experiment=layout.path, model_choice="latest") == latest
    assert resolve_model_path(model=None, experiment=layout.path, model_choice="best") == best_model

    explicit = tmp_path / "ad_hoc.zip"
    assert resolve_model_path(model=explicit, experiment=layout.path, model_choice="path") == explicit

    with pytest.raises(ValueError, match="requires --model"):
        resolve_model_path(model=None, experiment=None, model_choice="path")

