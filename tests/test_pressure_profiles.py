from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from ha2_env import ENEMY_BULLET_DAMAGE, ENEMY_BULLET_SPEED, HeliAttack2Env
from ha2_replay import JsonlReplayWriter, load_replay, verify_replay_file


IDLE_ACTION = [1, 0, 0, 0, 0, 0]


def run_enemy_fire_horizon(profile: str, steps: int = 240):
    env = HeliAttack2Env(render_mode=None, pressure_profile=profile)
    env.reset(seed=7)
    first_bullet = None
    try:
        for _ in range(steps):
            _obs, _reward, _terminated, _truncated, info = env.step(IDLE_ACTION)
            if info["enemy_event"]["spawned_enemy_bullet_ids"] and first_bullet is None:
                bullet = dict(env.enemy_bullets[-1])
                speed = (float(bullet["xspeed"]) ** 2 + float(bullet["yspeed"]) ** 2) ** 0.5
                first_bullet = {
                    "speed": speed,
                    "damage": int(bullet["damage"]),
                }
        return env.total_enemy_bullets_spawned, first_bullet, env.state_hash()
    finally:
        env.close()


def test_pressure_profile_normal_matches_implicit_default():
    explicit_count, _explicit_bullet, explicit_hash = run_enemy_fire_horizon("normal")
    env = HeliAttack2Env(render_mode=None)
    env.reset(seed=7)
    try:
        for _ in range(240):
            env.step(IDLE_ACTION)
        assert env.pressure_profile == "normal"
        assert env.total_enemy_bullets_spawned == explicit_count
        assert env.state_hash() == explicit_hash
    finally:
        env.close()


def test_slow_pressure_profiles_reduce_enemy_fire_only():
    normal_count, normal_bullet, _normal_hash = run_enemy_fire_horizon("normal")
    slow2_count, slow2_bullet, _slow2_hash = run_enemy_fire_horizon("enemy_fire_slow_2x")
    slow4_count, slow4_bullet, _slow4_hash = run_enemy_fire_horizon("enemy_fire_slow_4x")

    assert normal_count > slow2_count > slow4_count
    for bullet in (normal_bullet, slow2_bullet, slow4_bullet):
        assert bullet is not None
        assert bullet["speed"] == pytest.approx(ENEMY_BULLET_SPEED)
        assert bullet["damage"] == ENEMY_BULLET_DAMAGE


def test_replay_records_and_verifies_pressure_profile(tmp_path):
    replay_path = tmp_path / "slow4.jsonl"
    env = HeliAttack2Env(
        render_mode=None,
        training_profile="combat_v1",
        reward_profile="defense_v1",
        pressure_profile="enemy_fire_slow_4x",
        max_episode_steps=300,
    )
    obs, _info = env.reset(seed=11)
    try:
        with JsonlReplayWriter(replay_path, env, 11, obs) as writer:
            for _ in range(60):
                obs, reward, terminated, truncated, info = env.step(IDLE_ACTION)
                writer.append_step(env, IDLE_ACTION, obs, reward, terminated, truncated, info)
                if terminated or truncated:
                    break
    finally:
        env.close()

    header, steps = load_replay(replay_path)
    assert header["pressure_profile"] == "enemy_fire_slow_4x"
    assert header["reward_profile"] == "defense_v1"
    assert steps[0]["debug"]["pressure_profile"] == "enemy_fire_slow_4x"
    assert verify_replay_file(replay_path) == len(steps)


def test_replay_verification_uses_recorded_pressure_profile(tmp_path):
    replay_path = tmp_path / "slow4_long.jsonl"
    env = HeliAttack2Env(render_mode=None, pressure_profile="enemy_fire_slow_4x")
    obs, _info = env.reset(seed=7)
    try:
        with JsonlReplayWriter(replay_path, env, 7, obs) as writer:
            for _ in range(120):
                obs, reward, terminated, truncated, info = env.step(IDLE_ACTION)
                writer.append_step(env, IDLE_ACTION, obs, reward, terminated, truncated, info)
    finally:
        env.close()

    assert verify_replay_file(replay_path) == 120

    lines = replay_path.read_text(encoding="utf-8").splitlines()
    header = json.loads(lines[0])
    header["pressure_profile"] = "normal"
    bad_replay = tmp_path / "wrong_pressure.jsonl"
    bad_replay.write_text(
        "\n".join([json.dumps(header, separators=(",", ":")), *lines[1:]]) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(AssertionError, match="State hash mismatch|Reward mismatch"):
        verify_replay_file(bad_replay)


def test_play_human_accepts_pressure_profile_values():
    for profile in ("normal", "enemy_fire_slow_2x", "enemy_fire_slow_4x"):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import argparse; "
                    "from scripts.runtime_config import add_runtime_config_args, resolve_runtime_config; "
                    "p=argparse.ArgumentParser(); "
                    "add_runtime_config_args(p, training_profile_default='legacy', max_episode_steps_default=None); "
                    f"c=resolve_runtime_config(p.parse_args(['--pressure-profile','{profile}'])); "
                    "print(c.pressure_profile)"
                ),
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=True,
        )
        assert result.stdout.strip() == profile
