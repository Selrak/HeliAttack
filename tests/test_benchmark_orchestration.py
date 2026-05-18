from __future__ import annotations

import os
import json
import shutil
import zipfile
import sys
import time
from pathlib import Path
import pytest
from scripts.run_experiment_pair import get_auto_threads, create_thread_env


def _rmtree_with_retries(path: Path, retries: int = 20, delay: float = 0.05) -> None:
    for attempt in range(retries):
        try:
            shutil.rmtree(path)
            return
        except PermissionError:
            if attempt == retries - 1:
                raise
            time.sleep(delay)

def test_auto_threads():
    # Should be at least 2
    threads = get_auto_threads()
    assert threads >= 2
    assert isinstance(threads, int)

def test_create_thread_env():
    env = create_thread_env(4)
    assert env["OMP_NUM_THREADS"] == "4"
    assert env["MKL_NUM_THREADS"] == "4"
    assert env["NUMEXPR_NUM_THREADS"] == "4"
    assert env["HA2_TORCH_NUM_THREADS"] == "4"

def test_parallel_staggered_durations(tmp_path):
    from scripts import run_experiment_pair

    class FakeStdout:
        def __init__(self, lines: list[str]):
            self._lines = [line + "\n" for line in lines]
            self._index = 0

        def readline(self):
            if self._index >= len(self._lines):
                return ""
            line = self._lines[self._index]
            self._index += 1
            return line

        def close(self):
            return None

    class FakeProcess:
        def __init__(self, command, *_args, **_kwargs):
            self.command = command
            self.start = time.perf_counter()
            self.duration = 1.25 if command[-1].endswith("_a") else 1.35
            exp_name = command[command.index("--experiment-name") + 1]
            self.stdout = FakeStdout(
                [
                    "phase start",
                    f"Experiment directory: experiments/{exp_name}",
                ]
            )

        def poll(self):
            if time.perf_counter() - self.start >= self.duration:
                return 0
            return None

        def wait(self):
            while self.poll() is None:
                time.sleep(0.01)
            return 0

    class FakeLive:
        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def update(self, *_args, **_kwargs):
            return None

    class FakeLayout:
        def __init__(self, *_args, **_kwargs):
            pass

        def split_column(self, *_args, **_kwargs):
            return None

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(run_experiment_pair.subprocess, "Popen", FakeProcess)
    monkeypatch.setitem(sys.modules, "rich.live", type("RichLive", (), {"Live": FakeLive}))
    monkeypatch.setitem(sys.modules, "rich.layout", type("RichLayout", (), {"Layout": FakeLayout}))
    monkeypatch.setitem(sys.modules, "rich.panel", type("RichPanel", (), {"Panel": lambda *args, **kwargs: None}))
    monkeypatch.setitem(sys.modules, "rich.text", type("RichText", (), {"Text": lambda value: value}))

    args = [
        "run_experiment_pair.py",
        "--mode", "parallel",
        "--profile-a", "combat_v1",
        "--profile-b", "combat_v1",
        "--total-timesteps", "10",
        "--n-envs", "1",
        "--vec-env", "dummy",
        "--wandb", "off",
        "--train-eval", "off",
        "--eval-episodes", "1",
        "--stagger-seconds", "1",
        "--timing-profile", "off",
    ]
    old_argv = sys.argv
    sys.argv = args
    try:
        run_experiment_pair.main()
        pairs = sorted(Path("experiments").glob("pair_*"), key=lambda p: p.stat().st_mtime)
        latest_pair = pairs[-1]
        summary = json.loads((latest_pair / "pair_summary.json").read_text(encoding="utf-8"))
        job_b = summary["parallel"]["job_b"]
        total = summary["parallel"]["total_parallel_duration"]
        assert job_b["duration_seconds"] < total - 0.5
        assert total >= 1.0
        _rmtree_with_retries(latest_pair)
    finally:
        sys.argv = old_argv
        monkeypatch.undo()

def test_run_experiment_outputs_and_bundle(tmp_path, monkeypatch):
    from scripts import run_experiment

    monkeypatch.chdir(tmp_path)
    exp_dir = Path("experiments") / "test_bundle_smoke"

    def fake_train_main(_args_list):
        from scripts.experiment_utils import ExperimentLayout, write_json_file, write_text_file

        layout = ExperimentLayout(Path("experiments"), exp_dir)
        layout.ensure_directories()
        write_json_file(
            layout.config_path,
            {
                "net_arch": "32,32",
                "training_profile": "combat_v1",
                "control_mode": "full",
                "reward_profile": "combat_default",
                "pressure_profile": "normal",
            },
        )
        write_text_file(layout.git_info_path, "git unavailable\n", allow_overwrite=True)
        write_text_file((layout.models_dir / "latest.zip"), "model", allow_overwrite=True)
        write_text_file(layout.summary_path, "# Summary\n", allow_overwrite=True)
        timing_dir = layout.reports_dir / "timing"
        timing_dir.mkdir(parents=True, exist_ok=True)
        write_text_file(
            timing_dir / "train_timing.json",
            json.dumps(
                {
                    "rollout_count": 1,
                    "train_update_count": 1,
                    "other_or_unclassified_training_seconds": 0.0,
                }
            ),
            allow_overwrite=True,
        )
        write_text_file(timing_dir / "train_timing.md", "# Timing\n", allow_overwrite=True)
        return layout

    def fake_eval_main(args_list):
        report_name = "eval_latest.json"
        if "--report-name" in args_list:
            report_name = args_list[args_list.index("--report-name") + 1]
        report_path = exp_dir / "reports" / report_name
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "training_profile": "combat_v1",
            "control_mode": "full",
            "reward_profile": "combat_default",
            "pressure_profile": "normal",
            "net_arch": "32,32",
            "metrics": {
                "reward": {"mean": 0.0},
                "length": {"mean": 1.0},
                "heli_kills": {"mean": 0.0},
                "player_damage": {"mean": 0.0},
                "final_score": {"mean": 0.0},
                "frames_grounded": {"mean": 1.0},
                "frames_airborne": {"mean": 0.0},
                "frames_pressing_left": {"mean": 0.0},
                "frames_pressing_right": {"mean": 0.0},
                "frames_actual_moving_left": {"mean": 0.0},
                "frames_actual_moving_right": {"mean": 0.0},
                "frames_boost_pressed": {"mean": 0.0},
                "frames_boost_ready": {"mean": 0.0},
                "boost_activations": {"mean": 0.0},
                "frames_jump_pressed": {"mean": 0.0},
                "visible_enemy_bullets_seen_unique": {"mean": 0.0},
                "visible_enemy_bullets_max": {"mean": 0.0},
                "visible_enemy_bullets_over_top10_frames": {"mean": 0.0},
                "damage_events": {"mean": 0.0},
                "time_to_first_damage": {"mean": None},
                "longest_damage_free_streak": {"mean": 1.0},
            },
            "rates": {
                "hit_rate": 0.0,
                "death_rate": 0.0,
                "timeout_rate": 0.0,
                "visible_enemy_bullet_hit_rate_against_player": 0.0,
                "damage_free_episode_rate": 1.0,
                "input_motion_mismatch_rate": 0.0,
                "left_edge_camping_rate": 0.0,
                "right_edge_camping_rate": 0.0,
            },
        }
        report_path.write_text(json.dumps(report), encoding="utf-8")

    monkeypatch.setattr(run_experiment.train_parkour, "main", fake_train_main)
    monkeypatch.setattr(run_experiment.evaluate_model, "main", fake_eval_main)

    run_experiment.main(
        [
            "--total-timesteps", "100",
            "--n-envs", "1",
            "--wandb", "off",
            "--train-eval", "off",
            "--eval-episodes", "1",
            "--timing-profile", "on",
            "--net-arch", "32,32",
            "--experiment-name", "test_bundle_smoke",
        ]
    )

    assert exp_dir.exists()
    
    # Check net-arch in config
    with open(exp_dir / "config.json") as f:
        config = json.load(f)
    assert config["net_arch"] == "32,32"
    
    # Check net-arch and movement diagnostics in eval report
    with open(exp_dir / "reports" / "eval_latest.json") as f:
        eval_report = json.load(f)
    assert eval_report["net_arch"] == "32,32"
    assert "frames_grounded" in eval_report["metrics"]
    assert eval_report["metrics"]["frames_grounded"]["mean"] is not None
    assert isinstance(eval_report["metrics"]["frames_grounded"]["mean"], float)
    
    # Check diagnostic bundle
    bundle_path = exp_dir / "test_bundle_smoke_diagnostic_bundle.zip"
    assert bundle_path.exists()
    
    with zipfile.ZipFile(bundle_path, "r") as zf:
        namelist = zf.namelist()
        assert "train_timing.json" in namelist
        assert "train_timing.md" in namelist
        assert "orchestration_timing.json" in namelist
        
    # Check that PPO runtime timing constraints hold
    with open(exp_dir / "reports" / "timing" / "train_timing.json") as f:
        timing_report = json.load(f)
        
    assert timing_report["rollout_count"] > 0
    assert timing_report["train_update_count"] > 0
    assert timing_report["other_or_unclassified_training_seconds"] >= 0.0
    # In PPO, we do an update per rollout
    assert timing_report["train_update_count"] == timing_report["rollout_count"]
    
    _rmtree_with_retries(exp_dir)
