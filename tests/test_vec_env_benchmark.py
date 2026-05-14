from __future__ import annotations

import json
import subprocess
import sys

import pytest

from scripts import benchmark_vec_envs
from scripts import train_parkour


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


def test_benchmark_script_writes_dummy_reports(tmp_path):
    out_dir = tmp_path / "reports"
    experiments_root = tmp_path / "experiments"
    benchmark_vec_envs.main(
        [
            "--total-timesteps",
            "64",
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
    assert report["results"][0]["success"] is True
    assert "wall_clock_seconds" in report["results"][0]


def test_benchmark_subproc_smoke_via_module(tmp_path):
    out_dir = tmp_path / "reports"
    experiments_root = tmp_path / "experiments"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.benchmark_vec_envs",
            "--total-timesteps",
            "64",
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
