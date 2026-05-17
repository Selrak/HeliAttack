from __future__ import annotations

import argparse
import json
import subprocess
import sys
from types import SimpleNamespace
from pathlib import Path

import numpy as np
from gymnasium import spaces

from scripts.runtime_config import (
    add_runtime_config_args,
    explicit_runtime_overrides,
    resolve_runtime_config,
    runtime_env_kwargs,
)


def test_runtime_config_precedence_cli_over_config_over_default():
    parser = argparse.ArgumentParser()
    add_runtime_config_args(parser)
    config = {
        "training_profile": "combat_bullets_v1",
        "control_mode": "movement_scripted_attack_direct",
        "reward_profile": "defense_v1",
        "max_episode_steps": 777,
    }

    inferred = resolve_runtime_config(parser.parse_args([]), config)
    assert inferred.training_profile == "combat_bullets_v1"
    assert inferred.control_mode == "movement_scripted_attack_direct"
    assert inferred.reward_profile == "defense_v1"
    assert inferred.max_episode_steps == 777

    overridden_args = parser.parse_args(
        [
            "--training-profile",
            "combat_v1",
            "--control-mode",
            "full",
            "--reward-profile",
            "combat_default",
            "--max-episode-steps",
            "123",
        ]
    )
    overridden = resolve_runtime_config(overridden_args, config)
    assert overridden.training_profile == "combat_v1"
    assert overridden.control_mode == "full"
    assert overridden.reward_profile == "combat_default"
    assert overridden.max_episode_steps == 123
    assert set(explicit_runtime_overrides(overridden_args, config, overridden)) == {
        "training_profile",
        "control_mode",
        "reward_profile",
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
    assert seen_kwargs[0]["max_episode_steps"] == 222
    assert report["training_profile"] == "combat_bullets_v1"
    assert report["control_mode"] == "movement_scripted_attack_direct"
    assert report["reward_profile"] == "defense_v1"


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
    assert seen_kwargs[0]["max_episode_steps"] == 123
    assert report["training_profile"] == "combat_v1"
    assert report["control_mode"] == "full"
    assert report["reward_profile"] == "combat_default"


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
    assert seen_kwargs[0]["max_episode_steps"] == 222


def test_runtime_args_are_accepted_by_user_scripts():
    scripts = [
        "scripts.train_parkour",
        "scripts.evaluate_model",
        "scripts.watch_model",
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
        assert "--max-episode-steps" in help_text
