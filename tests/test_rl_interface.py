from __future__ import annotations

import numpy as np
import pytest

from ha2_env import COMBAT_V1_OBS_SIZE, HeliAttack2Env
from ha2_replay import JsonlReplayWriter, load_replay, verify_replay_file


IDLE_ACTION = [1, 0, 0, 0, 0, 0]


def test_combat_v1_observation_space_reset_and_step():
    env = HeliAttack2Env(
        render_mode=None,
        training_profile="combat_v1",
        max_episode_steps=300,
    )
    obs, _info = env.reset(seed=0)
    assert obs.shape == (COMBAT_V1_OBS_SIZE,)
    assert obs.dtype == np.float32
    assert np.isfinite(obs).all()
    assert env.observation_space.contains(obs)

    obs, _reward, _terminated, _truncated, info = env.step(IDLE_ACTION)
    assert obs.shape == (COMBAT_V1_OBS_SIZE,)
    assert np.isfinite(obs).all()
    assert env.observation_space.contains(obs)
    assert info["training_profile"] == "combat_v1"
    env.close()


def test_legacy_profile_remains_default_shape_and_reward():
    env = HeliAttack2Env(render_mode=None)
    obs, _info = env.reset(seed=0)
    assert obs.shape == (4,)
    obs, reward, terminated, truncated, info = env.step([1, 0, 0, 0])
    assert obs.shape == (4,)
    assert reward == 0.1
    assert terminated is False
    assert truncated is False
    assert "reward_breakdown" not in info
    env.close()


def test_unknown_training_profile_fails_fast():
    with pytest.raises(ValueError, match="Unknown training_profile"):
        HeliAttack2Env(render_mode=None, training_profile="unknown")


def test_combat_v1_player_death_terminates():
    env = HeliAttack2Env(render_mode=None, training_profile="combat_v1")
    env.reset(seed=0)
    env.health = 0
    _obs, reward, terminated, truncated, info = env.step(IDLE_ACTION)
    assert terminated is True
    assert truncated is False
    assert info["termination_reason"] == "player_death"
    assert info["reward_breakdown"]["terminal"] == -25.0
    assert reward < 0
    env.close()


def test_combat_v1_fall_terminates():
    env = HeliAttack2Env(render_mode=None, training_profile="combat_v1")
    env.reset(seed=0)
    env._y = env.map_pixel_height + 1
    _obs, _reward, terminated, truncated, info = env.step(IDLE_ACTION)
    assert terminated is True
    assert truncated is False
    assert info["termination_reason"] == "fall"
    env.close()


def test_combat_v1_time_limit_truncates():
    env = HeliAttack2Env(
        render_mode=None,
        training_profile="combat_v1",
        max_episode_steps=1,
    )
    env.reset(seed=0)
    _obs, _reward, terminated, truncated, info = env.step(IDLE_ACTION)
    assert terminated is False
    assert truncated is True
    assert info["termination_reason"] == "time_limit"
    env.close()


def test_combat_v1_enemy_damage_reward_component():
    env = HeliAttack2Env(
        render_mode=None,
        training_profile="combat_v1",
        spawn_default_heli=False,
    )
    env.reset(seed=0)
    env._add_enemy(health=300, x=150.0, y=100.0)
    env._add_bullet(100.0, 100.0, 0.0, 10)
    _obs, reward, _terminated, _truncated, info = env.step(IDLE_ACTION)
    assert info["reward_breakdown"]["enemy_damage"] > 0
    assert reward > 0
    env.close()


def test_combat_v1_player_damage_penalty_component():
    env = HeliAttack2Env(
        render_mode=None,
        training_profile="combat_v1",
        spawn_default_heli=False,
    )
    env.reset(seed=0)
    left, top, right, bottom = env._player_hit_rect()
    env._add_enemy_bullet((left + right) / 2, (top + bottom) / 2, 0.0, 0.0)
    _obs, reward, _terminated, _truncated, info = env.step(IDLE_ACTION)
    assert info["reward_breakdown"]["player_damage"] < 0
    assert reward < 0
    env.close()


def test_combat_v1_replay_header_verifies_with_profile(tmp_path):
    path = tmp_path / "combat_v1.jsonl"
    env = HeliAttack2Env(
        render_mode=None,
        training_profile="combat_v1",
        max_episode_steps=20,
    )
    obs, _info = env.reset(seed=5)
    with JsonlReplayWriter(path, env, 5, obs) as writer:
        for _ in range(3):
            obs, reward, terminated, truncated, info = env.step(IDLE_ACTION)
            writer.append_step(env, IDLE_ACTION, obs, reward, terminated, truncated, info)
            if terminated or truncated:
                break
    env.close()

    header, _steps = load_replay(path)
    assert header["training_profile"] == "combat_v1"
    assert header["max_episode_steps"] == 20
    assert verify_replay_file(path) == 3


def test_combat_v1_sb3_env_checker():
    pytest.importorskip("stable_baselines3")
    from stable_baselines3.common.env_checker import check_env

    env = HeliAttack2Env(
        render_mode=None,
        training_profile="combat_v1",
        max_episode_steps=300,
    )
    try:
        check_env(env, warn=True)
    finally:
        env.close()
