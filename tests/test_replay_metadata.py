from __future__ import annotations

import json

import pytest

import ha2_collision as collision
from ha2_env import ENV_VERSION, HeliAttack2Env
from ha2_replay import (
    CURRENT_SIMULATOR_ID,
    LEGACY_SIMULATOR_ID,
    JsonlReplayWriter,
    load_replay,
    recorded_replay_simulator_config,
    resolve_replay_simulator_config,
    verify_replay_file,
)


def _write_short_replay(path, *, collision_model=collision.COLLISION_MODEL_RECT):
    env = HeliAttack2Env(render_mode=None, collision_model=collision_model)
    obs, _info = env.reset(seed=3)
    try:
        with JsonlReplayWriter(path, env, 3, obs) as writer:
            action = [1, 0, 0, 0, 0, 0]
            obs, reward, terminated, truncated, info = env.step(action)
            writer.append_step(env, action, obs, reward, terminated, truncated, info)
    finally:
        env.close()


def _rewrite_header(path, mutate):
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    mutate(records[0])
    path.write_text(
        "\n".join(json.dumps(record, separators=(",", ":")) for record in records) + "\n",
        encoding="utf-8",
    )


def test_new_replay_header_records_simulator_metadata(tmp_path):
    path = tmp_path / "metadata.jsonl"
    _write_short_replay(path, collision_model=collision.COLLISION_MODEL_FFDEC_POLYGON)

    header, _steps = load_replay(path)
    assert header["simulator_id"] == CURRENT_SIMULATOR_ID
    assert header["simulator_version"] == ENV_VERSION
    assert header["simulation_semantics"]["collision_model"] == collision.COLLISION_MODEL_FFDEC_POLYGON


def test_old_header_without_simulator_metadata_infers_legacy_rect(tmp_path):
    path = tmp_path / "old.jsonl"
    _write_short_replay(path)

    def mutate(header):
        header.pop("simulator_id")
        header.pop("simulator_version")
        header.pop("simulation_semantics")
        header["env_version"] = "0.6"

    _rewrite_header(path, mutate)

    config = recorded_replay_simulator_config(load_replay(path)[0])
    assert config.simulator_id == LEGACY_SIMULATOR_ID
    assert config.simulation_semantics["collision_model"] == collision.COLLISION_MODEL_RECT
    assert verify_replay_file(path) == 1


def test_replay_resolution_defaults_to_recorded_semantics(tmp_path):
    path = tmp_path / "polygon.jsonl"
    _write_short_replay(path, collision_model=collision.COLLISION_MODEL_FFDEC_POLYGON)

    header, _steps = load_replay(path)
    config = resolve_replay_simulator_config(header)
    assert config.simulator_id == CURRENT_SIMULATOR_ID
    assert config.simulation_semantics["collision_model"] == collision.COLLISION_MODEL_FFDEC_POLYGON
    assert verify_replay_file(path) == 1


def test_replay_resolution_can_force_current_or_legacy(tmp_path):
    path = tmp_path / "current.jsonl"
    _write_short_replay(path, collision_model=collision.COLLISION_MODEL_FFDEC_POLYGON)

    header, _steps = load_replay(path)
    current = resolve_replay_simulator_config(header, replay_env="current")
    legacy = resolve_replay_simulator_config(header, replay_env="legacy")

    assert current.simulator_id == CURRENT_SIMULATOR_ID
    assert current.simulation_semantics["collision_model"] == collision.COLLISION_MODEL_FFDEC_POLYGON
    assert legacy.simulator_id == LEGACY_SIMULATOR_ID
    assert legacy.simulation_semantics["collision_model"] == collision.COLLISION_MODEL_RECT
    assert verify_replay_file(path, replay_env="current") == 1
    assert verify_replay_file(path, replay_env="legacy") == 1


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("simulator_id", "bad_env", "Unsupported replay simulator_id"),
        ("collision_model", "bad_collision", "Unsupported replay collision_model"),
    ],
)
def test_invalid_replay_metadata_fails_clearly(tmp_path, field, value, message):
    path = tmp_path / "bad.jsonl"
    _write_short_replay(path)

    def mutate(header):
        if field == "simulator_id":
            header["simulator_id"] = value
        else:
            header["simulation_semantics"]["collision_model"] = value

    _rewrite_header(path, mutate)

    with pytest.raises(ValueError, match=message):
        verify_replay_file(path)


def test_unclear_old_header_fails_clearly(tmp_path):
    path = tmp_path / "unclear.jsonl"
    _write_short_replay(path)

    def mutate(header):
        header.pop("simulator_id")
        header.pop("simulator_version")
        header.pop("simulation_semantics")
        header["env_version"] = "unknown"

    _rewrite_header(path, mutate)

    with pytest.raises(ValueError, match="no simulator_id"):
        verify_replay_file(path)
