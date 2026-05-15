from __future__ import annotations

import os
import json
import shutil
import zipfile
import sys
from pathlib import Path
import pytest
from scripts.run_experiment_pair import get_auto_threads, create_thread_env

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

def test_parallel_staggered_durations():
    from scripts import run_experiment_pair
    
    args = [
        "--mode", "parallel",
        "--profile-a", "legacy",
        "--profile-b", "legacy",
        "--total-timesteps", "10",
        "--n-envs", "1",
        "--vec-env", "dummy",
        "--wandb", "off",
        "--train-eval", "off",
        "--eval-episodes", "1",
        "--stagger-seconds", "2",
        "--timing-profile", "off"
    ]
    
    old_argv = sys.argv
    sys.argv = ["run_experiment_pair.py"] + args
    
    # Run it in the real repo root to get the python path right
    try:
        run_experiment_pair.main()
        
        # Sort to find the latest
        pairs = sorted(list(Path("experiments").glob("pair_*")), key=lambda p: p.stat().st_mtime)
        assert len(pairs) >= 1
        latest_pair = pairs[-1]
        
        with open(latest_pair / "pair_summary.json", "r") as f:
            summary = json.load(f)
            
        job_a = summary["parallel"]["job_a"]
        job_b = summary["parallel"]["job_b"]
        total = summary["parallel"]["total_parallel_duration"]
        
        # 10 timesteps on legacy profile should take < 1.0 seconds to run.
        # But stagger is 2 seconds. Job B starts after 2s.
        # So Job B's own duration must not include the 2s wait!
        assert job_b["duration_seconds"] < 2.0, f"Job B duration {job_b['duration_seconds']} should not include stagger"
        assert total >= 2.0, f"Total duration {total} must include stagger"
        
        # Cleanup
        shutil.rmtree(latest_pair)
        
    finally:
        sys.argv = old_argv

def test_run_experiment_outputs_and_bundle(tmp_path):
    from scripts import run_experiment
    
    exp_dir = Path("experiments") / "test_bundle_smoke"
    if exp_dir.exists():
        shutil.rmtree(exp_dir)
        
    args = [
        "--total-timesteps", "100",
        "--n-envs", "1",
        "--wandb", "off",
        "--train-eval", "off",
        "--eval-episodes", "1",
        "--timing-profile", "on",
        "--net-arch", "32,32",
        "--experiment-name", "test_bundle_smoke"
    ]
    
    old_argv = sys.argv
    sys.argv = ["run_experiment.py"] + args
    
    # Run it
    try:
        run_experiment.main()
    finally:
        sys.argv = old_argv
    
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
    
    # Cleanup
    shutil.rmtree(exp_dir)
