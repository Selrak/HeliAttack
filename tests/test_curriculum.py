from __future__ import annotations

import numpy as np
import pytest

from ha2_env import (
    DEFAULT_AIM_BIN,
    HeliAttack2Env,
    MovementNoBoostScriptedAttackDirectWrapper,
    MovementScriptedAttackDirectWrapper,
    apply_control_mode,
    get_full_action,
    get_policy_action,
    make_controlled_env,
)
from ha2_replay import load_replay
from scripts import evaluate_model, train_parkour

def test_movement_scripted_wrapper_action_space():
    env = HeliAttack2Env(training_profile="combat_v1")
    wrapper = MovementScriptedAttackDirectWrapper(env)
    assert wrapper.action_space.nvec.tolist() == [3, 2, 2, 2]
    wrapper.close()

def test_movement_no_boost_scripted_wrapper_action_space():
    env = HeliAttack2Env(training_profile="combat_v1")
    wrapper = MovementNoBoostScriptedAttackDirectWrapper(env)
    assert wrapper.action_space.nvec.tolist() == [3, 2, 2]
    wrapper.close()

def test_movement_wrapper_translates_actions():
    env = HeliAttack2Env(training_profile="combat_v1")
    env.reset(seed=42)
    wrapper = MovementScriptedAttackDirectWrapper(env)
    
    # Test when no enemy is present (fire should be 0, aim should be default)
    # Clear enemies just in case
    env.unwrapped.enemies = []
    
    action_in = np.array([2, 1, 0, 1])
    action_out = wrapper.action(action_in)
    
    assert action_out.tolist() == [2, 1, 0, 1, DEFAULT_AIM_BIN, 0]
    assert wrapper.last_policy_action == [2, 1, 0, 1]
    assert wrapper.last_full_action == [2, 1, 0, 1, DEFAULT_AIM_BIN, 0]
    wrapper.close()

def test_no_boost_wrapper_forces_boost_0():
    env = HeliAttack2Env(training_profile="combat_v1")
    env.reset(seed=42)
    wrapper = MovementNoBoostScriptedAttackDirectWrapper(env)
    env.unwrapped.enemies = []
    
    action_in = np.array([1, 1, 1])
    action_out = wrapper.action(action_in)
    
    # Boost is index 3, should be 0
    assert action_out.tolist() == [1, 1, 1, 0, DEFAULT_AIM_BIN, 0]
    assert wrapper.last_policy_action == [1, 1, 1]
    assert wrapper.last_full_action == [1, 1, 1, 0, DEFAULT_AIM_BIN, 0]
    wrapper.close()

def test_scripted_aim_points_at_enemy():
    env = HeliAttack2Env(training_profile="combat_v1")
    env.reset(seed=42)
    wrapper = MovementScriptedAttackDirectWrapper(env)
    
    # Manually insert an enemy
    enemy_x, enemy_y = 500.0, 100.0
    env.unwrapped.enemies = [{
        "id": 1,
        "health": 100,
        "visible": True,
        "x": enemy_x,
        "y": enemy_y
    }]
    env.unwrapped._x = 400.0
    env.unwrapped._y = 100.0
    
    action_in = np.array([1, 0, 0, 0])
    action_out = wrapper.action(action_in)
    
    # Should fire (index 5 is 1)
    assert action_out[5] == 1
    
    # Target is to the right. Muzzle is offset slightly, but generally aim should point right.
    # Exact bin calculation happens via aim_bin_for_world_target
    expected_bin = env.unwrapped.aim_bin_for_world_target(enemy_x, enemy_y)
    assert action_out[4] == expected_bin
    
    wrapper.close()

def test_full_mode_unchanged():
    env = HeliAttack2Env(training_profile="combat_v1")
    assert env.action_space.nvec.tolist() == [3, 2, 2, 2, 32, 2]
    env.close()


def test_make_controlled_env_spaces_and_last_actions():
    env = make_controlled_env(
        training_profile="combat_v1",
        control_mode="movement_no_boost_scripted_attack_direct",
    )
    obs, _info = env.reset(seed=1)
    assert env.action_space.nvec.tolist() == [3, 2, 2]
    obs, _reward, _terminated, _truncated, _info = env.step([2, 1, 0])
    assert get_policy_action(env) == [2, 1, 0]
    assert get_full_action(env)[3] == 0
    assert len(obs) > 0
    env.close()


def test_apply_control_mode_full_returns_original_env():
    env = HeliAttack2Env(training_profile="combat_v1")
    assert apply_control_mode(env, "full") is env
    env.close()


@pytest.mark.slow
def test_m0_training_eval_replay_records_full_no_boost_actions(tmp_path):
    pytest.importorskip("stable_baselines3")
    root = tmp_path / "experiments"
    m0_layout = train_parkour.main(
        [
            "--training-profile",
            "combat_bullets_v1",
            "--control-mode",
            "movement_no_boost_scripted_attack_direct",
            "--total-timesteps",
            "16",
            "--n-envs",
            "1",
            "--vec-env",
            "dummy",
            "--wandb",
            "off",
            "--train-eval",
            "off",
            "--max-episode-steps",
            "40",
            "--experiments-root",
            str(root),
        ]
    )
    full_layout = train_parkour.main(
        [
            "--training-profile",
            "combat_bullets_v1",
            "--control-mode",
            "full",
            "--total-timesteps",
            "16",
            "--n-envs",
            "1",
            "--vec-env",
            "dummy",
            "--wandb",
            "off",
            "--train-eval",
            "off",
            "--max-episode-steps",
            "40",
            "--experiments-root",
            str(root),
        ]
    )
    import json

    m0_config = json.loads(m0_layout.config_path.read_text(encoding="utf-8"))
    full_config = json.loads(full_layout.config_path.read_text(encoding="utf-8"))
    assert m0_config["policy_action_space_nvec"] == [3, 2, 2]
    assert m0_config["sim_action_space_nvec"] == [3, 2, 2, 2, 32, 2]
    assert full_config["policy_action_space_nvec"] == [3, 2, 2, 2, 32, 2]
    assert m0_config["trainable_parameters"] != full_config["trainable_parameters"]

    evaluate_model.main(
        [
            "--experiment",
            str(m0_layout.path),
            "--model-choice",
            "latest",
            "--episodes",
            "1",
            "--save-replays",
            "--report-name",
            "eval_m0_test.json",
            "--replay-prefix",
            "m0_test",
            "--max-episode-steps",
            "40",
        ]
    )
    report = json.loads((m0_layout.reports_dir / "eval_m0_test.json").read_text(encoding="utf-8"))
    assert report["control_mode"] == "movement_no_boost_scripted_attack_direct"
    assert report["policy_action_space_nvec"] == [3, 2, 2]
    assert "boost" not in report["policy_action_distributions"]
    assert report["metrics"]["boost_activations"]["sum"] == 0.0
    assert report["metrics"]["frames_boost_pressed"]["sum"] == 0.0
    assert set(report["full_action_distributions"]["boost"]) == {"0"}

    _header, steps = load_replay(m0_layout.replays_dir / "m0_test_ep0.jsonl")
    assert steps
    assert all(len(step["action"]) == 6 for step in steps)
    assert all(step["action"][3] == 0 for step in steps)
