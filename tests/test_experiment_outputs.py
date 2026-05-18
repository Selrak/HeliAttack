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
from scripts.evaluate_model import build_evaluation_report


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


def test_evaluation_report_defensive_metrics_handle_no_damage(tmp_path):
    stats = [
        {
            "reward": 1.0,
            "reward_breakdown": {"living": 0.2, "player_damage": 0.0},
            "length": 20,
            "termination_reason": "time_limit",
            "falls": 0,
            "deaths": 0,
            "heli_kills": 0,
            "heli_hits": 0,
            "player_shot_attempts": 0,
            "player_bullets_spawned": 0,
            "player_shots_spawn_blocked": 0,
            "total_player_damage": 0,
            "enemy_bullet_hits": 0,
            "frames_pressing_left": 0,
            "frames_pressing_right": 0,
            "frames_actual_moving_left": 0,
            "frames_actual_moving_right": 0,
            "frames_at_left_edge": 0,
            "frames_at_right_edge": 0,
            "frames_pressing_left_at_left_edge": 0,
            "frames_pressing_right_at_right_edge": 0,
            "final_score": 0,
            "max_score": 0,
            "visible_enemy_bullets_seen_unique": 0,
            "visible_enemy_bullets_hit_player": 0,
            "visible_enemy_bullets_removed_without_hit": 0,
            "visible_enemy_bullets_max": 0,
            "visible_enemy_bullets_mean": 0.0,
            "visible_enemy_bullets_p95": 0.0,
            "visible_enemy_bullets_over_top10_frames": 0,
            "max_visible_enemy_bullets_over_top10_excess": 0,
            "damage_events": 0,
            "time_to_first_damage": None,
            "mean_frames_between_damage": None,
            "min_frames_between_damage": None,
            "max_frames_between_damage": None,
            "frames_since_last_damage": 20,
            "longest_damage_free_streak": 20,
            "damage_free_episode": True,
            "engine_enemy_bullets_spawned": 0,
            "engine_enemy_bullets_active": 0,
            "enemy_bullet_hits_not_visible": 0,
            "action_frequencies": {"1|0|0|0|0|0": 20},
        }
    ]
    report = build_evaluation_report(
        layout=None,
        model_path=tmp_path / "model.zip",
        effective_model_choice="path",
        training_profile="combat_v1",
        max_episode_steps=20,
        episodes=1,
        stats=stats,
        replay_paths=[],
    )
    assert report["rates"]["visible_enemy_bullet_hit_rate_against_player"] is None
    assert report["rates"]["damage_free_episode_rate"] == 1.0
    assert report["metrics"]["time_to_first_damage"]["mean"] is None
    assert report["metrics"]["longest_damage_free_streak"]["mean"] == 20.0
    assert report["reward_breakdown"]["living"]["sum"] == 0.2
    assert report["reward_breakdown"]["player_damage"]["sum"] == 0.0
    assert report["pressure_profile"] == "normal"


def test_run_experiment_forwards_reward_profile_to_final_eval(tmp_path, monkeypatch):
    from scripts import run_experiment

    layout = ExperimentLayout(tmp_path, tmp_path / "exp")
    layout.ensure_directories()
    layout.summary_path.write_text("# Summary\n", encoding="utf-8")
    (layout.models_dir / "latest.zip").write_text("model", encoding="utf-8")

    def fake_train(args_list):
        assert "--reward-profile" in args_list
        assert args_list[args_list.index("--reward-profile") + 1] == "defense_v1"
        assert "--pressure-profile" in args_list
        assert args_list[args_list.index("--pressure-profile") + 1] == "enemy_fire_slow_4x"
        return layout

    eval_calls = []

    def fake_eval(args_list):
        eval_calls.append(args_list)
        assert "--reward-profile" in args_list
        assert args_list[args_list.index("--reward-profile") + 1] == "defense_v1"
        assert "--pressure-profile" in args_list
        assert args_list[args_list.index("--pressure-profile") + 1] == "enemy_fire_slow_4x"
        model_choice = args_list[args_list.index("--model-choice") + 1]
        report = {
            "metrics": {
                "reward": {"mean": 0.0},
                "length": {"mean": 1.0},
                "heli_kills": {"mean": 0.0},
                "player_damage": {"mean": 0.0},
                "final_score": {"mean": 0.0},
                "frames_grounded": {"mean": 0.0},
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
                "longest_damage_free_streak": {"mean": 0.0},
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
            "net_arch": "test",
            "training_profile": "combat_v1",
            "control_mode": "full",
            "reward_profile": "defense_v1",
            "pressure_profile": "enemy_fire_slow_4x",
        }
        write_json_file(layout.report_path(model_choice), report)

    monkeypatch.setattr(run_experiment.train_parkour, "main", fake_train)
    monkeypatch.setattr(run_experiment.evaluate_model, "main", fake_eval)

    run_experiment.main(
        [
            "--reward-profile",
            "defense_v1",
            "--pressure-profile",
            "enemy_fire_slow_4x",
            "--train-eval",
            "off",
            "--eval-episodes",
            "1",
            "--wandb",
            "off",
        ]
    )

    assert len(eval_calls) == 1
