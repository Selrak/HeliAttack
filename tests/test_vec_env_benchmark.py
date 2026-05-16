from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import benchmark_vec_envs
from scripts import train_parkour

# Optimization: reduce default steps for smoke tests to speed up the suite.
SMOKE_STEPS = "16"

def test_make_vec_env_dummy_works():
    pytest.importorskip("stable_baselines3")
    _PPO, _CheckpointCallback, _EvalCallback, Monitor, DummyVecEnv, SubprocVecEnv = train_parkour._load_sb3()
    env = train_parkour.make_vec_env(
        vec_env="dummy",
        n_envs=1,
        seed=0,
        training_profile="combat_v1",
        max_episode_steps=20,
        monitor_cls=Monitor,
        dummy_vec_env_cls=DummyVecEnv,
        subproc_vec_env_cls=SubprocVecEnv,
    )
    try:
        obs = env.reset()
        assert obs.shape[0] == 1
        obs, _rewards, _dones, _infos = env.step([[1, 0, 0, 0, 0, 0]])
        assert obs.shape[0] == 1
    finally:
        env.close()


def test_invalid_vec_env_fails_clearly():
    pytest.importorskip("stable_baselines3")
    _PPO, _CheckpointCallback, _EvalCallback, Monitor, DummyVecEnv, SubprocVecEnv = train_parkour._load_sb3()
    with pytest.raises(ValueError, match="Unknown vec_env"):
        train_parkour.make_vec_env(
            vec_env="invalid",
            n_envs=1,
            seed=0,
            training_profile="combat_v1",
            max_episode_steps=20,
            monitor_cls=Monitor,
            dummy_vec_env_cls=DummyVecEnv,
            subproc_vec_env_cls=SubprocVecEnv,
        )


def test_benchmark_script_writes_dummy_reports(tmp_path, monkeypatch):
    def fake_train_main(train_args):
        # Handle new timestamped directory naming in mock
        exp_root = Path(train_args[train_args.index("--experiments-root") + 1])
        name = "mock_exp"
        if "--experiment-name" in train_args:
            name = train_args[train_args.index("--experiment-name") + 1]
        exp_path = exp_root / name
        exp_path.mkdir(parents=True, exist_ok=True)
        print("| total_timesteps | 16 |")
        print("| fps | 123 |")
        return SimpleNamespace(path=exp_path)

    monkeypatch.setattr(benchmark_vec_envs.train_parkour, "main", fake_train_main)
    out_dir = tmp_path / "reports"
    experiments_root = tmp_path / "experiments"
    benchmark_vec_envs.main(
        [
            "--mode",
            "train-only",
            "--total-timesteps",
            SMOKE_STEPS,
            "--repeats",
            "1",
            "--vec-envs",
            "dummy",
            "--n-envs",
            "1",
            "--wandb",
            "off",
            "--device",
            "cpu",
            "--out-dir",
            str(out_dir),
            "--experiments-root",
            str(experiments_root),
        ]
    )
    json_reports = list(out_dir.glob("*_vec_env_benchmark.json"))
    md_reports = list(out_dir.glob("*_vec_env_benchmark.md"))
    assert len(json_reports) == 1
    assert len(md_reports) == 1
    report = json.loads(json_reports[0].read_text(encoding="utf-8"))
    assert report["results"][0]["vec_env"] == "dummy"
    assert report["results"][0]["mode"] == "train-only"
    assert report["results"][0]["success"] is True


def test_train_parkour_train_eval_off_tiny_dummy_run(tmp_path):
    pytest.importorskip("stable_baselines3")
    layout = train_parkour.main(
        [
            "--total-timesteps",
            SMOKE_STEPS,
            "--n-envs",
            "1",
            "--vec-env",
            "dummy",
            "--train-eval",
            "off",
            "--wandb",
            "off",
            "--device",
            "cpu",
            "--experiments-root",
            str(tmp_path / "experiments"),
        ]
    )
    config = json.loads((layout.path / "config.json").read_text(encoding="utf-8"))
    assert config["train_eval"] == "off"
    # Cleanup to avoid pollution
    shutil.rmtree(layout.path)


@pytest.mark.slow
def test_train_parkour_subproc_eval_same_tiny_run(tmp_path):
    pytest.importorskip("stable_baselines3")
    out_root = tmp_path / "experiments"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.train_parkour",
            "--total-timesteps",
            SMOKE_STEPS,
            "--n-envs",
            "2",
            "--vec-env",
            "subproc",
            "--eval-vec-env",
            "same",
            "--train-eval",
            "on",
            "--train-eval-episodes",
            "1",
            "--eval-freq",
            "16",
            "--wandb",
            "off",
            "--device",
            "cpu",
            "--experiments-root",
            str(out_root),
        ],
        cwd=".",
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Training and eval env are not of the same type" not in completed.stderr


def test_invalid_benchmark_mode_or_eval_vec_env_fails_clearly():
    with pytest.raises(SystemExit):
        benchmark_vec_envs.main(["--mode", "invalid"])
    with pytest.raises(SystemExit):
        benchmark_vec_envs.main(["--eval-vec-env", "invalid"])


@pytest.mark.slow
def test_benchmark_subproc_smoke_via_module(tmp_path):
    out_dir = tmp_path / "reports"
    experiments_root = tmp_path / "experiments"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.benchmark_vec_envs",
            "--total-timesteps",
            SMOKE_STEPS,
            "--repeats",
            "1",
            "--vec-envs",
            "subproc",
            "--n-envs",
            "2",
            "--wandb",
            "off",
            "--device",
            "cpu",
            "--out-dir",
            str(out_dir),
            "--experiments-root",
            str(experiments_root),
        ],
        cwd=".",
        check=True,
        capture_output=True,
        text=True,
    )
    assert "subproc" in completed.stdout
    json_reports = list(out_dir.glob("*_vec_env_benchmark.json"))
    assert len(json_reports) == 1
    report = json.loads(json_reports[0].read_text(encoding="utf-8"))
    assert report["results"][0]["vec_env"] == "subproc"
    assert report["results"][0]["n_envs"] == 2
    assert report["results"][0]["success"] is True
