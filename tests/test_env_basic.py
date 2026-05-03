from __future__ import annotations

import time

import numpy as np

from ha2_env import HeliAttack2Env


def test_import_reset_step():
    env = HeliAttack2Env(render_mode=None)
    obs, info = env.reset(seed=123)
    assert obs.shape == (4,)
    assert "state_hash" in info
    obs, reward, terminated, truncated, info = env.step([1, 0, 0, 0])
    assert obs.shape == (4,)
    assert reward == 0.1
    assert terminated is False
    assert truncated is False
    assert "state_hash" in info
    env.close()


def test_spaces_sanity():
    env = HeliAttack2Env(render_mode=None)
    assert env.action_space.nvec.tolist() == [3, 2, 2, 2]
    obs, _info = env.reset(seed=0)
    assert env.observation_space.contains(obs)
    env.close()


def test_deterministic_fixed_actions():
    actions = [
        [1, 0, 0, 0],
        [2, 0, 0, 0],
        [2, 1, 0, 0],
        [2, 1, 0, 0],
        [1, 0, 0, 1],
        [0, 0, 1, 0],
    ] * 20

    hashes = []
    for _ in range(2):
        env = HeliAttack2Env(render_mode=None)
        env.reset(seed=42)
        for action in actions:
            env.step(action)
        hashes.append(env.state_hash())
        env.close()

    assert hashes[0] == hashes[1]


def test_rgb_array_smoke():
    env = HeliAttack2Env(render_mode="rgb_array", auto_render=False)
    env.reset(seed=0)
    frame = env.render()
    assert isinstance(frame, np.ndarray)
    assert frame.shape == (320, 450, 3)
    env.close()


def test_headless_speed_smoke():
    env = HeliAttack2Env(render_mode=None)
    env.reset(seed=0)
    start = time.perf_counter()
    steps = 2_000
    for _ in range(steps):
        env.step([1, 0, 0, 0])
    elapsed = time.perf_counter() - start
    steps_per_sec = steps / elapsed
    assert steps_per_sec > 1_000
    env.close()
