from __future__ import annotations

import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_HIGH_SCORE_PATH = REPO_ROOT / "state" / "ha2_high_scores.json"


def raw_score(raw_score_value: float | int) -> int:
    return int(math.floor(float(raw_score_value)))


def display_score(raw_score_value: float | int) -> int:
    return raw_score(raw_score_value) * 100


def display_high_score(raw_high_score: int) -> int:
    return int(raw_high_score) * 100


def load_high_score(path: str | Path | None = None) -> int:
    score_path = Path(path) if path is not None else DEFAULT_HIGH_SCORE_PATH
    if not score_path.exists():
        return 0
    try:
        data: dict[str, Any] = json.loads(score_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0
    ha2 = data.get("ha2", {})
    try:
        return max(0, int(ha2.get("raw_high_score", 0)))
    except (TypeError, ValueError):
        return 0


def update_high_score(raw_score_value: float | int, path: str | Path | None = None) -> int:
    score_path = Path(path) if path is not None else DEFAULT_HIGH_SCORE_PATH
    current = load_high_score(score_path)
    candidate = raw_score(raw_score_value)
    if candidate <= current:
        return current

    score_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "ha2": {
            "raw_high_score": candidate,
            "display_high_score": display_high_score(candidate),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    }
    temp_path = score_path.with_name(f"{score_path.name}.tmp")
    temp_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp_path, score_path)
    return candidate
