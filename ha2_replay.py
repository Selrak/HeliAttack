from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

import ha2_collision as collision
from ha2_env import (
    CONTROL_MODE_FULL,
    ENV_NAME,
    ENV_VERSION,
    HeliAttack2Env,
    get_full_action,
    get_policy_action,
    policy_action_space_nvec,
    sim_action_space_nvec,
)


SCHEMA_VERSION = 1
CURRENT_SIMULATOR_ID = "ha2_env"
LEGACY_SIMULATOR_ID = "ha2_env_legacy"
REPLAY_ENV_RECORDED = "recorded"
REPLAY_ENV_CURRENT = "current"
REPLAY_ENV_LEGACY = "legacy"
REPLAY_ENV_CHOICES = (REPLAY_ENV_RECORDED, REPLAY_ENV_CURRENT, REPLAY_ENV_LEGACY)
PRE_SPLIT_ENV_VERSIONS = {"0.1", "0.2", "0.3", "0.4", "0.5", "0.6"}


@dataclass(frozen=True)
class ReplaySimulatorConfig:
    simulator_id: str
    simulator_version: str
    simulation_semantics: dict[str, Any]
    recorded_simulator_id: str
    recorded_simulation_semantics: dict[str, Any]
    replay_env: str


def to_jsonable(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    return value


def _simulator_id_for_env(env: Any) -> str:
    module = env.unwrapped.__class__.__module__
    if module == "ha2_env_legacy":
        return LEGACY_SIMULATOR_ID
    if module == "ha2_env":
        return CURRENT_SIMULATOR_ID
    raise ValueError(f"Unsupported replay simulator module: {module}")


def _simulator_version(simulator_id: str) -> str:
    if simulator_id == CURRENT_SIMULATOR_ID:
        return ENV_VERSION
    if simulator_id == LEGACY_SIMULATOR_ID:
        from ha2_env_legacy import ENV_VERSION as LEGACY_ENV_VERSION

        return LEGACY_ENV_VERSION
    raise ValueError(f"Unsupported simulator_id: {simulator_id}")


def _simulation_semantics_for_env(env: Any) -> dict[str, Any]:
    base_env = env.unwrapped
    return {
        "collision_model": getattr(base_env, "collision_model", collision.COLLISION_MODEL_RECT),
    }


def _validate_collision_model(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError(f"Replay collision_model must be a string, got {value!r}")
    if value not in collision.COLLISION_MODELS:
        raise ValueError(
            f"Unsupported replay collision_model {value!r}; "
            f"expected one of {sorted(collision.COLLISION_MODELS)}"
        )
    return value


def recorded_replay_simulator_config(header: dict[str, Any]) -> ReplaySimulatorConfig:
    simulator_id = header.get("simulator_id")
    if simulator_id is None:
        env_version = str(header.get("env_version", ""))
        if env_version not in PRE_SPLIT_ENV_VERSIONS:
            raise ValueError(
                "Replay has no simulator_id and env_version is not a known pre-split "
                f"version: {env_version!r}"
            )
        simulator_id = LEGACY_SIMULATOR_ID
        simulator_version = env_version
        semantics = {"collision_model": collision.COLLISION_MODEL_RECT}
        return ReplaySimulatorConfig(
            simulator_id=simulator_id,
            simulator_version=simulator_version,
            simulation_semantics=semantics,
            recorded_simulator_id=simulator_id,
            recorded_simulation_semantics=dict(semantics),
            replay_env=REPLAY_ENV_RECORDED,
        )

    if simulator_id not in (CURRENT_SIMULATOR_ID, LEGACY_SIMULATOR_ID):
        raise ValueError(f"Unsupported replay simulator_id: {simulator_id!r}")

    semantics = header.get("simulation_semantics")
    if not isinstance(semantics, dict):
        raise ValueError("Replay simulation_semantics must be present as an object")
    collision_model = _validate_collision_model(semantics.get("collision_model"))
    semantics = dict(semantics)
    semantics["collision_model"] = collision_model

    if simulator_id == LEGACY_SIMULATOR_ID and collision_model != collision.COLLISION_MODEL_RECT:
        raise ValueError("ha2_env_legacy replays only support collision_model='rect'")

    return ReplaySimulatorConfig(
        simulator_id=simulator_id,
        simulator_version=str(header.get("simulator_version", header.get("env_version", ""))),
        simulation_semantics=semantics,
        recorded_simulator_id=simulator_id,
        recorded_simulation_semantics=dict(semantics),
        replay_env=REPLAY_ENV_RECORDED,
    )


def resolve_replay_simulator_config(
    header: dict[str, Any],
    replay_env: str = REPLAY_ENV_RECORDED,
) -> ReplaySimulatorConfig:
    if replay_env not in REPLAY_ENV_CHOICES:
        raise ValueError(
            f"Unsupported replay_env {replay_env!r}; expected one of {REPLAY_ENV_CHOICES}"
        )

    recorded = recorded_replay_simulator_config(header)
    if replay_env == REPLAY_ENV_RECORDED:
        return recorded

    if replay_env == REPLAY_ENV_CURRENT:
        semantics = dict(recorded.recorded_simulation_semantics)
        return ReplaySimulatorConfig(
            simulator_id=CURRENT_SIMULATOR_ID,
            simulator_version=ENV_VERSION,
            simulation_semantics=semantics,
            recorded_simulator_id=recorded.recorded_simulator_id,
            recorded_simulation_semantics=dict(recorded.recorded_simulation_semantics),
            replay_env=replay_env,
        )

    semantics = {"collision_model": collision.COLLISION_MODEL_RECT}
    return ReplaySimulatorConfig(
        simulator_id=LEGACY_SIMULATOR_ID,
        simulator_version=_simulator_version(LEGACY_SIMULATOR_ID),
        simulation_semantics=semantics,
        recorded_simulator_id=recorded.recorded_simulator_id,
        recorded_simulation_semantics=dict(recorded.recorded_simulation_semantics),
        replay_env=replay_env,
    )


def replay_env_override_warning(config: ReplaySimulatorConfig) -> str | None:
    if config.replay_env == REPLAY_ENV_RECORDED:
        return None
    if (
        config.simulator_id == config.recorded_simulator_id
        and config.simulation_semantics == config.recorded_simulation_semantics
    ):
        return None
    return (
        "Replay simulator override: using "
        f"{config.simulator_id} {config.simulation_semantics}, recorded "
        f"{config.recorded_simulator_id} {config.recorded_simulation_semantics}."
    )


def make_replay_env(
    header: dict[str, Any],
    *,
    replay_env: str = REPLAY_ENV_RECORDED,
    render_mode: str | None = None,
    auto_render: bool = False,
):
    config = resolve_replay_simulator_config(header, replay_env=replay_env)
    kwargs = {
        "render_mode": render_mode,
        "training_profile": header.get("training_profile", "legacy"),
        "reward_profile": header.get("reward_profile", "combat_default"),
        "pressure_profile": header.get("pressure_profile", "normal"),
        "max_episode_steps": header.get("max_episode_steps"),
    }

    if config.simulator_id == CURRENT_SIMULATOR_ID:
        kwargs["auto_render"] = auto_render
        kwargs["collision_model"] = config.simulation_semantics["collision_model"]
        return HeliAttack2Env(**kwargs)

    from ha2_env_legacy import HeliAttack2Env as LegacyHeliAttack2Env

    if render_mode is not None:
        kwargs["auto_render"] = auto_render
    return LegacyHeliAttack2Env(**kwargs)


class JsonlReplayWriter:
    def __init__(self, path: str | Path, env: HeliAttack2Env, seed: int, initial_obs):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.file = self.path.open("w", encoding="utf-8")
        base_env = env.unwrapped
        simulator_id = _simulator_id_for_env(env)
        simulation_semantics = _simulation_semantics_for_env(env)
        header = {
            "type": "header",
            "schema_version": SCHEMA_VERSION,
            "env_name": ENV_NAME,
            "env_version": _simulator_version(simulator_id),
            "simulator_id": simulator_id,
            "simulator_version": _simulator_version(simulator_id),
            "simulation_semantics": simulation_semantics,
            "training_profile": base_env.training_profile,
            "reward_profile": getattr(base_env, "reward_profile", "combat_default"),
            "pressure_profile": getattr(base_env, "pressure_profile", "normal"),
            "max_episode_steps": base_env.max_episode_steps,
            "control_mode": getattr(env, "control_mode", CONTROL_MODE_FULL),
            "policy_action_space_nvec": policy_action_space_nvec(env),
            "sim_action_space_nvec": sim_action_space_nvec(env),
            "seed": int(seed),
            "initial_observation": to_jsonable(initial_obs),
            "initial_state": base_env.get_state(),
            "initial_state_hash": base_env.state_hash(),
            "action_space": {
                "type": env.action_space.__class__.__name__,
                "nvec": to_jsonable(env.action_space.nvec),
            },
        }
        self.write(header)

    def write(self, record: dict[str, Any]) -> None:
        self.file.write(json.dumps(to_jsonable(record), separators=(",", ":")) + "\n")
        self.file.flush()

    def append_step(
        self,
        env: HeliAttack2Env,
        action,
        obs,
        reward,
        terminated,
        truncated,
        info,
        *,
        policy_action=None,
        full_action=None,
        control_mode: str | None = None,
    ):
        policy_action = get_policy_action(env, action if policy_action is None else policy_action)
        full_action = get_full_action(env, action if full_action is None else full_action)
        control_mode = control_mode or getattr(env, "control_mode", CONTROL_MODE_FULL)
        base_env = env.unwrapped
        self.write(
            {
                "type": "step",
                "tick": base_env.tick,
                "action": [int(v) for v in full_action],
                "reward": float(reward),
                "terminated": bool(terminated),
                "truncated": bool(truncated),
                "observation": to_jsonable(obs),
                "state_hash": base_env.state_hash(),
                "debug": {
                    "control_mode": control_mode,
                    "reward_profile": getattr(base_env, "reward_profile", "combat_default"),
                    "pressure_profile": getattr(base_env, "pressure_profile", "normal"),
                    "policy_action": policy_action,
                    "full_action": full_action,
                    "reward_breakdown": info.get("reward_breakdown"),
                    "camera": info.get("camera"),
                    "contact": info.get("contact"),
                    "grounded": info.get("grounded"),
                    "gun": info.get("gun"),
                    "gun_event": info.get("gun_event"),
                    "active_bullets": info.get("active_bullets"),
                    "player_health": info.get("player_health"),
                    "combat": info.get("combat"),
                    "enemy_event": info.get("enemy_event"),
                    "active_enemy_bullets": info.get("active_enemy_bullets"),
                },
            }
        )

    def close(self) -> None:
        self.file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


def load_replay(path: str | Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    header = None
    steps: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("type") == "header":
                header = record
            elif record.get("type") == "step":
                steps.append(record)
    if header is None:
        raise ValueError(f"{path} does not contain a replay header")
    return header, steps


def verify_replay_file(path: str | Path, *, replay_env: str = REPLAY_ENV_RECORDED) -> int:
    header, steps = load_replay(path)
    if header.get("schema_version") != SCHEMA_VERSION:
        raise AssertionError(f"Unsupported replay schema: {header.get('schema_version')}")

    env = make_replay_env(header, replay_env=replay_env, render_mode=None)
    try:
        obs, _info = env.reset(seed=int(header["seed"]))
        if to_jsonable(obs) != header["initial_observation"]:
            raise AssertionError("Initial observation mismatch")
        if env.state_hash() != header["initial_state_hash"]:
            raise AssertionError("Initial state hash mismatch")

        for index, step in enumerate(steps, start=1):
            obs, reward, terminated, truncated, _info = env.step(step["action"])
            if env.state_hash() != step["state_hash"]:
                raise AssertionError(
                    f"State hash mismatch at replay step {index}: "
                    f"{env.state_hash()} != {step['state_hash']}"
                )
            if float(reward) != float(step["reward"]):
                raise AssertionError(f"Reward mismatch at replay step {index}")
            if bool(terminated) != bool(step["terminated"]):
                raise AssertionError(f"Terminated flag mismatch at replay step {index}")
            if bool(truncated) != bool(step["truncated"]):
                raise AssertionError(f"Truncated flag mismatch at replay step {index}")
    finally:
        env.close()

    return len(steps)
