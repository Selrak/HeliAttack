from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from ha2_env import ENV_NAME, ENV_VERSION, HeliAttack2Env


SCHEMA_VERSION = 1


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


class JsonlReplayWriter:
    def __init__(self, path: str | Path, env: HeliAttack2Env, seed: int, initial_obs):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.file = self.path.open("w", encoding="utf-8")
        header = {
            "type": "header",
            "schema_version": SCHEMA_VERSION,
            "env_name": ENV_NAME,
            "env_version": ENV_VERSION,
            "training_profile": env.training_profile,
            "max_episode_steps": env.max_episode_steps,
            "seed": int(seed),
            "initial_observation": to_jsonable(initial_obs),
            "initial_state": env.get_state(),
            "initial_state_hash": env.state_hash(),
            "action_space": {
                "type": env.action_space.__class__.__name__,
                "nvec": to_jsonable(env.action_space.nvec),
            },
        }
        self.write(header)

    def write(self, record: dict[str, Any]) -> None:
        self.file.write(json.dumps(to_jsonable(record), separators=(",", ":")) + "\n")
        self.file.flush()

    def append_step(self, env: HeliAttack2Env, action, obs, reward, terminated, truncated, info):
        self.write(
            {
                "type": "step",
                "tick": env.tick,
                "action": [int(v) for v in action],
                "reward": float(reward),
                "terminated": bool(terminated),
                "truncated": bool(truncated),
                "observation": to_jsonable(obs),
                "state_hash": env.state_hash(),
                "debug": {
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


def verify_replay_file(path: str | Path) -> int:
    header, steps = load_replay(path)
    if header.get("schema_version") != SCHEMA_VERSION:
        raise AssertionError(f"Unsupported replay schema: {header.get('schema_version')}")

    env = HeliAttack2Env(
        render_mode=None,
        training_profile=header.get("training_profile", "legacy"),
        max_episode_steps=header.get("max_episode_steps"),
    )
    obs, _info = env.reset(seed=int(header["seed"]))
    if to_jsonable(obs) != header["initial_observation"]:
        raise AssertionError("Initial observation mismatch")
    if env.state_hash() != header["initial_state_hash"]:
        raise AssertionError("Initial state hash mismatch")

    try:
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
