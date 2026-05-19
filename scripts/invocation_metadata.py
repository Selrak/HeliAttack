from __future__ import annotations

import os
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable

from scripts.experiment_utils import collect_git_info, write_json_file, write_text_file


DEFAULT_ENV_KEYS = (
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "HA2_TORCH_NUM_THREADS",
    "CUDA_VISIBLE_DEVICES",
)


def reconstruct_command_for_display(argv: Iterable[object]) -> str:
    """Return readable command text; original shell quoting cannot be recovered."""
    parts = [str(part) for part in argv]
    if os.name == "nt":
        return subprocess.list2cmdline(parts)
    return shlex.join(parts)


def argv_for_module(module_name: str, args_list: list[str] | None) -> list[str]:
    if args_list is None:
        return [str(part) for part in sys.argv]
    return [sys.executable, "-m", module_name, *[str(part) for part in args_list]]


def capture_invocation_metadata(
    script_name: str,
    argv: Iterable[object],
    cwd: Path | str,
    env_keys: Iterable[str] | None = None,
    repo_root: Path | None = None,
) -> dict[str, object]:
    argv_list = [str(part) for part in argv]
    selected_env = {
        key: os.environ[key]
        for key in (tuple(env_keys) if env_keys is not None else DEFAULT_ENV_KEYS)
        if key in os.environ
    }
    metadata: dict[str, object] = {
        "script_name": script_name,
        "argv": argv_list,
        "command": reconstruct_command_for_display(argv_list),
        "command_reconstruction_note": (
            "Best-effort reconstruction from argv; original shell text and quoting cannot be recovered."
        ),
        "cwd": str(Path(cwd)),
        "python_executable": sys.executable,
        "python_version": sys.version,
        "platform": f"{sys.platform}/{os.name}",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "environment": selected_env,
    }
    if repo_root is not None:
        try:
            metadata["git"] = collect_git_info(repo_root)
        except Exception as exc:
            metadata["git"] = {
                "available": "false",
                "note": f"git metadata unavailable: {exc}",
            }
    return metadata


def write_invocation_files(output_dir: Path, metadata: dict[str, object], prefix: str = "") -> None:
    output_dir = Path(output_dir)
    write_json_file(output_dir / f"{prefix}argv.json", metadata.get("argv", []), allow_overwrite=True)
    write_text_file(output_dir / f"{prefix}command.txt", str(metadata.get("command", "")) + "\n", allow_overwrite=True)
    write_json_file(output_dir / f"{prefix}invocation_metadata.json", metadata, allow_overwrite=True)


def write_resolved_config(output_dir: Path, config_dict: dict[str, object], filename: str = "resolved_config.json") -> None:
    write_json_file(Path(output_dir) / filename, config_dict, allow_overwrite=True)
