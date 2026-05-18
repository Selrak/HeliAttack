from __future__ import annotations

import argparse
import json
import subprocess
import sys
from types import SimpleNamespace
from pathlib import Path

import numpy as np
import pytest
from gymnasium import spaces

from scripts.runtime_config import (
    add_runtime_config_args,
    explicit_runtime_overrides,
    parse_human_count,
    resolve_runtime_config,
    runtime_env_kwargs,
)


def test_parse_human_count_accepts_suffix_and_underscore_forms():
    assert parse_human_count("500_000") == 500_000
    assert parse_human_count("1_000_000") == 1_000_000
    assert parse_human_count("500k") == 500_000
    assert parse_human_count("1M") == 1_000_000


def test_runtime_config_precedence_cli_over_config_over_default():
    parser = argparse.ArgumentParser()
    add_runtime_config_args(parser)
    config = {
        "training_profile": "combat_bullets_v1",
        "control_mode": "movement_scripted_attack_direct",
        "reward_profile": "defense_v1",
        "pressure_profile": "enemy_fire_slow_4x",
        "max_episode_steps": 777,
    }

    inferred = resolve_runtime_config(parser.parse_args([]), config)
    assert inferred.training_profile == "combat_bullets_v1"
    assert inferred.control_mode == "movement_scripted_attack_direct"
    assert inferred.reward_profile == "defense_v1"
    assert inferred.pressure_profile == "enemy_fire_slow_4x"
    assert inferred.max_episode_steps == 777

    overridden_args = parser.parse_args(
        [
            "--training-profile",
            "combat_v1",
            "--control-mode",
            "full",
            "--reward-profile",
            "combat_default",
            "--pressure-profile",
            "normal",
            "--max-episode-steps",
            "1M",
        ]
    )
    overridden = resolve_runtime_config(overridden_args, config)
    assert overridden.training_profile == "combat_v1"
    assert overridden.control_mode == "full"
    assert overridden.reward_profile == "combat_default"
    assert overridden.pressure_profile == "normal"
    assert overridden.max_episode_steps == 1_000_000
    assert set(explicit_runtime_overrides(overridden_args, config, overridden)) == {
        "training_profile",
        "control_mode",
        "reward_profile",
        "pressure_profile",
        "max_episode_steps",
    }


def test_runtime_env_kwargs_contains_env_creation_values():
    parser = argparse.ArgumentParser()
    add_runtime_config_args(parser)
    config = resolve_runtime_config(
        parser.parse_args(["--reward-profile", "defense_v1"])
    )
    assert runtime_env_kwargs(config) == {
        "training_profile": "combat_v1",
        "control_mode": "full",
        "reward_profile": "defense_v1",
        "pressure_profile": "normal",
        "max_episode_steps": 1800,
    }


class FakeModel:
    def predict(self, obs, deterministic=True):
        return np.array([1, 0, 0, 0, 0, 0]), None


class FakePPO:
    @staticmethod
    def load(path):
        return FakeModel()


class FakeEnv:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.control_mode = kwargs["control_mode"]
        self.training_profile = kwargs["training_profile"]
        self.reward_profile = kwargs["reward_profile"]
        self.pressure_profile = kwargs["pressure_profile"]
        self.max_episode_steps = kwargs["max_episode_steps"]
        self.action_space = spaces.MultiDiscrete([3, 2, 2, 2, 32, 2])
        self.unwrapped = self
        self._x = 25.0
        self.score = 0
        self.window = None
        self.window_size = (450, 320)

    def reset(self, seed=0):
        return np.zeros(1, dtype=np.float32), {}

    def step(self, action):
        info = {
            "termination_reason": "time_limit",
            "total_player_damage": 0,
            "heli_kills": 0,
            "heli_hits": 0,
            "player_shot_attempts": 0,
            "player_bullets_spawned": 0,
            "player_shots_spawn_blocked": 0,
            "enemy_bullet_hits": 0,
            "reward_breakdown": {
                "living": 0.0,
                "enemy_damage": 0.0,
                "kill": 0.0,
                "player_damage": 0.0,
                "terminal": 0.0,
                "camping": 0.0,
                "inefficiency": 0.0,
            },
            "defensive_diagnostics": {},
            "movement_diagnostics": {},
            "combat": {"score": 0},
        }
        return np.zeros(1, dtype=np.float32), 0.0, False, True, info

    def render(self, **kwargs):
        return None

    def close(self):
        return None


class FakeTrainPolicy:
    activation_fn = type("FakeActivation", (), {})

    def parameters(self):
        return []


class FakeTrainModel:
    action_space = spaces.MultiDiscrete([3, 2, 2])
    observation_space = spaces.Box(
        low=-np.ones(84, dtype=np.float32),
        high=np.ones(84, dtype=np.float32),
        dtype=np.float32,
    )
    learn_calls: list[dict] = []

    def __init__(self):
        self.policy = FakeTrainPolicy()
        self.tensorboard_log = None
        self.env = None

    def set_env(self, env):
        self.env = env

    def learn(self, total_timesteps, callback=None, reset_num_timesteps=True):
        self.learn_calls.append(
            {
                "total_timesteps": total_timesteps,
                "reset_num_timesteps": reset_num_timesteps,
            }
        )
        return self

    def save(self, path):
        path = Path(path)
        if path.suffix != ".zip":
            path = path.with_suffix(".zip")
        path.write_text("model", encoding="utf-8")


class FakeTrainPPO:
    @staticmethod
    def load(path, **kwargs):
        return FakeTrainModel()


class FakeCheckpointCallback:
    def __init__(self, *args, **kwargs):
        pass


class FakeEvalCallback:
    def __init__(self, *args, **kwargs):
        pass


class FakeVecEnv:
    action_space = spaces.MultiDiscrete([3, 2, 2])
    observation_space = spaces.Box(
        low=-np.ones(84, dtype=np.float32),
        high=np.ones(84, dtype=np.float32),
        dtype=np.float32,
    )

    def close(self):
        return None


def test_evaluate_model_infers_runtime_config_from_experiment(tmp_path, monkeypatch):
    from scripts import evaluate_model
    from scripts.experiment_utils import ExperimentLayout

    layout = ExperimentLayout(tmp_path, tmp_path / "exp")
    layout.ensure_directories()
    (layout.models_dir / "latest.zip").write_text("model", encoding="utf-8")
    layout.config_path.write_text(
        json.dumps(
            {
                "training_profile": "combat_bullets_v1",
                "control_mode": "movement_scripted_attack_direct",
                "reward_profile": "defense_v1",
                "pressure_profile": "enemy_fire_slow_4x",
                "max_episode_steps": 222,
            }
        ),
        encoding="utf-8",
    )
    seen_kwargs = []
    monkeypatch.setattr(evaluate_model, "_load_ppo", lambda: FakePPO)
    monkeypatch.setattr(
        evaluate_model,
        "make_controlled_env",
        lambda **kwargs: seen_kwargs.append(kwargs) or FakeEnv(**kwargs),
    )

    evaluate_model.main(
        [
            "--experiment",
            str(layout.path),
            "--model-choice",
            "latest",
            "--episodes",
            "1",
            "--report-name",
            "eval_runtime_test.json",
        ]
    )

    report = json.loads((layout.reports_dir / "eval_runtime_test.json").read_text())
    assert seen_kwargs[0]["training_profile"] == "combat_bullets_v1"
    assert seen_kwargs[0]["control_mode"] == "movement_scripted_attack_direct"
    assert seen_kwargs[0]["reward_profile"] == "defense_v1"
    assert seen_kwargs[0]["pressure_profile"] == "enemy_fire_slow_4x"
    assert seen_kwargs[0]["max_episode_steps"] == 222
    assert report["training_profile"] == "combat_bullets_v1"
    assert report["control_mode"] == "movement_scripted_attack_direct"
    assert report["reward_profile"] == "defense_v1"
    assert report["pressure_profile"] == "enemy_fire_slow_4x"


def test_evaluate_model_cli_overrides_experiment_runtime_config(tmp_path, monkeypatch):
    from scripts import evaluate_model
    from scripts.experiment_utils import ExperimentLayout

    layout = ExperimentLayout(tmp_path, tmp_path / "exp")
    layout.ensure_directories()
    (layout.models_dir / "latest.zip").write_text("model", encoding="utf-8")
    layout.config_path.write_text(
        json.dumps(
            {
                "training_profile": "combat_bullets_v1",
                "control_mode": "movement_scripted_attack_direct",
                "reward_profile": "defense_v1",
                "pressure_profile": "enemy_fire_slow_4x",
                "max_episode_steps": 222,
            }
        ),
        encoding="utf-8",
    )
    seen_kwargs = []
    monkeypatch.setattr(evaluate_model, "_load_ppo", lambda: FakePPO)
    monkeypatch.setattr(
        evaluate_model,
        "make_controlled_env",
        lambda **kwargs: seen_kwargs.append(kwargs) or FakeEnv(**kwargs),
    )

    evaluate_model.main(
        [
            "--experiment",
            str(layout.path),
            "--model-choice",
            "latest",
            "--episodes",
            "1",
            "--training-profile",
            "combat_v1",
            "--control-mode",
            "full",
            "--reward-profile",
            "combat_default",
            "--pressure-profile",
            "normal",
            "--max-episode-steps",
            "123",
            "--report-name",
            "eval_runtime_override.json",
        ]
    )

    report = json.loads((layout.reports_dir / "eval_runtime_override.json").read_text())
    assert seen_kwargs[0]["training_profile"] == "combat_v1"
    assert seen_kwargs[0]["control_mode"] == "full"
    assert seen_kwargs[0]["reward_profile"] == "combat_default"
    assert seen_kwargs[0]["pressure_profile"] == "normal"
    assert seen_kwargs[0]["max_episode_steps"] == 123
    assert report["training_profile"] == "combat_v1"
    assert report["control_mode"] == "full"
    assert report["reward_profile"] == "combat_default"
    assert report["pressure_profile"] == "normal"


def test_watch_model_infers_runtime_config_from_experiment(tmp_path, monkeypatch):
    from scripts import watch_model
    from scripts.experiment_utils import ExperimentLayout
    import ha2_env

    layout = ExperimentLayout(tmp_path, tmp_path / "exp")
    layout.ensure_directories()
    (layout.models_dir / "latest.zip").write_text("model", encoding="utf-8")
    layout.config_path.write_text(
        json.dumps(
            {
                "training_profile": "combat_bullets_v1",
                "control_mode": "movement_scripted_attack_direct",
                "reward_profile": "defense_v1",
                "pressure_profile": "enemy_fire_slow_2x",
                "max_episode_steps": 222,
            }
        ),
        encoding="utf-8",
    )
    seen_kwargs = []
    monkeypatch.setattr(watch_model, "_load_ppo", lambda: FakePPO)
    monkeypatch.setattr(
        ha2_env,
        "make_controlled_env",
        lambda **kwargs: seen_kwargs.append(kwargs) or FakeEnv(**kwargs),
    )

    class FakeClock:
        def tick(self, fps):
            return None

    fake_pygame = SimpleNamespace(
        QUIT=1,
        KEYDOWN=2,
        K_ESCAPE=27,
        K_f=102,
        event=SimpleNamespace(get=lambda: [SimpleNamespace(type=1)]),
        time=SimpleNamespace(Clock=lambda: FakeClock()),
    )
    monkeypatch.setitem(sys.modules, "pygame", fake_pygame)

    watch_model.main(
        [
            "--experiment",
            str(layout.path),
            "--model-choice",
            "latest",
        ]
    )

    assert seen_kwargs[0]["training_profile"] == "combat_bullets_v1"
    assert seen_kwargs[0]["control_mode"] == "movement_scripted_attack_direct"
    assert seen_kwargs[0]["reward_profile"] == "defense_v1"
    assert seen_kwargs[0]["pressure_profile"] == "enemy_fire_slow_2x"
    assert seen_kwargs[0]["max_episode_steps"] == 222


def test_train_parkour_resume_writes_lineage_and_uses_no_reset_default(tmp_path, monkeypatch):
    from scripts import train_parkour

    parent = tmp_path / "parent_exp"
    parent_models = parent / "models"
    parent_models.mkdir(parents=True)
    parent_model = parent_models / "latest.zip"
    parent_model.write_text("model", encoding="utf-8")
    (parent / "config.json").write_text(
        json.dumps(
            {
                "training_profile": "combat_bullets_v1",
                "control_mode": "movement_no_boost_scripted_attack_direct",
                "reward_profile": "defense_v1",
                "pressure_profile": "enemy_fire_slow_4x",
            }
        ),
        encoding="utf-8",
    )
    FakeTrainModel.learn_calls.clear()
    monkeypatch.setattr(
        train_parkour,
        "_load_sb3",
        lambda: (FakeTrainPPO, FakeCheckpointCallback, FakeEvalCallback, object, object, object),
    )
    monkeypatch.setattr(train_parkour, "make_vec_env", lambda **kwargs: FakeVecEnv())

    layout = train_parkour.main(
        [
            "--experiments-root",
            str(tmp_path / "experiments"),
            "--experiment-name",
            "child_resume",
            "--resume-from",
            str(parent_model),
            "--total-timesteps",
            "5",
            "--train-eval",
            "off",
            "--wandb",
            "off",
            "--training-profile",
            "combat_bullets_v1",
            "--control-mode",
            "movement_no_boost_scripted_attack_direct",
            "--reward-profile",
            "defense_v1",
            "--pressure-profile",
            "enemy_fire_slow_2x",
        ]
    )

    config = json.loads(layout.config_path.read_text(encoding="utf-8"))
    resolved = json.loads((layout.path / "resolved_config.json").read_text(encoding="utf-8"))
    summary = layout.summary_path.read_text(encoding="utf-8")
    assert layout.path != parent
    assert isinstance(json.loads((layout.path / "argv.json").read_text(encoding="utf-8")), list)
    assert "scripts.train_parkour" in (layout.path / "command.txt").read_text(encoding="utf-8")
    assert resolved["experiment_label"] == "child_resume"
    assert config["resume_from"] == str(parent_model)
    assert config["parent_experiment_dir"] == str(parent)
    assert config["parent_training_profile"] == "combat_bullets_v1"
    assert config["parent_control_mode"] == "movement_no_boost_scripted_attack_direct"
    assert config["parent_reward_profile"] == "defense_v1"
    assert config["parent_pressure_profile"] == "enemy_fire_slow_4x"
    assert config["reset_num_timesteps"] is False
    assert config["fine_tune_timesteps"] == 5
    assert FakeTrainModel.learn_calls[-1]["reset_num_timesteps"] is False
    assert "resume_from" in summary
    assert "fine_tune_timesteps" in summary


def test_train_parkour_resume_rejects_incompatible_action_space(tmp_path, monkeypatch):
    from scripts import train_parkour

    parent_model = tmp_path / "model.zip"
    parent_model.write_text("model", encoding="utf-8")
    original_action_space = FakeTrainModel.action_space
    FakeTrainModel.action_space = spaces.MultiDiscrete([3, 2, 2, 2, 32, 2])
    monkeypatch.setattr(
        train_parkour,
        "_load_sb3",
        lambda: (FakeTrainPPO, FakeCheckpointCallback, FakeEvalCallback, object, object, object),
    )
    monkeypatch.setattr(train_parkour, "make_vec_env", lambda **kwargs: FakeVecEnv())
    try:
        try:
            train_parkour.main(
                [
                    "--experiments-root",
                    str(tmp_path / "experiments"),
                    "--experiment-name",
                    "bad_resume",
                    "--resume-from",
                    str(parent_model),
                    "--total-timesteps",
                    "1",
                    "--train-eval",
                    "off",
                    "--training-profile",
                    "combat_bullets_v1",
                    "--control-mode",
                    "movement_no_boost_scripted_attack_direct",
                ]
            )
        except SystemExit as exc:
            assert "Cannot resume model with action_space" in str(exc)
        else:
            raise AssertionError("Expected incompatible resume to fail")
    finally:
        FakeTrainModel.action_space = original_action_space


def test_run_experiment_forwards_resume_args(tmp_path, monkeypatch):
    from scripts import run_experiment
    from scripts.experiment_utils import ExperimentLayout, write_json_file, write_text_file

    captured_train_args = []
    parent_model = tmp_path / "parent" / "models" / "latest.zip"
    parent_model.parent.mkdir(parents=True)
    parent_model.write_text("model", encoding="utf-8")
    exp_dir = Path("experiments") / "resume_orchestration"

    def fake_train_main(args_list):
        captured_train_args.extend(args_list)
        layout = ExperimentLayout(Path("experiments"), exp_dir)
        layout.ensure_directories()
        write_json_file(
            layout.config_path,
            {
                "training_profile": "combat_bullets_v1",
                "control_mode": "movement_no_boost_scripted_attack_direct",
                "reward_profile": "defense_v1",
                "pressure_profile": "enemy_fire_slow_2x",
                "resume_from": str(parent_model),
                "reset_num_timesteps": False,
                "fine_tune_timesteps": 5,
            },
        )
        write_text_file(layout.summary_path, "# Summary\n", allow_overwrite=True)
        write_text_file(layout.git_info_path, "git unavailable\n", allow_overwrite=True)
        write_text_file(layout.models_dir / "latest.zip", "model", allow_overwrite=True)
        return layout

    def fake_eval_main(args_list):
        report_path = exp_dir / "reports" / "eval_latest.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(
                {
                    "training_profile": "combat_bullets_v1",
                    "control_mode": "movement_no_boost_scripted_attack_direct",
                    "reward_profile": "defense_v1",
                    "pressure_profile": "enemy_fire_slow_2x",
                    "metrics": {
                        "reward": {"mean": 0.0},
                        "length": {"mean": 1.0},
                        "heli_kills": {"mean": 0.0},
                        "player_damage": {"mean": 0.0},
                        "final_score": {"mean": 0.0},
                    },
                    "rates": {"hit_rate": 0.0, "death_rate": 0.0, "timeout_rate": 0.0},
                }
            ),
            encoding="utf-8",
        )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(run_experiment.train_parkour, "main", fake_train_main)
    monkeypatch.setattr(run_experiment.evaluate_model, "main", fake_eval_main)

    run_experiment.main(
        [
            "--experiment-name",
            "resume_orchestration",
            "--resume-from",
            str(parent_model),
            "--total-timesteps",
            "5",
            "--train-eval",
            "off",
            "--eval-episodes",
            "1",
            "--training-profile",
            "combat_bullets_v1",
            "--control-mode",
            "movement_no_boost_scripted_attack_direct",
            "--reward-profile",
            "defense_v1",
            "--pressure-profile",
            "enemy_fire_slow_2x",
        ]
    )

    assert captured_train_args[captured_train_args.index("--resume-from") + 1] == str(parent_model)
    assert "--no-reset-num-timesteps" in captured_train_args
    assert (exp_dir / "argv.json").exists()
    assert (exp_dir / "command.txt").exists()
    assert (exp_dir / "train_argv.json").exists()
    assert (exp_dir / "train_command.txt").exists()
    assert (exp_dir / "eval_latest_argv.json").exists()
    assert (exp_dir / "eval_latest_command.txt").exists()
    resolved = json.loads((exp_dir / "resolved_config.json").read_text(encoding="utf-8"))
    assert resolved["experiment_label"] == "resume_orchestration"
    assert resolved["resume_from"] == str(parent_model)


def test_run_experiment_label_alias_and_conflict(tmp_path, monkeypatch):
    from scripts import run_experiment
    from scripts.experiment_utils import ExperimentLayout, write_json_file, write_text_file

    monkeypatch.chdir(tmp_path)
    exp_dir = Path("experiments") / "alias_run"

    def fake_train_main(args_list):
        assert args_list[args_list.index("--experiment-name") + 1] == "alias_run"
        layout = ExperimentLayout(Path("experiments"), exp_dir)
        layout.ensure_directories()
        write_json_file(
            layout.config_path,
            {
                "training_profile": "combat_v1",
                "control_mode": "full",
                "reward_profile": "combat_default",
                "pressure_profile": "normal",
            },
        )
        write_text_file(layout.summary_path, "# Summary\n", allow_overwrite=True)
        write_text_file(layout.git_info_path, "git unavailable\n", allow_overwrite=True)
        write_text_file(layout.models_dir / "latest.zip", "model", allow_overwrite=True)
        return layout

    def fake_eval_main(_args_list):
        report_path = exp_dir / "reports" / "eval_latest.json"
        report_path.write_text(
            json.dumps(
                {
                    "training_profile": "combat_v1",
                    "control_mode": "full",
                    "reward_profile": "combat_default",
                    "pressure_profile": "normal",
                    "metrics": {
                        "reward": {"mean": 0.0},
                        "length": {"mean": 1.0},
                        "heli_kills": {"mean": 0.0},
                        "player_damage": {"mean": 0.0},
                        "final_score": {"mean": 0.0},
                    },
                    "rates": {"hit_rate": 0.0, "death_rate": 0.0, "timeout_rate": 0.0},
                }
            ),
            encoding="utf-8",
        )

    monkeypatch.setattr(run_experiment.train_parkour, "main", fake_train_main)
    monkeypatch.setattr(run_experiment.evaluate_model, "main", fake_eval_main)

    run_experiment.main(["--label", "alias_run", "--train-eval", "off", "--eval-episodes", "1"])
    resolved = json.loads((exp_dir / "resolved_config.json").read_text(encoding="utf-8"))
    assert resolved["experiment_label"] == "alias_run"

    with pytest.raises(SystemExit, match="aliases"):
        run_experiment.main(["--label", "a", "--experiment-name", "b"])


def test_run_experiment_rejects_net_arch_with_resume(tmp_path):
    from scripts import run_experiment

    parent_model = tmp_path / "parent" / "models" / "latest.zip"
    parent_model.parent.mkdir(parents=True)
    parent_model.write_text("model", encoding="utf-8")

    with pytest.raises(SystemExit, match="--net-arch cannot be used"):
        run_experiment.main(
            [
                "--resume-from",
                str(parent_model),
                "--net-arch",
                "128,128",
            ]
        )


def test_runtime_args_are_accepted_by_user_scripts():
    scripts = [
        "scripts.play_human",
        "scripts.run_experiment",
        "scripts.run_experiment_pair",
    ]
    for module in scripts:
        result = subprocess.run(
            [sys.executable, "-m", module, "--help"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=True,
        )
        help_text = result.stdout
        assert "--training-profile" in help_text or module.endswith("run_experiment_pair")
        assert "--control-mode" in help_text
        assert "--reward-profile" in help_text
        assert "--pressure-profile" in help_text
        assert "--max-episode-steps" in help_text


def test_run_experiment_pair_forwards_pressure_profiles(tmp_path, monkeypatch):
    from scripts import run_experiment_pair

    calls = []

    def fake_run_job(name, args, env, log_dir):
        calls.append((name, list(args)))
        command_path = Path(log_dir) / f"{name}_command.txt"
        argv_path = Path(log_dir) / f"{name}_argv.json"
        command_path.write_text("fake command\n", encoding="utf-8")
        argv_path.write_text("[]\n", encoding="utf-8")
        return run_experiment_pair.JobResult(
            command=[sys.executable, "-m", "scripts.run_experiment", *args],
            stdout_log=str(Path(log_dir) / f"{name}.stdout.log"),
            stderr_log=str(Path(log_dir) / f"{name}.stderr.log"),
            exit_code=0,
            experiment_path=str(tmp_path / name),
            command_path=str(command_path),
            argv_path=str(argv_path),
        )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(run_experiment_pair, "run_job", fake_run_job)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_experiment_pair",
            "--mode",
            "sequential",
            "--pressure-profile",
            "enemy_fire_slow_2x",
            "--pressure-profile-b",
            "enemy_fire_slow_4x",
            "--total-timesteps",
            "1",
            "--stagger-seconds",
            "0",
        ],
    )

    run_experiment_pair.main()

    assert calls[0][1][calls[0][1].index("--pressure-profile") + 1] == "enemy_fire_slow_2x"
    assert calls[1][1][calls[1][1].index("--pressure-profile") + 1] == "enemy_fire_slow_4x"
    summary_path = next((tmp_path / "experiments").glob("pair_*/pair_summary.json"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["_metadata"]["pressure_profile_a"] == "enemy_fire_slow_2x"
    assert summary["_metadata"]["pressure_profile_b"] == "enemy_fire_slow_4x"
    pair_dir = summary_path.parent
    assert (pair_dir / "argv.json").exists()
    assert (pair_dir / "command.txt").exists()
    assert (pair_dir / "resolved_config.json").exists()
    assert (pair_dir / "pair_invocation_metadata.json").exists()


def test_run_experiment_pair_forwards_resume_paths_and_reset_overrides(tmp_path, monkeypatch):
    from scripts import run_experiment_pair

    calls = []
    common_parent = tmp_path / "common" / "models" / "latest.zip"
    parent_b = tmp_path / "parent_b" / "models" / "latest.zip"
    common_parent.parent.mkdir(parents=True)
    parent_b.parent.mkdir(parents=True)
    common_parent.write_text("model", encoding="utf-8")
    parent_b.write_text("model", encoding="utf-8")

    def fake_run_job(name, args, env, log_dir):
        calls.append((name, list(args)))
        command_path = Path(log_dir) / f"{name}_command.txt"
        argv_path = Path(log_dir) / f"{name}_argv.json"
        command_path.write_text("fake command\n", encoding="utf-8")
        argv_path.write_text("[]\n", encoding="utf-8")
        return run_experiment_pair.JobResult(
            command=[sys.executable, "-m", "scripts.run_experiment", *args],
            stdout_log=str(Path(log_dir) / f"{name}.stdout.log"),
            stderr_log=str(Path(log_dir) / f"{name}.stderr.log"),
            exit_code=0,
            experiment_path=str(tmp_path / name),
            command_path=str(command_path),
            argv_path=str(argv_path),
        )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(run_experiment_pair, "run_job", fake_run_job)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_experiment_pair",
            "--mode",
            "sequential",
            "--resume-from",
            str(common_parent),
            "--resume-from-b",
            str(parent_b),
            "--no-reset-num-timesteps",
            "--reset-num-timesteps-b",
            "--total-timesteps",
            "7",
            "--stagger-seconds",
            "0",
        ],
    )

    run_experiment_pair.main()

    args_a = calls[0][1]
    args_b = calls[1][1]
    assert args_a[args_a.index("--resume-from") + 1] == str(common_parent)
    assert "--no-reset-num-timesteps" in args_a
    assert args_b[args_b.index("--resume-from") + 1] == str(parent_b)
    assert "--reset-num-timesteps" in args_b
    summary_path = next((tmp_path / "experiments").glob("pair_*/pair_summary.json"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["_metadata"]["resume_a"]["resume_from"] == str(common_parent)
    assert summary["_metadata"]["resume_a"]["reset_num_timesteps"] is False
    assert summary["_metadata"]["resume_a"]["fine_tune_timesteps"] == 7
    assert summary["_metadata"]["resume_b"]["resume_from"] == str(parent_b)
    assert summary["_metadata"]["resume_b"]["reset_num_timesteps"] is True
    assert summary["sequential"]["job_a"]["command_path"]
    assert summary["sequential"]["job_a"]["argv_path"]
