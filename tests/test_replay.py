from __future__ import annotations

import numpy as np

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
