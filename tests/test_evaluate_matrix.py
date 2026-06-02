from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import pytest

from scripts import evaluate_matrix


def make_experiment(root: Path, name: str, *, config: dict | None = None) -> Path:
    exp = root / name
    (exp / "models").mkdir(parents=True)
    (exp / "reports").mkdir()
    (exp / "models" / "latest.zip").write_text("latest", encoding="utf-8")
    (exp / "models" / "best.zip").write_text("best", encoding="utf-8")
    (exp / "config.json").write_text(
        json.dumps(
            config
            or {
                "training_profile": "combat_bullets_v1",
                "control_mode": "movement_no_boost_scripted_attack_direct",
                "reward_profile": "defense_v1",
                "pressure_profile": "enemy_fire_slow_2x",
                "max_episode_steps": 1800,
            }
        ),
        encoding="utf-8",
    )
    return exp


def fake_eval_report(*, pressure_profile: str) -> dict:
    return {
        "training_profile": "combat_bullets_v1",
        "control_mode": "movement_no_boost_scripted_attack_direct",
        "reward_profile": "defense_v1",
        "pressure_profile": pressure_profile,
        "metrics": {
            "reward": {"mean": 12.0},
            "length": {"mean": 200.0},
            "player_damage": {"mean": 10.0},
            "damage_events": {"mean": 1.0},
            "heli_kills": {"mean": 2.0},
            "engine_enemy_bullets_spawned": {"mean": 30.0},
            "time_to_first_damage": {"mean": 50.0},
            "longest_damage_free_streak": {"mean": 100.0},
            "boost_activations": {"mean": 0.0},
            "frames_boost_pressed": {"mean": 0.0},
            "frames_grounded": {"mean": 150.0},
            "frames_airborne": {"mean": 50.0},
            "sum_abs_player_dx": {"mean": 44.0},
        },
        "rates": {
            "death_rate": 0.0,
            "fall_rate": 0.0,
            "out_of_bounds_safety_rate": 0.0,
            "timeout_rate": 1.0,
            "damage_free_episode_rate": 0.0,
            "visible_enemy_bullet_hit_rate_against_player": 0.1,
            "left_edge_camping_rate": 0.2,
            "right_edge_camping_rate": 0.0,
            "input_motion_mismatch_rate": 0.3,
        },
    }


def test_parse_entry_accepts_windows_paths_and_rejects_malformed():
    entry = evaluate_matrix.parse_entry(r"label=M0;experiment=experiments\foo\bar;model=latest")
    assert entry.label == "M0"
    assert str(entry.experiment) == r"experiments\foo\bar"
    assert entry.model == "latest"

    with pytest.raises(Exception):
        evaluate_matrix.parse_entry("label=M0;experiment=no_model")
    with pytest.raises(Exception):
        evaluate_matrix.parse_entry("label=M0;experiment=x;model=latest;model=best")


def test_eval_id_is_short_and_unambiguous():
    eval_id = evaluate_matrix.make_eval_id(
        1,
        "M0 no boost with a very long descriptive label",
        "latest",
        "enemy_fire_slow_4x",
        max_length=64,
    )
    assert eval_id.startswith("001_M0-no-boost")
    assert len(eval_id) <= 64
    assert "pressure-" in eval_id


def test_dry_run_writes_config_manifest_and_bundle_without_subprocess(tmp_path, monkeypatch):
    exp = make_experiment(tmp_path / "experiments", "m0")
    monkeypatch.chdir(tmp_path)

    def forbidden_popen(*args, **kwargs):
        raise AssertionError("dry-run must not launch subprocesses")

    monkeypatch.setattr(evaluate_matrix.subprocess, "Popen", forbidden_popen)

    matrix_dir = evaluate_matrix.main(
        [
            "--matrix-name",
            "dry",
            "--entry",
            f"label=M0;experiment={exp};model=latest",
            "--pressure-profiles",
            "enemy_fire_slow_4x,normal",
            "--episodes",
            "1",
            "--max-episode-steps",
            "200",
            "--output-root",
            str(tmp_path / "matrices"),
            "--dry-run",
        ]
    )

    config = json.loads((matrix_dir / "matrix_config.json").read_text(encoding="utf-8"))
    manifest = json.loads((matrix_dir / "matrix_manifest.json").read_text(encoding="utf-8"))
    assert config["dry_run"] is True
    assert config["save_replays"] is False
    assert len(manifest["jobs"]) == 2
    assert all(job["dry_run"] for job in manifest["jobs"].values())
    assert (matrix_dir / "matrix_summary.json").exists()
    assert (matrix_dir / "argv.json").exists()
    assert (matrix_dir / "command.txt").exists()
    assert (matrix_dir / "resolved_config.json").exists()
    bundle = next(matrix_dir.glob("*_bundle.zip"))
    with zipfile.ZipFile(bundle) as zf:
        names = set(zf.namelist())
    assert "matrix_config.json" in names
    assert "resolved_config.json" in names
    assert "argv.json" in names
    assert "command.txt" in names
    assert "matrix_manifest.json" in names
    assert "matrix_summary.md" in names


def test_duplicate_labels_are_rejected(tmp_path):
    exp = make_experiment(tmp_path / "experiments", "m0")
    entry = f"label=M0;experiment={exp};model=latest"
    with pytest.raises(SystemExit, match="Duplicate"):
        evaluate_matrix.main(
            [
                "--matrix-name",
                "dupes",
                "--entry",
                entry,
                "--entry",
                entry,
                "--pressure-profiles",
                "normal",
                "--output-root",
                str(tmp_path / "matrices"),
                "--dry-run",
            ]
        )


def test_real_matrix_with_mocked_subprocess_copies_reports_summarizes_and_sets_env(tmp_path, monkeypatch):
    exp = make_experiment(tmp_path / "experiments", "m0")
    monkeypatch.chdir(tmp_path)
    seen_envs = []
    seen_commands = []

    class FakeProcess:
        def __init__(self, command, stdout, stderr, cwd, env, text):
            self.command = command
            self.returncode = 0
            seen_envs.append(env)
            seen_commands.append(command)
            experiment = Path(command[command.index("--experiment") + 1])
            report_name = command[command.index("--report-name") + 1]
            pressure = command[command.index("--pressure-profile") + 1]
            report_path = experiment / "reports" / report_name
            report_path.write_text(json.dumps(fake_eval_report(pressure_profile=pressure)), encoding="utf-8")
            stdout.write(f"Wrote {report_path}\n")

        def poll(self):
            return self.returncode

        def wait(self):
            return self.returncode

        def kill(self):
            self.returncode = -9

    monkeypatch.setattr(evaluate_matrix.subprocess, "Popen", FakeProcess)

    matrix_dir = evaluate_matrix.main(
        [
            "--matrix-name",
            "mock",
            "--entry",
            f"label=M0;experiment={exp};model=latest",
            "--pressure-profiles",
            "enemy_fire_slow_4x",
            "--episodes",
            "1",
            "--max-episode-steps",
            "200",
            "--max-parallel",
            "1",
            "--threads-per-job",
            "3",
            "--output-root",
            str(tmp_path / "matrices"),
            "--no-save-replays",
        ]
    )

    jobs = list((matrix_dir / "jobs").iterdir())
    assert len(jobs) == 1
    job_dir = jobs[0]
    assert (job_dir / "eval_report.json").exists()
    assert (job_dir / "stdout.log").exists()
    assert (job_dir / "stderr.log").exists()
    assert (job_dir / "command.txt").exists()
    assert (job_dir / "metadata.json").exists()
    assert (job_dir / "parent_config.json").exists()
    assert seen_envs[0]["OMP_NUM_THREADS"] == "3"
    assert seen_envs[0]["MKL_NUM_THREADS"] == "3"
    assert seen_envs[0]["NUMEXPR_NUM_THREADS"] == "3"
    assert seen_envs[0]["HA2_TORCH_NUM_THREADS"] == "3"
    assert sys.executable == seen_commands[0][0]
    assert "-m" in seen_commands[0]
    assert "scripts.evaluate_model" in seen_commands[0]
    summary = json.loads((matrix_dir / "matrix_summary.json").read_text(encoding="utf-8"))
    assert summary["matrix_duration_seconds"] >= 0
    assert summary["job_count"] == 1
    assert summary["succeeded_count"] == 1
    row = summary["rows"][0]
    assert row["mean_reward"] == 12.0
    assert row["visible_bullet_hit_rate"] == 0.1
    assert row["pressure_profile"] == "enemy_fire_slow_4x"
    csv_text = (matrix_dir / "matrix_summary.csv").read_text(encoding="utf-8")
    md_text = (matrix_dir / "matrix_summary.md").read_text(encoding="utf-8")
    assert "mean_reward" in csv_text
    assert "eval_report.json" in md_text
    bundle = next(matrix_dir.glob("*_bundle.zip"))
    with zipfile.ZipFile(bundle) as zf:
        names = set(zf.namelist())
    assert f"jobs/{job_dir.name}/eval_report.json" in names
    assert f"jobs/{job_dir.name}/metadata.json" in names
    assert "command.txt" in names
    assert "argv.json" in names
    assert "resolved_config.json" in names


def test_save_replays_is_opt_in(tmp_path):
    exp = make_experiment(tmp_path / "experiments", "m0")
    matrix_id, matrix_dir = evaluate_matrix.unique_matrix_dir(tmp_path / "matrices", "replay_default")
    matrix_dir.mkdir(parents=True)
    entry = evaluate_matrix.MatrixEntry("M0", exp, "latest")

    default_jobs = evaluate_matrix.build_jobs(
        entries=[entry],
        pressure_profiles=["normal"],
        matrix_id=matrix_id,
        matrix_dir=matrix_dir,
        episodes=1,
        max_episode_steps=200,
        save_replays=False,
        damage_forensics=False,
        damage_forensics_window=60,
        threads_per_job=1,
        overrides={"training_profile": None, "control_mode": None, "reward_profile": None},
        timeout_seconds=None,
    )
    opt_in_jobs = evaluate_matrix.build_jobs(
        entries=[entry],
        pressure_profiles=["normal"],
        matrix_id=matrix_id,
        matrix_dir=matrix_dir,
        episodes=1,
        max_episode_steps=200,
        save_replays=True,
        damage_forensics=False,
        damage_forensics_window=60,
        threads_per_job=1,
        overrides={"training_profile": None, "control_mode": None, "reward_profile": None},
        timeout_seconds=None,
    )

    assert "--save-replays" not in default_jobs[0].command
    assert "--save-replays" in opt_in_jobs[0].command


def test_damage_forensics_flag_is_forwarded_to_eval_jobs(tmp_path):
    exp = make_experiment(tmp_path / "experiments", "m0")
    matrix_id, matrix_dir = evaluate_matrix.unique_matrix_dir(tmp_path / "matrices", "forensics")
    matrix_dir.mkdir(parents=True)
    entry = evaluate_matrix.MatrixEntry("M0", exp, "latest")

    jobs = evaluate_matrix.build_jobs(
        entries=[entry],
        pressure_profiles=["normal"],
        matrix_id=matrix_id,
        matrix_dir=matrix_dir,
        episodes=1,
        max_episode_steps=200,
        save_replays=False,
        damage_forensics=True,
        damage_forensics_window=7,
        threads_per_job=1,
        overrides={"training_profile": None, "control_mode": None, "reward_profile": None},
        timeout_seconds=None,
    )

    assert "--damage-forensics" in jobs[0].command
    assert jobs[0].command[jobs[0].command.index("--damage-forensics") + 1] == "on"
    assert jobs[0].command[jobs[0].command.index("--damage-forensics-window") + 1] == "7"


def test_fail_fast_skips_pending_jobs_without_hanging(tmp_path, monkeypatch):
    exp = make_experiment(tmp_path / "experiments", "m0")
    monkeypatch.chdir(tmp_path)

    class FailingProcess:
        def __init__(self, command, stdout, stderr, cwd, env, text):
            self.returncode = 1
            stderr.write("failed\n")

        def poll(self):
            return self.returncode

        def wait(self):
            return self.returncode

        def kill(self):
            self.returncode = -9

    monkeypatch.setattr(evaluate_matrix.subprocess, "Popen", FailingProcess)

    matrix_dir = evaluate_matrix.main(
        [
            "--matrix-name",
            "fail_fast",
            "--entry",
            f"label=M0;experiment={exp};model=latest",
            "--pressure-profiles",
            "enemy_fire_slow_4x,normal",
            "--episodes",
            "1",
            "--max-episode-steps",
            "200",
            "--max-parallel",
            "1",
            "--threads-per-job",
            "1",
            "--output-root",
            str(tmp_path / "matrices"),
            "--fail-fast",
        ]
    )

    manifest = json.loads((matrix_dir / "matrix_manifest.json").read_text(encoding="utf-8"))
    jobs = list(manifest["jobs"].values())
    assert jobs[0]["env_updates"]["HA2_TORCH_NUM_THREADS"] == "1"
    assert jobs[0]["exit_code"] == 1
    assert jobs[1]["skipped"] is True
    assert jobs[1]["skip_reason"] == "fail_fast"


def test_matrix_copies_damage_forensics_outputs_and_bundles_them(tmp_path, monkeypatch):
    exp = make_experiment(tmp_path / "experiments", "m0")
    monkeypatch.chdir(tmp_path)

    class ForensicsProcess:
        def __init__(self, command, stdout, stderr, cwd, env, text):
            self.returncode = 0
            experiment = Path(command[command.index("--experiment") + 1])
            report_name = command[command.index("--report-name") + 1]
            report_path = experiment / "reports" / report_name
            forensics_json = experiment / "reports" / f"damage_forensics_{Path(report_name).stem}.json"
            forensics_md = experiment / "reports" / f"damage_forensics_{Path(report_name).stem}.md"
            forensics_json.write_text(
                json.dumps(
                    {
                        "aggregate": {
                            "heuristic_tag_counts": {
                                "high_bullet_density": 1,
                                "possible_missed_boost": 2,
                                "boost_related_or_cooldown": 1,
                            }
                        },
                        "events": [],
                    }
                ),
                encoding="utf-8",
            )
            forensics_md.write_text("# Damage Forensics\n", encoding="utf-8")
            report = fake_eval_report(pressure_profile="normal")
            report["damage_forensics"] = {
                "enabled": True,
                "json_path": str(forensics_json),
                "markdown_path": str(forensics_md),
            }
            report_path.write_text(json.dumps(report), encoding="utf-8")

        def poll(self):
            return self.returncode

        def wait(self):
            return self.returncode

        def kill(self):
            self.returncode = -9

    monkeypatch.setattr(evaluate_matrix.subprocess, "Popen", ForensicsProcess)

    matrix_dir = evaluate_matrix.main(
        [
            "--matrix-name",
            "forensics_copy",
            "--entry",
            f"label=M0;experiment={exp};model=latest",
            "--pressure-profiles",
            "normal",
            "--episodes",
            "1",
            "--max-episode-steps",
            "200",
            "--max-parallel",
            "1",
            "--threads-per-job",
            "1",
            "--output-root",
            str(tmp_path / "matrices"),
            "--damage-forensics",
        ]
    )

    job_dir = next((matrix_dir / "jobs").iterdir())
    assert (job_dir / "damage_forensics.json").exists()
    assert (job_dir / "damage_forensics.md").exists()
    summary = json.loads((matrix_dir / "matrix_summary.json").read_text(encoding="utf-8"))
    assert summary["rows"][0]["damage_forensics_available"] is True
    assert summary["rows"][0]["high_bullet_density_hits"] == 1
    assert summary["rows"][0]["boost_related_hits"] == 3
    bundle = next(matrix_dir.glob("*_bundle.zip"))
    with zipfile.ZipFile(bundle) as zf:
        names = set(zf.namelist())
    assert f"jobs/{job_dir.name}/damage_forensics.json" in names
    assert f"jobs/{job_dir.name}/damage_forensics.md" in names
