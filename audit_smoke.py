from pathlib import Path
import json
import zipfile
import sys

def main():
    root = Path("experiments")
    
    # Trouver le dernier pair_ run
    pairs = sorted([d for d in root.glob("pair_*") if d.is_dir()], key=os.path.getmtime)
    if not pairs:
        print("Aucun run pair_ trouvé.")
        sys.exit(1)
    
    pair_dir = pairs[-1]
    summary_path = pair_dir / "pair_summary.json"
    
    with open(summary_path, "r") as f:
        summary = json.load(f)
        
    job_a = summary["parallel"]["job_a"]
    job_b = summary["parallel"]["job_b"]
    
    assert job_a["timing_report_path"] is not None, "timing_report_path is null in pair_summary.json"
    assert job_b["timing_report_path"] is not None, "timing_report_path is null in pair_summary.json"
    
    for job in [job_a, job_b]:
        exp_path = Path(job["experiment_path"])
        
        # Check config.json
        with open(exp_path / "config.json") as f:
            config = json.load(f)
        assert config["net_arch"] == "128,128", f"net_arch is {config.get('net_arch')}"
        assert config.get("trainable_parameters") is not None and config["trainable_parameters"] > 0
        
        # Check timing json
        with open(exp_path / "reports" / "timing" / "train_timing.json") as f:
            timing = json.load(f)
        assert timing["train_update_count"] == timing["rollout_count"], "train_update_count != rollout_count"
        assert timing["other_or_unclassified_training_seconds"] >= 0, "other_or_unclassified < 0"
        
        # Check movement diagnostics
        with open(exp_path / "reports" / "eval_latest.json") as f:
            eval_report = json.load(f)
        metrics = eval_report["metrics"]
        assert "frames_grounded" in metrics, "frames_grounded missing"
        assert metrics["frames_grounded"]["mean"] is not None, "frames_grounded is None"
        assert metrics["frames_airborne"]["mean"] is not None, "frames_airborne is None"
        
        assert metrics["frames_grounded"]["sum"] + metrics["frames_airborne"]["sum"] > 0, "no movement registered"
        
        # Check ZIP
        bundle_path = exp_path / f"{exp_path.name}_diagnostic_bundle.zip"
        assert bundle_path.exists(), "diagnostic bundle missing"
        with zipfile.ZipFile(bundle_path, 'r') as zf:
            namelist = zf.namelist()
            assert "train_timing.json" in namelist
            assert "orchestration_timing.json" in namelist
            assert "eval_latest.json" in namelist
            assert "latest_eval_ep0.jsonl" in namelist
            
    print("Tous les critères d'audit ont réussi !")

if __name__ == "__main__":
    import os
    main()
