from __future__ import annotations

import argparse
import re
from dataclasses import asdict, dataclass
from typing import Any

from ha2_env import (
    CONTROL_MODE_FULL,
    CONTROL_MODES,
    PRESSURE_PROFILE_NORMAL,
    PRESSURE_PROFILES,
    REWARD_PROFILES,
    TRAINING_PROFILES,
)


DEFAULT_TRAINING_PROFILE = "combat_v1"
DEFAULT_CONTROL_MODE = CONTROL_MODE_FULL
DEFAULT_REWARD_PROFILE = "combat_default"
DEFAULT_PRESSURE_PROFILE = PRESSURE_PROFILE_NORMAL
DEFAULT_MAX_EPISODE_STEPS = 1800
DEFAULT_SKIP_INTRO = True

_HUMAN_COUNT_SUFFIXES = {
    "k": 1_000,
    "m": 1_000_000,
}


def parse_human_count(value: int | str) -> int:
    if isinstance(value, int):
        return value
    text = str(value).strip().replace("_", "")
    match = re.fullmatch(r"(\d+)([kKmM]?)", text)
    if match is None:
        raise argparse.ArgumentTypeError(
            f"Expected an integer or a suffix form like 500k/1M, got {value!r}"
        )
    amount = int(match.group(1))
    suffix = match.group(2).lower()
    if suffix:
        amount *= _HUMAN_COUNT_SUFFIXES[suffix]
    return amount


@dataclass(frozen=True)
class RuntimeConfig:
    training_profile: str = DEFAULT_TRAINING_PROFILE
    control_mode: str = DEFAULT_CONTROL_MODE
    reward_profile: str = DEFAULT_REWARD_PROFILE
    pressure_profile: str = DEFAULT_PRESSURE_PROFILE
    max_episode_steps: int | None = DEFAULT_MAX_EPISODE_STEPS
    skip_intro: bool = DEFAULT_SKIP_INTRO

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


RUNTIME_ARG_FIELDS = (
    "training_profile",
    "control_mode",
    "reward_profile",
    "pressure_profile",
    "max_episode_steps",
    "skip_intro",
)


def add_runtime_config_args(
    parser: argparse.ArgumentParser,
    *,
    training_profile_default: str | None = DEFAULT_TRAINING_PROFILE,
    control_mode_default: str | None = DEFAULT_CONTROL_MODE,
    reward_profile_default: str | None = DEFAULT_REWARD_PROFILE,
    pressure_profile_default: str | None = DEFAULT_PRESSURE_PROFILE,
    max_episode_steps_default: int | None = DEFAULT_MAX_EPISODE_STEPS,
    skip_intro_default: bool = DEFAULT_SKIP_INTRO,
) -> None:
    parser.add_argument(
        "--training-profile",
        choices=sorted(TRAINING_PROFILES),
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--control-mode",
        choices=sorted(CONTROL_MODES),
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--reward-profile",
        choices=sorted(REWARD_PROFILES),
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--pressure-profile",
        choices=sorted(PRESSURE_PROFILES),
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--max-episode-steps",
        type=parse_human_count,
        default=argparse.SUPPRESS,
    )
    parser.add_argument("--skip-intro", dest="skip_intro", action="store_true", default=argparse.SUPPRESS)
    parser.add_argument("--no-skip-intro", dest="skip_intro", action="store_false", default=argparse.SUPPRESS)
    parser.set_defaults(
        _runtime_defaults=RuntimeConfig(
            training_profile=training_profile_default,
            control_mode=control_mode_default,
            reward_profile=reward_profile_default,
            pressure_profile=pressure_profile_default,
            max_episode_steps=max_episode_steps_default,
            skip_intro=skip_intro_default,
        )
    )


def resolve_runtime_config(
    args: argparse.Namespace,
    experiment_config: dict[str, Any] | None = None,
) -> RuntimeConfig:
    defaults = getattr(args, "_runtime_defaults", RuntimeConfig())
    config = experiment_config or {}
    values: dict[str, Any] = {}
    for field in RUNTIME_ARG_FIELDS:
        if hasattr(args, field):
            values[field] = getattr(args, field)
        elif field in config:
            values[field] = config[field]
        else:
            values[field] = getattr(defaults, field)
    return RuntimeConfig(
        training_profile=str(values["training_profile"]),
        control_mode=str(values["control_mode"]),
        reward_profile=str(values["reward_profile"]),
        pressure_profile=str(values["pressure_profile"]),
        max_episode_steps=(
            None
            if values["max_episode_steps"] is None
            else int(values["max_episode_steps"])
        ),
        skip_intro=bool(values["skip_intro"]),
    )


def runtime_env_kwargs(config: RuntimeConfig) -> dict[str, Any]:
    return config.as_dict()


def explicit_runtime_overrides(
    args: argparse.Namespace,
    experiment_config: dict[str, Any] | None,
    resolved: RuntimeConfig,
) -> dict[str, tuple[Any, Any]]:
    config = experiment_config or {}
    overrides: dict[str, tuple[Any, Any]] = {}
    for field in RUNTIME_ARG_FIELDS:
        if hasattr(args, field) and field in config:
            cli_value = getattr(resolved, field)
            config_value = config[field]
            if cli_value != config_value:
                overrides[field] = (config_value, cli_value)
    return overrides
