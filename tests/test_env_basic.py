from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pygame
import pytest

from ha2_env import HA2_HUD_FONT_PATH, HeliAttack2Env
from scripts.play_human import action_from_keys


IDLE_ACTION = [1, 0, 0, 0, 0, 0]


def step_until_default_heli_spawn(env: HeliAttack2Env, max_steps: int = 120):
    for _ in range(max_steps):
        _obs, _reward, _terminated, _truncated, info = env.step(IDLE_ACTION)
        if info["enemy_event"]["spawned_enemy_ids"]:
            return info
    raise AssertionError("default Heli did not spawn")


def test_import_reset_step():
    env = HeliAttack2Env(render_mode=None)
    obs, info = env.reset(seed=123)
    assert obs.shape == (4,)
    assert "state_hash" in info
    obs, reward, terminated, truncated, info = env.step([1, 0, 0, 0])
    assert obs.shape == (4,)
    assert reward == 0.1
    assert terminated is False
    assert truncated is False
    assert "state_hash" in info
    env.close()


def test_spaces_sanity():
    env = HeliAttack2Env(render_mode=None)
    assert env.action_space.nvec.tolist() == [3, 2, 2, 2, 32, 2]
    obs, _info = env.reset(seed=0)
    assert env.observation_space.contains(obs)
    env.close()


def test_deterministic_fixed_actions():
    actions = [
        [1, 0, 0, 0],
        [2, 0, 0, 0],
        [2, 1, 0, 0],
        [2, 1, 0, 0],
        [1, 0, 0, 1],
        [0, 0, 1, 0],
    ] * 20

    hashes = []
    for _ in range(2):
        env = HeliAttack2Env(render_mode=None)
        env.reset(seed=42)
        for action in actions:
            env.step(action)
        hashes.append(env.state_hash())
        env.close()

    assert hashes[0] == hashes[1]


def test_rgb_array_smoke():
    env = HeliAttack2Env(render_mode="rgb_array", auto_render=False)
    env.reset(seed=0)
    frame = env.render()
    assert isinstance(frame, np.ndarray)
    assert frame.shape == (320, 450, 3)
    env.close()


def test_player_health_hud_uses_health_value():
    env = HeliAttack2Env(render_mode="rgb_array", auto_render=False)
    env.reset(seed=0)
    full_health_frame = env.render()
    env.health = 50
    half_health_frame = env.render()

    health_region = np.s_[
        0:80,
        431:450,
        :,
    ]
    assert not np.array_equal(
        full_health_frame[health_region],
        half_health_frame[health_region],
    )
    env.close()


@pytest.mark.parametrize(
    "training_profile",
    ["legacy", "combat_v1", "combat_bullets_v1"],
)
def test_health_depletion_terminates_universally(training_profile):
    env = HeliAttack2Env(
        render_mode=None,
        training_profile=training_profile,
        spawn_default_heli=False,
        skip_intro=True,
    )
    env.reset(seed=0)
    env.health = -5

    _obs, _reward, terminated, truncated, info = env.step(IDLE_ACTION)

    assert terminated is True
    assert truncated is False
    assert env.health == 0
    assert info["player_health"] == 0
    assert info["termination_reason"] == "player_death"
    env.close()


@pytest.mark.parametrize(
    ("side", "start_x", "action"),
    [
        ("left", 0.0, [0, 0, 0, 0, 0, 0]),
        ("right", None, [2, 0, 0, 0, 0, 0]),
    ],
)
def test_lateral_world_bounds_are_collision_bounds_not_fall_death(
    side,
    start_x,
    action,
):
    env = HeliAttack2Env(
        render_mode=None,
        training_profile="combat_v1",
        spawn_default_heli=False,
        skip_intro=True,
    )
    env.reset(seed=0)
    if start_x is None:
        env._x = env.map_pixel_width - env.width
    else:
        env._x = start_x
    env.xspeed = -6 if action[0] == 0 else 6

    info = {}
    terminated = truncated = False
    for _ in range(12):
        _obs, _reward, terminated, truncated, info = env.step(action)
        assert terminated is False
        assert truncated is False
        assert info["termination_reason"] != "fall"

    left, _top, right, _bottom = env._player_hit_rect()
    if side == "left":
        assert left >= -1.0
        assert info["contact"]["wall"] == "left"
    else:
        assert right <= env.map_pixel_width
        assert info["contact"]["wall"] == "right"
    env.close()


def test_play_human_accepts_zqsd_layout():
    class FakeKeys:
        def __init__(self, pressed):
            self.pressed = set(pressed)

        def __getitem__(self, key):
            return key in self.pressed

    env = HeliAttack2Env(render_mode=None)
    env.reset(seed=0)

    left_action = action_from_keys(FakeKeys({pygame.K_q}), env)
    jump_action = action_from_keys(FakeKeys({pygame.K_z}), env)
    duck_action = action_from_keys(FakeKeys({pygame.K_s}), env)

    assert left_action[0] == 0
    assert jump_action[1] == 1
    assert duck_action[2] == 1
    env.close()


def test_debug_overlay_uses_side_panel_not_game_area():
    env = HeliAttack2Env(render_mode="rgb_array", auto_render=False)
    env.reset(seed=0)
    game_frame = env.render()
    debug_frame = env.render(debug_overlay=True, debug_lines=["debug panel smoke"])

    assert debug_frame.shape[0] == game_frame.shape[0]
    assert debug_frame.shape[1] > game_frame.shape[1]
    assert np.array_equal(debug_frame[:, : game_frame.shape[1], :], game_frame)
    env.close()


def test_heli_render_asset_omits_hidden_hit_shape():
    env = HeliAttack2Env(render_mode="rgb_array", auto_render=False)
    env.reset(seed=0)
    env.render()
    heli = env.images["heli1"]
    assert heli is not None
    pixels = pygame.surfarray.array3d(heli)
    bright_green = (
        (pixels[:, :, 0] < 80)
        & (pixels[:, :, 1] > 220)
        & (pixels[:, :, 2] < 120)
    )
    assert bright_green.mean() < 0.05
    env.close()


def test_headless_speed_smoke():
    env = HeliAttack2Env(render_mode=None)
    env.reset(seed=0)
    start = time.perf_counter()
    steps = 2_000
    for _ in range(steps):
        env.step([1, 0, 0, 0])
    elapsed = time.perf_counter() - start
    steps_per_sec = steps / elapsed
    assert steps_per_sec > 1_000
    env.close()


def test_machinegun_deterministic_hold_fire():
    def run_once():
        env = HeliAttack2Env(render_mode=None, skip_intro=True)
        env.reset(seed=123)
        for _ in range(60):
            env.step([1, 0, 0, 0, 0, 0])
        for _ in range(60):
            env.step([1, 0, 0, 0, 0, 1])
        state = env.get_state()
        state_hash = env.state_hash()
        env.close()
        return state, state_hash

    first_state, first_hash = run_once()
    second_state, second_hash = run_once()

    assert first_hash == second_hash
    assert first_state["gun"]["player_shot_attempts"] == 12
    assert first_state["gun"]["total_bullets_spawned"] == 12


def test_machinegun_bullet_moves_rightward():
    env = HeliAttack2Env(render_mode=None)
    env.reset(seed=0)
    env._add_bullet(100.0, 100.0, 0.0, 10)
    env.step([1, 0, 0, 0, 0, 0])
    assert len(env.bullets) == 1
    bullet = env.bullets[0]
    assert bullet["x"] == 108.0
    assert bullet["y"] == 100.0
    env.close()


def test_machinegun_bullet_removed_on_solid_tile():
    env = HeliAttack2Env(render_mode=None)
    env.reset(seed=0)
    env._add_bullet(25.0, 700.0, 0.0, 10)
    env.step([1, 0, 0, 0, 0, 0])
    assert env.bullets == []
    env.close()


def test_player_bullet_damages_heli():
    env = HeliAttack2Env(render_mode=None)
    env.reset(seed=0)
    env.enemies = []
    env.next_enemy_id = 1
    env._add_enemy(health=300, x=150.0, y=100.0)
    env._add_bullet(100.0, 100.0, 0.0, 10)
    env.step([1, 0, 0, 0, 0, 0])
    assert env.bullets == []
    assert env.enemies[0]["health"] == 290
    assert env.hits == 1
    assert env.score == 10
    env.close()


def test_heli_death_respawns_replacement_once():
    env = HeliAttack2Env(render_mode=None, spawn_default_heli=False)
    env.reset(seed=0)
    env._add_enemy(health=10, x=150.0, y=100.0)
    before = env.state_hash()
    env._add_bullet(100.0, 100.0, 0.0, 10)

    env.step(IDLE_ACTION)

    assert env.last_enemy_event["killed_enemy_ids"] == [1]
    assert env.last_enemy_event["spawned_enemy_ids"] == [2]
    assert env.helis == 1
    assert env.rthelis == 1
    assert env.total_enemies_spawned == 2
    assert len(env.enemies) == 1
    assert env.enemies[0]["id"] == 2
    assert env.enemies[0]["health"] == 300
    assert env.state_hash() != before

    env.step(IDLE_ACTION)
    assert env.rthelis == 1
    assert env.helis == 1
    env.close()


def test_heli_death_can_disable_respawn():
    env = HeliAttack2Env(
        render_mode=None,
        spawn_default_heli=False,
        respawn_helis=False,
    )
    env.reset(seed=0)
    env._add_enemy(health=10, x=150.0, y=100.0)
    env._add_bullet(100.0, 100.0, 0.0, 10)

    env.step(IDLE_ACTION)

    assert env.last_enemy_event["killed_enemy_ids"] == [1]
    assert env.last_enemy_event["spawned_enemy_ids"] == []
    assert env.rthelis == 1
    assert env.enemies == []
    env.close()


def test_heli_death_respawn_deterministic():
    states = []
    hashes = []
    for _ in range(2):
        env = HeliAttack2Env(render_mode=None, spawn_default_heli=False)
        env.reset(seed=123)
        env._add_enemy(health=10, x=150.0, y=100.0)
        env._add_bullet(100.0, 100.0, 0.0, 10)
        env.step(IDLE_ACTION)
        states.append(env.get_state()["enemies"])
        hashes.append(env.state_hash())
        env.close()

    assert states[0] == states[1]
    assert hashes[0] == hashes[1]


def test_default_heli_deterministic():
    hashes = []
    enemy_states = []
    for _ in range(2):
        env = HeliAttack2Env(render_mode=None)
        env.reset(seed=123)
        for _ in range(80):
            env.step(IDLE_ACTION)
        hashes.append(env.state_hash())
        enemy_states.append(env.get_state()["enemies"])
        env.close()

    assert hashes[0] == hashes[1]
    assert enemy_states[0] == enemy_states[1]
    assert enemy_states[0][0]["type"] == "Heli"


def test_default_intro_spawns_heli_after_as_start_lifecycle():
    env = HeliAttack2Env(render_mode=None)
    env.reset(seed=0)
    assert env.enemies == []
    assert env.pending_default_heli is True
    assert env.intro_active is True
    assert env.skip_intro is False

    for _ in range(20):
        _obs, _reward, _terminated, _truncated, info = env.step(IDLE_ACTION)
        assert env.enemies == []
        assert info["contact"]["ground"] is False

    spawn_info = step_until_default_heli_spawn(env)
    assert spawn_info["intro_active"] is False
    assert env.default_heli_spawned is True
    assert env.pending_default_heli is False
    assert len(env.enemies) == 1
    env.close()


def test_hud_debug_info_and_exact_font_asset(monkeypatch):
    monkeypatch.setattr("ha2_env.load_high_score", lambda: 7)
    env = HeliAttack2Env(render_mode="rgb_array", auto_render=False)
    env.reset(seed=0)
    env.score = 12.9
    env.rthelis = 3
    env.hyperjump = 75
    env.render()

    info = env.get_debug_info()
    assert HA2_HUD_FONT_PATH.exists()
    assert env.images["hud_health"] is not None
    assert env.images["hud_health_base"] is not None
    assert env.images["hud_health_fill"] is not None
    assert env.images["hud_hyperjump_full"] is not None
    assert env.images["hud_hyperjump_base"] is not None
    assert env.images["hud_hyperjump_fill"] is not None
    assert env.images["hud_reload_full"] is not None
    assert env.images["hud_reload_base"] is not None
    assert env.images["hud_reload_fill"] is not None
    assert env.images["hud_reload_ready"] is not None
    assert env.images["hud_weapon_icon"] is not None
    assert info["elapsed_seconds"] == 0
    assert info["heli_count"] == 3
    assert info["display_score"] == 1200
    assert info["raw_high_score"] == 7
    assert info["display_high_score"] == 700
    assert info["hyperjump_fraction"] == 0.5
    assert info["reload_ready"] is True
    assert info["reload_fraction"] == 1.0
    assert info["hud_font_exact"] is True
    env.close()


def test_viewer_scripts_do_not_duplicate_normal_hud_drawing():
    forbidden = [
        "Health:",
        "HyperJump:",
        "Reload:",
        "Infinite x ",
        "hud_health",
        "hud_hyperjump",
        "hud_reload",
        "hud_weapon_icon",
    ]
    for script in [
        Path("scripts/play_human.py"),
        Path("scripts/watch_model.py"),
        Path("scripts/play_replay.py"),
    ]:
        text = script.read_text(encoding="utf-8")
        for needle in forbidden:
            assert needle not in text


def test_hud_font_fallback_does_not_crash(monkeypatch, tmp_path):
    monkeypatch.setattr("ha2_env.HA2_HUD_FONT_PATH", tmp_path / "missing.ttf")
    env = HeliAttack2Env(render_mode="rgb_array", auto_render=False)
    env.reset(seed=0)
    frame = env.render()
    info = env.get_debug_info()
    assert isinstance(frame, np.ndarray)
    assert info["hud_font_exact"] is False
    env.close()


def test_skip_intro_starts_on_ground_with_default_heli():
    env = HeliAttack2Env(render_mode=None, skip_intro=True)
    _obs, info = env.reset(seed=0)
    assert info["skip_intro"] is True
    assert info["intro_mode"] == "skip_intro"
    assert info["grounded"] is True
    assert env.intro_active is False
    assert env.pending_default_heli is False
    assert env.default_heli_spawned is True
    assert len(env.enemies) == 1
    env.close()


def test_default_heli_startup_has_no_large_vertical_dart():
    env = HeliAttack2Env(render_mode=None, skip_intro=True)
    env.reset(seed=0)
    assert env.default_heli_spawned is True

    y_values = [float(env.enemies[0]["y"])]
    for _ in range(20):
        env.step(IDLE_ACTION)
        y_values.append(float(env.enemies[0]["y"]))

    assert min(y_values) >= 300.0
    assert max(abs(b - a) for a, b in zip(y_values, y_values[1:])) < 50.0
    env.close()


def test_heli_gun_rotation_changes_toward_player():
    env = HeliAttack2Env(render_mode=None)
    env.reset(seed=0)
    step_until_default_heli_spawn(env)
    before = env.enemies[0]["gun_rotation"]
    for _ in range(5):
        env.step(IDLE_ACTION)
    after = env.enemies[0]["gun_rotation"]
    assert after != before
    assert env.enemies[0]["gun_target_rotation"] != 0.0
    env.close()


def test_heli_fires_enemy_bullets_deterministically():
    def run_once():
        env = HeliAttack2Env(render_mode=None)
        env.reset(seed=7)
        for _ in range(80):
            env.step(IDLE_ACTION)
        state = env.get_state()
        state_hash = env.state_hash()
        env.close()
        return state, state_hash

    first_state, first_hash = run_once()
    second_state, second_hash = run_once()

    assert first_hash == second_hash
    assert first_state["combat"]["total_enemy_bullets_spawned"] > 0
    assert first_state["combat"]["total_enemy_bullets_spawned"] == second_state["combat"]["total_enemy_bullets_spawned"]


def test_enemy_bullet_moves_at_as_speed():
    env = HeliAttack2Env(render_mode=None, spawn_default_heli=False)
    env.reset(seed=0)
    env._add_enemy_bullet(100.0, 100.0, 0.0, 7.0)
    env.step([1, 0, 0, 0, 0, 0])
    assert len(env.enemy_bullets) == 1
    bullet = env.enemy_bullets[0]
    assert bullet["x"] == 107.0
    assert bullet["y"] == 100.0
    env.close()


def test_enemy_bullet_hit_damages_player_and_removes_bullet():
    env = HeliAttack2Env(render_mode=None, spawn_default_heli=False)
    env.reset(seed=0)
    left, top, right, bottom = env._player_hit_rect()
    env._add_enemy_bullet((left + right) / 2, (top + bottom) / 2, 0.0, 0.0)
    env.step([1, 0, 0, 0, 0, 0])
    assert env.health == 90
    assert env.enemy_bullets == []
    assert env.enemy_bullet_hits == 1
    assert env.last_enemy_event["player_damage"] == 10
    assert env.last_player_damage_tick == 1
    env.close()


def test_player_health_affects_state_hash():
    env = HeliAttack2Env(render_mode=None, spawn_default_heli=False)
    env.reset(seed=0)
    before = env.state_hash()
    env.health -= 10
    after = env.state_hash()
    assert before != after
    env.close()


def test_enemy_bullet_state_affects_state_hash():
    env = HeliAttack2Env(render_mode=None, spawn_default_heli=False)
    env.reset(seed=0)
    before = env.state_hash()
    env._add_enemy_bullet(100.0, 100.0, 0.0, 7.0)
    after = env.state_hash()
    assert before != after
    env.close()


def test_enemy_state_affects_state_hash():
    env = HeliAttack2Env(render_mode=None, spawn_default_heli=False)
    env.reset(seed=0)
    env._add_enemy(health=300, x=150.0, y=100.0)
    before = env.state_hash()
    env.enemies[0]["health"] -= 10
    after = env.state_hash()
    assert before != after
    env.close()


def test_machinegun_ffdec_barrel_offset_zero_rotation():
    env = HeliAttack2Env(render_mode=None)
    env.reset(seed=0)
    barrel_x, barrel_y = env._machinegun_visual_barrel_world_pos(0.0)
    assert abs((barrel_x - env._x) - 46.7) < 1e-9
    assert abs((barrel_y - env._y) - 21.6) < 1e-9
    env.close()
