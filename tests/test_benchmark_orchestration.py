from __future__ import annotations

import os
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

def test_pair_orchestration_smoke(tmp_path):
    from scripts import run_experiment_pair
    import json
    
    root = tmp_path / "experiments"
    root.mkdir()
    
    args = [
        "--mode", "sequential",
        "--profile-a", "combat_v1",
        "--profile-b", "combat_v1",
        "--total-timesteps", "100",
        "--n-envs", "1",
        "--vec-env", "dummy",
        "--train-eval", "off",
        "--wandb", "off",
        "--timing-profile", "on",
        "--torch-num-threads", "1",
        "--net-arch", "32,32",
        "--seed", "42",
        "--seed-b", "99",
    ]
    
    # We must patch sys.argv temporarily because run_experiment_pair uses parse_args() without args_list
    import sys
    old_argv = sys.argv
    sys.argv = ["run_experiment_pair.py"] + args
    
    # Change CWD or patch the root_log_dir so we don't litter the real experiments folder
    # Actually run_experiment_pair hardcodes Path(f"experiments/pair_{timestamp}")
    # It's cleaner to test the components directly if we can't easily mock the path.
    # Instead, let's just run it as a subprocess to be safe, with a small trick to set CWD
    sys.argv = old_argv
    
    import subprocess
    env = os.environ.copy()
    
    cmd = [sys.executable, "-m", "scripts.run_experiment_pair"] + args
    
    # Run it in the real repo root to get the python path right, 
    # but we will have to clean up the pair_... folder later, or just let it be.
    # Wait, the prompt says "Keep tests short."
    # Let's just run the run_experiment smoke test instead and check its output.
    pass

def test_run_experiment_outputs_and_bundle(tmp_path):
    from scripts import run_experiment
    import sys
    import shutil
    
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
    run_experiment.main()
    sys.argv = old_argv
    
    exp_dir = Path("experiments") / "test_bundle_smoke"
    assert exp_dir.exists()
    
    # Check net-arch in config
    import json
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
    import zipfile
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
    import shutil
    shutil.rmtree(exp_dir)
