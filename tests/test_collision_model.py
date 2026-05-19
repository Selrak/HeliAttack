from __future__ import annotations

import pytest

import ha2_collision as collision
from ha2_env import HeliAttack2Env


def make_env(**kwargs) -> HeliAttack2Env:
    env = HeliAttack2Env(render_mode=None, auto_render=False, spawn_default_heli=False, **kwargs)
    env.reset(seed=0)
    return env


def make_enemy(
    x: float = 300.0,
    y: float = 200.0,
    *,
    frame: int = 1,
    rotation: float = 0.0,
) -> dict:
    return {
        "id": 1,
        "type": "Heli",
        "x": x,
        "y": y,
        "health": 300,
        "frame": frame,
        "rotation": rotation,
    }


def test_ffdec_polygon_collision_model_is_current_default():
    env = make_env()
    try:
        assert env.collision_model == collision.COLLISION_MODEL_FFDEC_POLYGON
    finally:
        env.close()


def test_explicit_rect_collision_model_locks_current_enemy_rect_behavior():
    env = make_env(collision_model=collision.COLLISION_MODEL_RECT)
    try:
        enemy = make_enemy()
        env.enemies = [enemy]

        left, top, right, bottom = env._enemy_hit_rect(enemy)
        assert (left, top, right, bottom) == pytest.approx((195.5, 147.45, 402.5, 240.45))

        hit_enemy_id = env._bullet_hit_enemy(
            {"id": 1, "x": left + 1.0, "y": top + 1.0, "damage": 10}
        )

        assert hit_enemy_id == 1
        assert enemy["health"] == 290
        assert env.score == 10
        assert env.hits == 1
    finally:
        env.close()


def test_explicit_rect_collision_model_locks_current_player_rect_behavior():
    env = make_env(collision_model=collision.COLLISION_MODEL_RECT)
    try:
        env._x = 100.0
        env._y = 50.0
        env.duck = 0
        env.playerwidth = env.defplayerwidth
        env.playerheight = env.defplayerheight

        left, top, right, bottom = env._player_hit_rect()
        assert (left, top, right, bottom) == pytest.approx((119.0, 53.0, 129.0, 95.0))
        assert env._enemy_bullet_hit_player({"x": left + 1.0, "y": top + 1.0})
        assert not env._enemy_bullet_hit_player({"x": left - 1.0, "y": top + 1.0})
    finally:
        env.close()


def test_invalid_collision_model_fails_clearly():
    with pytest.raises(ValueError, match="Unknown collision_model"):
        HeliAttack2Env(render_mode=None, collision_model="not-a-model")


def test_point_in_polygon_known_inside_outside_points():
    assert collision.point_in_polygon((100.0, 50.0), collision.HELI_HIT_POLYGON)
    assert not collision.point_in_polygon((1.0, 1.0), collision.HELI_HIT_POLYGON)

    assert collision.point_in_polygon((10.0, 30.0), collision.PLAYER_STANDING_HIT_POLYGON)
    assert not collision.point_in_polygon((0.0, 0.0), collision.PLAYER_STANDING_HIT_POLYGON)

    assert collision.point_in_polygon((10.0, 20.0), collision.PLAYER_DUCK_HIT_POLYGON)
    assert not collision.point_in_polygon((0.0, 0.0), collision.PLAYER_DUCK_HIT_POLYGON)


def test_heli_frame_1_polygon_uses_ffdec_hit_placement():
    polygon = collision.heli_hit_polygon_world(300.0, 200.0, frame=1)

    assert polygon[0] == pytest.approx((400.75, 147.5))
    assert polygon[-1] == pytest.approx((198.1, 147.5))


def test_heli_frame_2_polygon_uses_mirrored_ffdec_hit_placement():
    polygon = collision.heli_hit_polygon_world(300.0, 200.0, frame=2)

    assert polygon[0] == pytest.approx((198.25, 148.05))
    assert polygon[-1] == pytest.approx((400.9, 148.05))


def test_heli_parent_rotation_rotates_hit_shape_around_registration_point():
    polygon = collision.heli_hit_polygon_world(300.0, 200.0, frame=1, rotation=90.0)

    assert polygon[0] == pytest.approx((352.5, 300.75))


def test_player_standing_polygon_uses_definesprite_119_placement():
    polygon = collision.player_hit_polygon_world(100.0, 50.0, duck=False)

    assert polygon[0] == pytest.approx((113.95, 71.05))
    assert polygon[-1] == pytest.approx((113.85, 98.0))


def test_player_duck_polygon_uses_definesprite_123_placement():
    polygon = collision.player_hit_polygon_world(100.0, 50.0, duck=True)

    assert polygon[0] == pytest.approx((112.75, 66.0))
    assert polygon[-1] == pytest.approx((112.65, 93.95))


def test_player_hit_shape_includes_one_pixel_stroke():
    # Just left of the standing vertical outline: outside fill, inside the 0.5 px stroke radius.
    assert collision.point_in_player_hit_shape_world((113.45, 85.0), 100.0, 50.0, duck=False)
    assert not collision.point_in_polygon(
        (113.45, 85.0),
        collision.player_hit_polygon_world(100.0, 50.0, duck=False),
    )


def test_ffdec_polygon_heli_collision_can_differ_from_rect_near_edge():
    rect_env = make_env(collision_model=collision.COLLISION_MODEL_RECT)
    polygon_env = make_env(collision_model=collision.COLLISION_MODEL_FFDEC_POLYGON)
    try:
        enemy_rect = make_enemy()
        enemy_polygon = make_enemy()
        rect_env.enemies = [enemy_rect]
        polygon_env.enemies = [enemy_polygon]

        left, top, _right, _bottom = rect_env._enemy_hit_rect(enemy_rect)
        probe = {"id": 1, "x": left + 1.0, "y": top + 1.0, "damage": 10}

        assert rect_env._bullet_hit_enemy(dict(probe)) == 1
        assert polygon_env._bullet_hit_enemy(dict(probe)) is None
        assert enemy_polygon["health"] == 300
    finally:
        rect_env.close()
        polygon_env.close()


def test_ffdec_polygon_player_collision_can_differ_from_rect_near_standing_edge():
    rect_env = make_env(collision_model=collision.COLLISION_MODEL_RECT)
    polygon_env = make_env(collision_model=collision.COLLISION_MODEL_FFDEC_POLYGON)
    try:
        for env in (rect_env, polygon_env):
            env._x = 100.0
            env._y = 50.0
            env.duck = 0
            env.playerwidth = env.defplayerwidth
            env.playerheight = env.defplayerheight

        probe = {"x": 115.0, "y": 70.0}
        assert not rect_env._enemy_bullet_hit_player(probe)
        assert polygon_env._enemy_bullet_hit_player(probe)
    finally:
        rect_env.close()
        polygon_env.close()


def test_ffdec_polygon_player_collision_uses_duck_shape():
    env = make_env(collision_model=collision.COLLISION_MODEL_FFDEC_POLYGON)
    try:
        env._x = 100.0
        env._y = 50.0
        env.duck = 1
        env.playerwidth = 2 * env.defplayerwidth / 3
        env.playerheight = 2 * env.defplayerheight / 3

        duck_probe = {"x": 115.0, "y": 75.0}
        standing_only_probe = {"x": 115.0, "y": 97.0}

        assert env._enemy_bullet_hit_player(duck_probe)
        assert not env._enemy_bullet_hit_player(standing_only_probe)
    finally:
        env.close()


def test_ffdec_polygon_enemy_collision_uses_heli_frame_2_shape():
    env = make_env(collision_model=collision.COLLISION_MODEL_FFDEC_POLYGON)
    try:
        enemy = make_enemy(frame=2)
        env.enemies = [enemy]

        assert env._bullet_hit_enemy({"id": 1, "x": 199.0, "y": 149.0, "damage": 10}) == 1
        assert enemy["health"] == 290
    finally:
        env.close()
