from __future__ import annotations

import numpy as np
import pytest

from ha2_env import HeliAttack2Env, MovementScriptedAttackDirectWrapper, MovementNoBoostScriptedAttackDirectWrapper, DEFAULT_AIM_BIN

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
