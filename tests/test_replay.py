from __future__ import annotations

import json

import numpy as np
import pytest

from ha2_env import HeliAttack2Env
from ha2_replay import JsonlReplayWriter, load_replay, verify_replay_file


def test_replay_roundtrip(tmp_path):
    path = tmp_path / "roundtrip.jsonl"
    rng = np.random.default_rng(7)
    env = HeliAttack2Env(render_mode=None)
    obs, _info = env.reset(seed=7)

    with JsonlReplayWriter(path, env, 7, obs) as writer:
        for _ in range(50):
            action = rng.integers(0, env.action_space.nvec).astype(int).tolist()
            obs, reward, terminated, truncated, info = env.step(action)
            writer.append_step(env, action, obs, reward, terminated, truncated, info)
            if terminated or truncated:
                break
    env.close()

    header, steps = load_replay(path)
    assert header["schema_version"] == 1
    assert len(steps) > 0
    assert verify_replay_file(path) == len(steps)


def test_replay_detects_bullet_state_mismatch(tmp_path):
    path = tmp_path / "bullets.jsonl"
    env = HeliAttack2Env(render_mode=None)
    obs, _info = env.reset(seed=11)

    with JsonlReplayWriter(path, env, 11, obs) as writer:
        for action in ([[1, 0, 0, 0, 0, 0]] * 60) + ([[1, 0, 0, 0, 0, 1]] * 10):
            obs, reward, terminated, truncated, info = env.step(action)
            writer.append_step(env, action, obs, reward, terminated, truncated, info)
    env.close()

    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    for record in records:
        if record.get("type") == "step" and record["debug"].get("active_bullets", 0) > 0:
            record["state_hash"] = "badbulletstate"
            break
    path.write_text(
        "\n".join(json.dumps(record, separators=(",", ":")) for record in records) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError, match="State hash mismatch"):
        verify_replay_file(path)
