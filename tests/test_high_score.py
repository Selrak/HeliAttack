from __future__ import annotations

import json

from ha2_high_score import (
    display_high_score,
    display_score,
    load_high_score,
    update_high_score,
)


def test_display_score_uses_floor_times_100():
    assert display_score(12.9) == 1200
    assert display_score(0) == 0


def test_high_score_missing_file_loads_zero(tmp_path):
    assert load_high_score(tmp_path / "missing.json") == 0


def test_high_score_updates_only_when_higher(tmp_path):
    path = tmp_path / "ha2_high_scores.json"

    assert update_high_score(3.9, path) == 3
    assert update_high_score(2, path) == 3
    assert update_high_score(5, path) == 5

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["ha2"]["raw_high_score"] == 5
    assert data["ha2"]["display_high_score"] == display_high_score(5)
    assert isinstance(data["ha2"]["updated_at"], str)
