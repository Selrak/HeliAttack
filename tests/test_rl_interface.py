from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

import ha2_constants as const
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


def test_combat_v1_out_of_bounds_safety_terminates():
    env = HeliAttack2Env(render_mode=None, training_profile="combat_v1")
    env.reset(seed=0)
    env._y = env.map_pixel_height + 1
    _obs, _reward, terminated, truncated, info = env.step(IDLE_ACTION)
    assert terminated is True
    assert truncated is False
    assert info["termination_reason"] == "out_of_bounds_safety"
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


def test_combat_v1_defensive_info_keys_exist():
    env = HeliAttack2Env(render_mode=None, training_profile="combat_v1", spawn_default_heli=False)
    env.reset(seed=0)
    _obs, _reward, _terminated, _truncated, info = env.step(IDLE_ACTION)
    assert "defensive_diagnostics" in info
    for key in [
        "visible_enemy_bullets_current",
        "visible_enemy_bullets_seen_unique",
        "visible_enemy_bullet_hit_rate_against_player",
        "damage_event_frames",
        "longest_damage_free_streak",
    ]:
        assert key in info
        assert key in info["defensive_diagnostics"]
    env.close()


def test_visible_enemy_bullet_count_excludes_offscreen_bullets():
    env = HeliAttack2Env(render_mode=None, training_profile="combat_v1", spawn_default_heli=False)
    env.reset(seed=0)
    env._add_enemy_bullet(20.0, 220.0, 0.0, 0.0)
    env._add_enemy_bullet(const.SCREEN_WIDTH + 20.0, 220.0, 0.0, 0.0)
    _obs, _reward, _terminated, _truncated, info = env.step(IDLE_ACTION)
    assert info["visible_enemy_bullets_current"] == 1
    assert info["visible_enemy_bullets_seen_unique"] == 1
    assert info["engine_enemy_bullets_active"] == 2
    env.close()


def test_visible_enemy_bullet_top10_diagnostics():
    env = HeliAttack2Env(render_mode=None, training_profile="combat_v1", spawn_default_heli=False)
    env.reset(seed=0)
    for index in range(12):
        env._add_enemy_bullet(20.0 + index * 10.0, 220.0, 0.0, 0.0)
    _obs, _reward, _terminated, _truncated, info = env.step(IDLE_ACTION)
    assert info["visible_enemy_bullets_current"] == 12
    assert info["visible_enemy_bullets_over_top10_frames"] == 1
    assert info["max_visible_enemy_bullets_over_top10_excess"] == 2
    env.close()


def test_damage_frames_recorded_for_enemy_bullet_hit():
    env = HeliAttack2Env(render_mode=None, training_profile="combat_v1", spawn_default_heli=False)
    env.reset(seed=0)
    left, top, right, bottom = env._player_hit_rect()
    env._add_enemy_bullet((left + right) / 2, (top + bottom) / 2, 0.0, 0.0)
    _obs, _reward, _terminated, _truncated, info = env.step(IDLE_ACTION)
    assert info["damage_event_frames"] == [1]
    assert info["damage_events"] == 1
    assert info["time_to_first_damage"] == 1
    assert info["damage_free_episode"] is False
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


def test_observation_audit_documents_bullet_limitations():
    text = (Path("docs/ai/OBSERVATION_AUDIT.md")).read_text(encoding="utf-8")
    assert "37" in text
    assert "nearest enemy bullet" in text
    assert "velocity" in text
    assert "one" in text.lower() or "1" in text
