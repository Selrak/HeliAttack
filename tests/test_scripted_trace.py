from __future__ import annotations

from ha2_replay import verify_replay_file
from scripts.record_scripted_trace import SCENARIOS, record_scenario


def test_scripted_trace_generation(tmp_path):
    result = record_scenario(
        "idle_120",
        tmp_path,
        frame_count=12,
        selected_frames=(0, 1, 2, 10, 12),
        write_screenshots=False,
    )

    assert "idle_120" in SCENARIOS
    assert result.replay_path.exists()
    assert result.summary_path.exists()
    assert result.frame_count == 12
    assert result.replay_verified is True
    assert verify_replay_file(result.replay_path) == 12

    summary = result.summary_path.read_text(encoding="utf-8")
    assert "scenario=idle_120" in summary
    assert "frame_count=12" in summary
    assert "frame_0010=" in summary


def test_scripted_trace_deterministic(tmp_path):
    first = record_scenario(
        "walk_right_120",
        tmp_path / "first",
        frame_count=20,
        write_screenshots=False,
    )
    second = record_scenario(
        "walk_right_120",
        tmp_path / "second",
        frame_count=20,
        write_screenshots=False,
    )

    assert first.final_hash == second.final_hash
    assert first.replay_path.read_text(encoding="utf-8") == second.replay_path.read_text(
        encoding="utf-8"
    )
    assert first.summary_path.read_text(encoding="utf-8") == second.summary_path.read_text(
        encoding="utf-8"
    )
