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


def test_scripted_fire_trace_summary(tmp_path):
    result = record_scenario(
        "fire_right_60",
        tmp_path,
        write_screenshots=False,
    )

    assert result.replay_path.exists()
    assert result.replay_verified is True
    assert verify_replay_file(result.replay_path) == result.frame_count

    summary = result.summary_path.read_text(encoding="utf-8")
    assert "scenario=fire_right_60" in summary
    assert "gun_shots=12" in summary
    assert "total_bullets_spawned=12" in summary
    assert "first_bullet_initial=" in summary


def test_scripted_fire_at_heli_trace_summary(tmp_path):
    result = record_scenario(
        "fire_at_heli_180",
        tmp_path,
        write_screenshots=False,
    )

    assert result.replay_verified is True
    assert verify_replay_file(result.replay_path) == result.frame_count

    summary = result.summary_path.read_text(encoding="utf-8")
    assert "scenario=fire_at_heli_180" in summary
    assert "hits=" in summary
    assert "score=" in summary


def test_scripted_fire_at_heli_deterministic(tmp_path):
    first = record_scenario(
        "fire_at_heli_180",
        tmp_path / "first",
        write_screenshots=False,
    )
    second = record_scenario(
        "fire_at_heli_180",
        tmp_path / "second",
        write_screenshots=False,
    )

    assert first.final_hash == second.final_hash
    assert first.replay_path.read_text(encoding="utf-8") == second.replay_path.read_text(
        encoding="utf-8"
    )


def test_scripted_heli_shoots_hero_trace_summary(tmp_path):
    result = record_scenario(
        "heli_shoots_hero_240",
        tmp_path,
        write_screenshots=False,
    )

    assert result.replay_verified is True
    assert verify_replay_file(result.replay_path) == result.frame_count

    summary = result.summary_path.read_text(encoding="utf-8")
    assert "scenario=heli_shoots_hero_240" in summary
    assert "enemy_bullets_spawned=" in summary
    assert "enemy_bullet_hits=1" in summary
    assert "initial_player_health=100" in summary
    assert "final_player_health=90" in summary
    assert "first_enemy_damage_frame=240" in summary
    assert "first_enemy_damage_bullet_id=12" in summary


def test_scripted_kill_heli_respawn_trace_summary(tmp_path):
    result = record_scenario(
        "kill_heli_respawn_600",
        tmp_path,
        write_screenshots=False,
    )

    assert result.replay_verified is True
    assert verify_replay_file(result.replay_path) == result.frame_count

    summary = result.summary_path.read_text(encoding="utf-8")
    assert "scenario=kill_heli_respawn_600" in summary
    assert "helis_killed=0" not in summary
    assert "killed_enemy_ids=[]" not in summary
    assert "spawned_enemy_ids=[]" not in summary
    assert "first_heli_death_frame=None" not in summary
    assert "replacement_heli_spawn_frame=None" not in summary
    assert "active_enemies=1" in summary
