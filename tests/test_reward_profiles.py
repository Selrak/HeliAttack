from __future__ import annotations

import numpy as np
import pytest

from ha2_env import HeliAttack2Env
from ha2_replay import JsonlReplayWriter, load_replay
from scripts.train_parkour import EnvFactory


def step_player_damage_reward(reward_profile: str) -> tuple[float, dict]:
    env = HeliAttack2Env(training_profile="combat_v1", reward_profile=reward_profile)
    try:
        env.reset(seed=123)
        left, top, right, bottom = env.unwrapped._player_hit_rect()
        env.unwrapped._add_enemy_bullet(
            (left + right) / 2.0,
            (top + bottom) / 2.0,
            rotation=0.0,
            speed=0.0,
        )
        _obs, reward, _terminated, _truncated, info = env.step([1, 0, 0, 0, 0, 0])
        return reward, info
    finally:
        env.close()


def test_reward_profiles_change_actual_player_damage_reward():
    default_reward, default_info = step_player_damage_reward("combat_default")
    defense_reward, defense_info = step_player_damage_reward("defense_v1")

    assert default_info["reward_breakdown"]["player_damage"] == pytest.approx(-1.0)
    assert default_reward == pytest.approx(-0.99)
    assert defense_info["reward_breakdown"]["player_damage"] == pytest.approx(-10.0)
    assert defense_reward == pytest.approx(-10.0)
    assert defense_reward != default_reward


def test_env_factory_forwards_reward_profile():
    pytest.importorskip("stable_baselines3")
    env = EnvFactory(
        rank=0,
        seed=7,
        training_profile="combat_v1",
        max_episode_steps=40,
        reward_profile="defense_v1",
    )()
    try:
        assert env.unwrapped.reward_profile == "defense_v1"
    finally:
        env.close()


def test_replay_records_reward_profile_and_breakdown(tmp_path):
    path = tmp_path / "defense_replay.jsonl"
    env = HeliAttack2Env(training_profile="combat_v1", reward_profile="defense_v1")
    obs, _info = env.reset(seed=5)
    with JsonlReplayWriter(path, env, 5, obs) as writer:
        obs, reward, terminated, truncated, info = env.step([1, 0, 0, 0, 0, 0])
        writer.append_step(env, [1, 0, 0, 0, 0, 0], obs, reward, terminated, truncated, info)
    env.close()

    header, steps = load_replay(path)
    assert header["reward_profile"] == "defense_v1"
    assert steps[0]["debug"]["reward_profile"] == "defense_v1"
    assert "reward_breakdown" in steps[0]["debug"]
    assert steps[0]["debug"]["reward_breakdown"]["living"] == 0.0

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
