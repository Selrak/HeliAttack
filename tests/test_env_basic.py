from __future__ import annotations

import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pygame
import pytest

from ha2_env import HA2_HUD_FONT_PATH, HeliAttack2Env
from ha2_gui import (
    GUI_SPEED_FACTORS,
    GuiState,
    advance_post_death_visuals,
    handle_common_event,
    is_player_death_termination,
)
from ha2_sound import SOUND_MANIFEST_PATH, SoundPlayer, load_sound_manifest, loop_volumes_from_env
from scripts.play_human import action_from_keys


IDLE_ACTION = [1, 0, 0, 0, 0, 0]
FIRE_ACTION = [1, 0, 0, 0, 0, 1]
JUMP_ACTION = [1, 1, 0, 0, 0, 0]
BOOST_ACTION = [1, 0, 0, 1, 0, 0]


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


def test_sound_manifest_assets_exist():
    manifest = load_sound_manifest()

    assert SOUND_MANIFEST_PATH.exists()
    for required in ("sgun", "sheliboom", "shurt", "shjump", "sheli", "smusic"):
        assert manifest[required]["status"] == "implemented"
    assert {
        name
        for name, entry in manifest.items()
        if entry.get("status") == "implemented"
    } == {"sgun", "sheliboom", "shurt", "shjump", "sheli", "smusic"}
    for name, entry in manifest.items():
        asset = Path(entry["asset"])
        assert asset.exists(), name
        assert asset.stat().st_size > 0, name


def test_sound_player_disabled_does_not_initialize_audio():
    player = SoundPlayer(enabled=False)

    assert player.available is False
    player.play("sgun")
    player.play_events(["sgun", "sheliboom"])


def test_sound_player_handles_mixer_failure(monkeypatch):
    import pygame

    monkeypatch.setattr(pygame.mixer, "get_init", lambda: False)

    def fail_init():
        raise pygame.error("audio unavailable")

    monkeypatch.setattr(pygame.mixer, "init", fail_init)
    player = SoundPlayer(enabled=True)

    assert player.available is False
    assert "audio unavailable" in str(player.warning)


def test_sound_player_loop_methods_use_channels_without_restarting(monkeypatch):
    import pygame

    class FakeChannel:
        def __init__(self):
            self.stopped = False
            self.volumes = []

        def set_volume(self, volume):
            self.volumes.append(volume)

        def stop(self):
            self.stopped = True

    class FakeSound:
        def __init__(self, _path):
            self.channel = FakeChannel()
            self.play_calls = []
            self.volumes = []

        def set_volume(self, volume):
            self.volumes.append(volume)

        def play(self, loops=0):
            self.play_calls.append(loops)
            return self.channel

    fake_sounds = []

    def fake_sound(path):
        sound = FakeSound(path)
        fake_sounds.append(sound)
        return sound

    monkeypatch.setattr(pygame.mixer, "get_init", lambda: True)
    monkeypatch.setattr(pygame.mixer, "Sound", fake_sound)
    player = SoundPlayer(enabled=True)

    player.start_loop("smusic", volume=50)
    player.start_loop("smusic", volume=25)
    player.set_loop_volume("smusic", 10)
    player.sync_loop_volumes({"smusic": 50, "sheli": 0})

    music = player._sounds["smusic"]
    assert music.play_calls == [-1]
    assert music.channel.volumes[-1] == 0.5
    assert "smusic" in player._loop_channels
    assert "sheli" in player._loop_channels
    heli = player._sounds["sheli"]
    assert heli.play_calls == [-1]
    player.set_loop_volume("sheli", 75)
    assert heli.channel.volumes[-1] == 0.75
    player.stop_all()
    assert player._loop_channels == {}
    assert music.channel.stopped is True
    assert heli.channel.stopped is True


def test_loop_volumes_are_computed_viewer_side_from_existing_env_state():
    env = HeliAttack2Env(render_mode=None, spawn_default_heli=False, skip_intro=True)
    env.reset(seed=0)

    no_heli = loop_volumes_from_env(env)
    env._add_enemy(health=300, x=env._x + env.width / 2.0, y=env._y)
    close_heli = loop_volumes_from_env(env)
    env.enemies.clear()
    env._add_enemy(health=300, x=env._x + env.width / 2.0 + 800.0, y=env._y)
    far_heli = loop_volumes_from_env(env)
    env.last_terminated = True
    terminal = loop_volumes_from_env(env)

    assert no_heli == {"smusic": 50.0, "sheli": 0.0}
    assert close_heli["sheli"] == 75.0
    assert far_heli["sheli"] == 0.0
    assert terminal == {"smusic": 50.0, "sheli": 0.0}
    assert not hasattr(env, "sound_loop_volumes")
    env.close()


def test_headless_step_emits_machinegun_sound_event_without_audio_playback():
    env = HeliAttack2Env(render_mode=None, spawn_default_heli=False, skip_intro=True)
    env.reset(seed=0)

    _obs, _reward, _terminated, _truncated, _info = env.step(FIRE_ACTION)

    assert "sgun" in env.pop_sound_events()
    assert env.pop_sound_events() == []
    env.close()


def test_heli_destruction_emits_sheliboom_sound_event():
    env = HeliAttack2Env(render_mode=None, spawn_default_heli=False)
    env.reset(seed=0)
    env._add_enemy(health=10, x=150.0, y=100.0)
    env._add_bullet(100.0, 100.0, 0.0, 10)

    env.step(IDLE_ACTION)

    assert "sheliboom" in env.pop_sound_events()
    env.close()


def test_player_damage_emits_shurt_sound_event():
    env = HeliAttack2Env(render_mode=None, spawn_default_heli=False, skip_intro=True)
    env.reset(seed=0)
    env._add_enemy_bullet(env._x + env.width / 2.0, env._y + env.height / 2.0, 0.0, speed=0.0)

    env.step(IDLE_ACTION)

    assert "shurt" in env.pop_sound_events()
    env.close()


def test_hyperjump_emits_shjump_but_ordinary_movement_does_not():
    env = HeliAttack2Env(render_mode=None, spawn_default_heli=False, skip_intro=True)
    env.reset(seed=0)

    env.step(IDLE_ACTION)
    assert "shjump" not in env.pop_sound_events()
    env.step(JUMP_ACTION)
    assert "shjump" not in env.pop_sound_events()
    env.step(IDLE_ACTION)
    assert "shjump" not in env.pop_sound_events()

    env.hyperjump = 150
    env.jump = 0
    env.jump2 = 0
    env.hjump = 0
    env.boostK = 0
    env.step(BOOST_ACTION)

    assert "shjump" in env.pop_sound_events()
    env.close()


def test_player_damage_spawns_three_render_only_blood_effects():
    env = HeliAttack2Env(render_mode="rgb_array", auto_render=False, spawn_default_heli=False, skip_intro=True)
    env.reset(seed=0)
    before_health = env.health
    env._add_enemy_bullet(env._x + env.width / 2.0, env._y + env.height / 2.0, 0.0, speed=0.0)

    obs, reward, terminated, truncated, _info = env.step(IDLE_ACTION)

    blood_effects = [effect for effect in env.visual_effects if effect["type"] == "blood"]
    assert env.health == before_health - 10
    assert len(blood_effects) == 3
    assert [effect["pause"] for effect in blood_effects] == [0, 2, 4]
    assert obs.shape == env.observation_space.shape
    assert reward == 0.1
    assert terminated is False
    assert truncated is False
    frame = env.render()
    assert frame.shape == (320, 450, 3)
    env.close()


def test_blood_effects_do_not_affect_hash_outputs_or_gameplay_rng(monkeypatch):
    def run_once(disable_blood: bool):
        env = HeliAttack2Env(
            render_mode=None,
            training_profile="combat_v1",
            spawn_default_heli=False,
            skip_intro=True,
        )
        if disable_blood:
            monkeypatch.setattr(env, "_spawn_player_blood_effects", lambda: None)
        env.reset(seed=321)
        env._add_enemy_bullet(env._x + env.width / 2.0, env._y + env.height / 2.0, 0.0, speed=0.0)
        obs, reward, terminated, truncated, info = env.step(IDLE_ACTION)
        state_hash = env.state_hash()
        effects = [dict(effect) for effect in env.visual_effects]
        for _ in range(20):
            env.step(FIRE_ACTION)
        after_hash = env.state_hash()
        result = {
            "obs": obs,
            "reward": reward,
            "terminated": terminated,
            "truncated": truncated,
            "reward_breakdown": info["reward_breakdown"],
            "state_hash": state_hash,
            "after_hash": after_hash,
            "effects": effects,
        }
        env.close()
        return result

    with_blood = run_once(False)
    without_blood = run_once(True)

    assert np.array_equal(with_blood["obs"], without_blood["obs"])
    assert with_blood["reward"] == without_blood["reward"]
    assert with_blood["terminated"] == without_blood["terminated"]
    assert with_blood["truncated"] == without_blood["truncated"]
    assert with_blood["reward_breakdown"] == without_blood["reward_breakdown"]
    assert with_blood["state_hash"] == without_blood["state_hash"]
    assert with_blood["after_hash"] == without_blood["after_hash"]
    assert [effect["type"] for effect in with_blood["effects"]] == ["blood", "blood", "blood"]
    assert without_blood["effects"] == []


def test_sound_events_do_not_affect_state_hash_or_step_outputs(monkeypatch):
    def run_once(disable_sound_events: bool):
        env = HeliAttack2Env(
            render_mode=None,
            training_profile="combat_v1",
            spawn_default_heli=False,
            skip_intro=True,
        )
        if disable_sound_events:
            monkeypatch.setattr(env, "emit_sound_event", lambda _event_name: None)
        env.reset(seed=123)
        obs, reward, terminated, truncated, info = env.step(FIRE_ACTION)
        result = {
            "obs": obs,
            "reward": reward,
            "terminated": terminated,
            "truncated": truncated,
            "state_hash": env.state_hash(),
            "events": env.pop_sound_events(),
            "reward_breakdown": info["reward_breakdown"],
        }
        env.close()
        return result

    with_events = run_once(False)
    without_events = run_once(True)

    assert np.array_equal(with_events["obs"], without_events["obs"])
    assert with_events["reward"] == without_events["reward"]
    assert with_events["terminated"] == without_events["terminated"]
    assert with_events["truncated"] == without_events["truncated"]
    assert with_events["state_hash"] == without_events["state_hash"]
    assert with_events["reward_breakdown"] == without_events["reward_breakdown"]
    assert with_events["events"] == ["sgun"]
    assert without_events["events"] == []


def test_common_gui_speed_and_key_policy():
    assert GUI_SPEED_FACTORS == (0.25, 0.5, 1.0, 2.0, 4.0, 8.0)
    state = GuiState()

    assert state.user_speed_factor == 1.0
    handle_common_event(state, SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_f, mod=0), pygame)
    assert state.user_speed_factor == 2.0
    handle_common_event(
        state,
        SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_f, mod=pygame.KMOD_SHIFT),
        pygame,
    )
    assert state.user_speed_factor == 1.0
    handle_common_event(state, SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_f, mod=0), pygame)
    handle_common_event(state, SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_1, mod=0), pygame)
    assert state.user_speed_factor == 1.0
    handle_common_event(state, SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_p, mod=0), pygame)
    assert state.paused is True
    handle_common_event(state, SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_n, mod=0), pygame)
    assert state.single_step is True
    handle_common_event(state, SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_F1, mod=0), pygame)
    assert state.debug_overlay is False
    handle_common_event(state, SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_F3, mod=0), pygame)
    assert state.collision_overlay is True


def test_gui_speed_composes_with_gameover_slowdown():
    state = GuiState()
    state.speed_up()
    assert state.effective_visual_speed() == 2.0
    state.enter_terminal("player_death")
    state.gameover_slowdown = 0.5
    assert state.effective_visual_speed() == 1.0
    state.speed_down()
    state.speed_down()
    assert state.effective_visual_speed() == 0.25


def test_common_post_death_visual_advancement_preserves_state_hash():
    env = HeliAttack2Env(render_mode=None, spawn_default_heli=False, skip_intro=True)
    env.reset(seed=0)
    env.health = 0
    _obs, _reward, terminated, _truncated, info = env.step(IDLE_ACTION)
    assert is_player_death_termination(terminated, info)
    before = env.state_hash()
    state = GuiState()
    state.enter_terminal("player_death")

    for _ in range(20):
        advance_post_death_visuals(env, state)

    assert state.gameover_slowdown == pytest.approx(0.2)
    assert env.state_hash() == before
    env.close()


@pytest.mark.parametrize("script", ["scripts/play_human.py", "scripts/watch_model.py", "scripts/play_replay.py"])
def test_gui_scripts_use_shared_helper_and_default_sound_policy(script):
    source = Path(script).read_text(encoding="utf-8")

    assert "from ha2_gui import" in source
    assert "GuiState" in source
    assert "GuiSound" in source
    assert "handle_common_event" in source
    assert "add_common_gui_args(parser)" in source
    assert "SoundPlayer" not in source


def test_evaluate_model_does_not_require_audio():
    source = Path("scripts/evaluate_model.py").read_text(encoding="utf-8")

    assert "SoundPlayer" not in source
    assert "ha2_gui" not in source
    assert "--no-sound" not in source


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
    assert [effect["type"] for effect in env.visual_effects] == [
        "player_burned",
        "boom",
    ]
    env.close()


def test_player_death_visual_effects_are_render_only(monkeypatch):
    def run_once(disable_effects: bool):
        env = HeliAttack2Env(
            render_mode=None,
            training_profile="combat_v1",
            spawn_default_heli=False,
            skip_intro=True,
        )
        if disable_effects:
            monkeypatch.setattr(env, "_spawn_player_death_effects", lambda: None)
        env.reset(seed=123)
        env.health = -5

        obs, reward, terminated, truncated, info = env.step(IDLE_ACTION)
        result = {
            "obs": obs,
            "reward": reward,
            "terminated": terminated,
            "truncated": truncated,
            "state_hash": env.state_hash(),
            "reward_breakdown": info["reward_breakdown"],
            "termination_reason": info["termination_reason"],
            "visual_effect_count": len(env.visual_effects),
        }
        env.close()
        return result

    with_effects = run_once(False)
    without_effects = run_once(True)

    assert np.array_equal(with_effects["obs"], without_effects["obs"])
    assert with_effects["reward"] == without_effects["reward"]
    assert with_effects["terminated"] is True
    assert with_effects["terminated"] == without_effects["terminated"]
    assert with_effects["truncated"] == without_effects["truncated"]
    assert with_effects["state_hash"] == without_effects["state_hash"]
    assert with_effects["reward_breakdown"] == without_effects["reward_breakdown"]
    assert with_effects["termination_reason"] == "player_death"
    assert without_effects["termination_reason"] == "player_death"
    assert with_effects["visual_effect_count"] == 2
    assert without_effects["visual_effect_count"] == 0


def test_player_death_visual_effects_do_not_consume_gameplay_rng(monkeypatch):
    def make_env(disable_effects: bool):
        env = HeliAttack2Env(render_mode=None, spawn_default_heli=False, skip_intro=True)
        if disable_effects:
            monkeypatch.setattr(env, "_spawn_player_death_effects", lambda: None)
        env.reset(seed=987)
        env.health = -5
        return env

    with_effects = make_env(False)
    without_effects = make_env(True)
    try:
        obs_a, reward_a, terminated_a, truncated_a, info_a = with_effects.step(IDLE_ACTION)
        obs_b, reward_b, terminated_b, truncated_b, info_b = without_effects.step(IDLE_ACTION)

        assert np.array_equal(obs_a, obs_b)
        assert reward_a == reward_b
        assert terminated_a == terminated_b
        assert truncated_a == truncated_b
        assert info_a["termination_reason"] == info_b["termination_reason"] == "player_death"
        assert with_effects.state_hash() == without_effects.state_hash()

        with_effects._add_enemy()
        without_effects._add_enemy()
        assert with_effects.get_state()["enemies"] == without_effects.get_state()["enemies"]
    finally:
        with_effects.close()
        without_effects.close()


def test_advance_visual_effects_only_preserves_gameplay_state():
    env = HeliAttack2Env(
        render_mode=None,
        training_profile="combat_v1",
        spawn_default_heli=False,
        skip_intro=True,
    )
    env.reset(seed=0)
    env.health = -5
    _obs, reward, terminated, truncated, info = env.step(IDLE_ACTION)
    assert terminated is True
    assert truncated is False
    assert info["termination_reason"] == "player_death"
    before_hash = env.state_hash()
    before_state = env.get_state()
    before_effects = list(before_state["visual_effects"])

    env.advance_visual_effects_only(frames=5)

    after_state = env.get_state()
    assert env.state_hash() == before_hash
    for key in after_state:
        if key not in ("visual_effects", "next_visual_effect_id"):
            assert after_state[key] == before_state[key]
    assert after_state["visual_effects"] != before_effects
    assert env.last_reward == reward
    assert env.last_terminated is True
    assert env.last_termination_reason == "player_death"
    env.close()


def test_rgb_array_render_works_after_player_death():
    env = HeliAttack2Env(
        render_mode="rgb_array",
        auto_render=False,
        spawn_default_heli=False,
        skip_intro=True,
    )
    env.reset(seed=0)
    env.health = -5
    _obs, _reward, terminated, _truncated, info = env.step(IDLE_ACTION)
    frame = env.render()

    assert terminated is True
    assert info["termination_reason"] == "player_death"
    assert isinstance(frame, np.ndarray)
    assert frame.shape == (320, 450, 3)
    env.close()


def test_player_death_hold_suppresses_live_player_after_effects_expire():
    env = HeliAttack2Env(
        render_mode="rgb_array",
        auto_render=False,
        training_profile="combat_v1",
        spawn_default_heli=False,
        skip_intro=True,
    )
    env.reset(seed=0)
    env.health = -5
    obs, reward, terminated, truncated, info = env.step(IDLE_ACTION)
    before_hash = env.state_hash()

    assert terminated is True
    assert truncated is False
    assert info["termination_reason"] == "player_death"
    assert env._should_draw_live_player() is False

    env.advance_visual_effects_only(frames=300)
    frame = env.render()

    assert isinstance(frame, np.ndarray)
    assert frame.shape == (320, 450, 3)
    assert env.visual_effects == []
    assert env._should_draw_live_player() is False
    assert env.state_hash() == before_hash
    assert env.last_reward == reward
    assert env.last_terminated is True
    assert env.last_truncated is False
    assert env.last_termination_reason == "player_death"
    assert np.array_equal(env._get_obs(), obs)

    env.reset(seed=0)
    assert env._should_draw_live_player() is True
    env.close()


def test_play_human_detects_player_death_without_auto_reset():
    assert is_player_death_termination(True, {"termination_reason": "player_death"}) is True
    assert is_player_death_termination(True, {"termination_reason": "time_limit"}) is False
    assert is_player_death_termination(False, {"termination_reason": "player_death"}) is False


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
    assert [effect["type"] for effect in env.visual_effects] == [
        "shard",
        "shard",
        "shard",
        "guy_burned",
        "heli_destroyed",
        "boom",
    ]
    env.close()


def test_heli_destruction_effect_assets_load_and_render():
    env = HeliAttack2Env(render_mode="rgb_array", auto_render=False, spawn_default_heli=False)
    env.reset(seed=0)
    env._add_enemy(health=10, x=150.0, y=100.0)
    env._add_bullet(100.0, 100.0, 0.0, 10)

    env.step(IDLE_ACTION)
    frame = env.render()

    assert isinstance(frame, np.ndarray)
    assert env.images["heli_destroyed1"] is not None
    assert env.images["heli_destroyed2"] is not None
    assert env.images["guy_burned"] is not None
    for index in range(1, 11):
        assert env.images[f"boom{index}"] is not None
    for index in range(1, 7):
        assert env.images[f"shard{index}"] is not None
    env.close()


def test_heli_destruction_effects_are_visual_only(monkeypatch):
    def run_once(disable_effects: bool):
        env = HeliAttack2Env(
            render_mode=None,
            training_profile="combat_v1",
            spawn_default_heli=False,
        )
        if disable_effects:
            monkeypatch.setattr(
                env,
                "_spawn_heli_destruction_effects",
                lambda _enemy: None,
            )
        env.reset(seed=123)
        env._add_enemy(health=10, x=150.0, y=100.0)
        env._add_bullet(100.0, 100.0, 0.0, 10)
        obs, reward, terminated, truncated, info = env.step(IDLE_ACTION)
        result = {
            "obs": obs,
            "reward": reward,
            "terminated": terminated,
            "truncated": truncated,
            "state_hash": env.state_hash(),
            "enemies": env.get_state()["enemies"],
            "reward_breakdown": info["reward_breakdown"],
            "visual_effect_count": len(env.visual_effects),
        }
        env.close()
        return result

    with_effects = run_once(False)
    without_effects = run_once(True)

    assert np.array_equal(with_effects["obs"], without_effects["obs"])
    assert with_effects["reward"] == without_effects["reward"]
    assert with_effects["terminated"] == without_effects["terminated"]
    assert with_effects["truncated"] == without_effects["truncated"]
    assert with_effects["state_hash"] == without_effects["state_hash"]
    assert with_effects["enemies"] == without_effects["enemies"]
    assert with_effects["reward_breakdown"] == without_effects["reward_breakdown"]
    assert with_effects["visual_effect_count"] == 6
    assert without_effects["visual_effect_count"] == 0


def test_active_visual_effects_do_not_affect_collisions_or_step_outcomes():
    def run_once(with_effects: bool):
        env = HeliAttack2Env(
            render_mode=None,
            training_profile="combat_v1",
            spawn_default_heli=False,
        )
        env.reset(seed=321)
        env._add_enemy(health=300, x=180.0, y=100.0)
        env._add_bullet(90.0, 100.0, 0.0, 10)
        env._add_enemy_bullet(env._x - 100.0, env._y - 100.0, 0.0)
        if with_effects:
            env.visual_effects = [
                {
                    "id": 1,
                    "type": "boom",
                    "x": round(float(env._x), 8),
                    "y": round(float(env._y), 8),
                    "xspeed": 0.0,
                    "yspeed": 0.0,
                    "rotation": 0.0,
                    "frame": 1,
                    "scale": 2.0,
                    "stepc": 0.0,
                    "pause": 0,
                    "age": 0,
                },
                {
                    "id": 2,
                    "type": "shard",
                    "x": 98.0,
                    "y": 100.0,
                    "xspeed": 0.0,
                    "yspeed": 0.0,
                    "rotation": 0.0,
                    "frame": 1,
                    "scale": 1.0,
                    "stepc": 0.0,
                    "bounces": 0,
                    "r": 0,
                    "age": 0,
                },
                {
                    "id": 3,
                    "type": "guy_burned",
                    "x": 180.0,
                    "y": 100.0,
                    "xspeed": 0.0,
                    "yspeed": 0.0,
                    "rotation": 0.0,
                    "frame": 1,
                    "scale": 1.0,
                    "stepc": 0.0,
                    "rot": 10,
                    "age": 0,
                },
                {
                    "id": 4,
                    "type": "heli_destroyed",
                    "x": 180.0,
                    "y": 100.0,
                    "xspeed": 0.0,
                    "yspeed": 0.0,
                    "rotation": 0.0,
                    "frame": 1,
                    "scale": 1.0,
                    "stepc": 0.0,
                    "age": 0,
                },
            ]
            env.next_visual_effect_id = 5

        obs, reward, terminated, truncated, info = env.step(IDLE_ACTION)
        result = {
            "obs": obs,
            "reward": reward,
            "terminated": terminated,
            "truncated": truncated,
            "state_hash": env.state_hash(),
            "health": env.health,
            "score": env.score,
            "hits": env.hits,
            "bullets": env.get_state()["bullets"],
            "enemy_bullets": env.get_state()["enemy_bullets"],
            "enemies": env.get_state()["enemies"],
            "reward_breakdown": info["reward_breakdown"],
            "termination_reason": info["termination_reason"],
            "active_visual_effects": len(env.visual_effects),
        }
        env.close()
        return result

    with_effects = run_once(True)
    without_effects = run_once(False)

    assert np.array_equal(with_effects["obs"], without_effects["obs"])
    assert with_effects["reward"] == without_effects["reward"]
    assert with_effects["terminated"] == without_effects["terminated"]
    assert with_effects["truncated"] == without_effects["truncated"]
    assert with_effects["state_hash"] == without_effects["state_hash"]
    assert with_effects["health"] == without_effects["health"]
    assert with_effects["score"] == without_effects["score"]
    assert with_effects["hits"] == without_effects["hits"]
    assert with_effects["bullets"] == without_effects["bullets"]
    assert with_effects["enemy_bullets"] == without_effects["enemy_bullets"]
    assert with_effects["enemies"] == without_effects["enemies"]
    assert with_effects["reward_breakdown"] == without_effects["reward_breakdown"]
    assert with_effects["termination_reason"] == without_effects["termination_reason"]
    assert with_effects["active_visual_effects"] > without_effects["active_visual_effects"]


def test_visual_effects_do_not_consume_gameplay_rng(monkeypatch):
    def make_env(disable_effects: bool):
        env = HeliAttack2Env(render_mode=None, spawn_default_heli=False)
        if disable_effects:
            monkeypatch.setattr(env, "_spawn_heli_destruction_effects", lambda _enemy: None)
        env.reset(seed=987)
        env._add_enemy(health=10, x=150.0, y=100.0)
        env._add_bullet(100.0, 100.0, 0.0, 10)
        return env

    with_effects = make_env(False)
    without_effects = make_env(True)
    try:
        for _ in range(90):
            obs_a, reward_a, terminated_a, truncated_a, info_a = with_effects.step(IDLE_ACTION)
            obs_b, reward_b, terminated_b, truncated_b, info_b = without_effects.step(IDLE_ACTION)

            assert np.array_equal(obs_a, obs_b)
            assert reward_a == reward_b
            assert terminated_a == terminated_b
            assert truncated_a == truncated_b
            assert with_effects.state_hash() == without_effects.state_hash()
            assert info_a["enemy_event"] == info_b["enemy_event"]
            assert info_a["gun_event"] == info_b["gun_event"]
    finally:
        with_effects.close()
        without_effects.close()


def test_heli_destruction_effects_are_seed_deterministic():
    states = []
    for _ in range(2):
        env = HeliAttack2Env(render_mode=None, spawn_default_heli=False)
        env.reset(seed=7)
        env._add_enemy(health=10, x=150.0, y=100.0)
        env._add_bullet(100.0, 100.0, 0.0, 10)
        env.step(IDLE_ACTION)
        states.append(env.get_state()["visual_effects"])
        env.close()

    assert states[0] == states[1]


def test_state_load_without_visual_effects_defaults_empty():
    env = HeliAttack2Env(render_mode=None, spawn_default_heli=False)
    env.reset(seed=0)
    state = env.get_state()
    state.pop("visual_effects")
    state.pop("next_visual_effect_id")

    env.set_state(state)

    assert env.visual_effects == []
    assert env.next_visual_effect_id == 1
    env.close()


def test_no_rotor_animation_state_added():
    env = HeliAttack2Env(render_mode=None, spawn_default_heli=False)
    env.reset(seed=0)
    state_text = str(env.get_state()).lower()
    image_keys = " ".join(env.images.keys()).lower()

    assert "rotor" not in state_text
    assert "rotor" not in image_keys
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
