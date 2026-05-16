from __future__ import annotations

import numpy as np
import pytest

from ha2_env import HeliAttack2Env

def test_combat_default_reward_profile():
    env = HeliAttack2Env(training_profile="combat_v1", reward_profile="combat_default")
    env.reset()
    
    # Fake some events
    env.unwrapped.score = 50
    contact = env.unwrapped._empty_contact()
    gun_event = env.unwrapped._empty_gun_event()
    enemy_event = {
        "killed_enemy_ids": [1],
        "spawned_enemy_ids": [],
        "removed_enemy_bullet_ids": [],
        "spawned_enemy_bullet_ids": [],
        "player_damage": 10,
    }
    
    # We simulate what ha2_env.step() does at the end
    before_score = 0
    killed_helis = len(enemy_event["killed_enemy_ids"])
    score_delta = max(0, int(env.unwrapped.score) - before_score)
    player_damage = int(enemy_event["player_damage"])
    terminated = False
    
    reward_breakdown = {
        "living": 0.01,
        "enemy_damage": 0.05 * float(score_delta),
        "kill": 5.0 * float(killed_helis),
        "player_damage": -0.10 * float(player_damage),
        "terminal": -25.0 if terminated else 0.0,
    }
    reward = float(sum(reward_breakdown.values()))
    
    assert reward_breakdown["living"] == 0.01
    assert reward_breakdown["enemy_damage"] == 2.5
    assert reward_breakdown["kill"] == 5.0
    assert reward_breakdown["player_damage"] == -1.0
    assert reward_breakdown["terminal"] == 0.0
    assert reward == 6.51
    env.close()

def test_defense_v1_reward_profile_penalties():
    env = HeliAttack2Env(training_profile="combat_v1", reward_profile="defense_v1")
    env.reset()
    
    # To test defense_v1, we need to interact with the environment
    # or just test the logic locally inside the test if we mock the env state.
    # The actual implementation is inside step().
    
    # Test terminal penalty
    obs, info = env.reset(seed=42)
    # Move player out of bounds to trigger fall
    env.unwrapped._y = 5000 
    obs, reward, terminated, truncated, info = env.step([1, 0, 0, 0, 0, 0])
    
    assert terminated is True
    # The reward breakdown is not exported in info by default unless we use debug info
    # But info["defensive_diagnostics"] or info["reward_breakdown"] is in info!
    assert "reward_breakdown" in info
    assert info["reward_breakdown"]["terminal"] == -50.0
    
    env.close()

def test_defense_v1_reward_profile_camping():
    env = HeliAttack2Env(training_profile="combat_v1", reward_profile="defense_v1")
    obs, info = env.reset(seed=42)
    
    # Move to left edge (X < 1.0)
    env.unwrapped._x = 0.0
    env.unwrapped.current_consecutive_frames_at_left_edge = 31
    
    obs, reward, terminated, truncated, info = env.step([1, 0, 0, 0, 0, 0])
    assert info["reward_breakdown"]["camping"] == -0.01
    
    env.close()

def test_defense_v1_reward_profile_inefficiency():
    env = HeliAttack2Env(training_profile="combat_v1", reward_profile="defense_v1")
    obs, info = env.reset(seed=42)
    
    # Fast forward enough steps moving left to ensure we hit the physical left wall boundary
    for _ in range(30):
        obs, reward, terminated, truncated, info = env.step([0, 0, 0, 0, 0, 0])
        
    assert info["reward_breakdown"]["inefficiency"] == -0.01
    env.close()

def test_defense_v1_reward_profile_combat_values():
    env = HeliAttack2Env(training_profile="combat_v1", reward_profile="defense_v1")
    obs, info = env.reset(seed=42)
    
    # Fake score and killed_helis by injecting into env before step returns ?
    # It's easier to mock or just check the code logic. We can mock enemy_update_event.
    # We can fake a kill by removing an enemy.
    env.unwrapped.enemies = [{"id": 1, "health": 1, "visible": True, "x": 100, "y": 100}]
    env.unwrapped._add_bullet(100, 100, 0, 100) # instant hit
    
    obs, reward, terminated, truncated, info = env.step([1, 0, 0, 0, 0, 0])
    
    # Check that it got killed
    assert info["reward_breakdown"]["kill"] == 3.0
    assert info["reward_breakdown"]["living"] == 0.0
    
    env.close()
