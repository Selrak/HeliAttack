from __future__ import annotations


def test_legacy_env_import_reset_step_and_hash():
    import ha2_env
    import ha2_env_legacy

    assert ha2_env_legacy.HeliAttack2Env is not ha2_env.HeliAttack2Env

    env = ha2_env_legacy.HeliAttack2Env(render_mode=None)
    try:
        obs, info = env.reset(seed=0)
        assert obs is not None
        assert isinstance(info, dict)
        for _ in range(5):
            obs, reward, terminated, truncated, info = env.step([1, 0, 0, 0, 16, 0])
            assert obs is not None
            assert isinstance(reward, float)
            assert isinstance(terminated, bool)
            assert isinstance(truncated, bool)
            assert isinstance(info, dict)
        assert isinstance(env.get_state(), dict)
        assert isinstance(env.state_hash(), str)
    finally:
        env.close()
