from __future__ import annotations

import argparse

import ha2_collision as collision
from ha2_env import HeliAttack2Env


def _make_env(model: str) -> HeliAttack2Env:
    env = HeliAttack2Env(
        render_mode=None,
        auto_render=False,
        spawn_default_heli=False,
        collision_model=model,
    )
    env.reset(seed=0)
    return env


def _make_enemy(*, frame: int = 1, rotation: float = 0.0) -> dict:
    return {
        "id": 1,
        "type": "Heli",
        "x": 300.0,
        "y": 200.0,
        "health": 300,
        "frame": frame,
        "rotation": rotation,
    }


def _probe_enemy(rect_env: HeliAttack2Env, poly_env: HeliAttack2Env, label: str, point: tuple[float, float], enemy: dict) -> dict:
    rect_enemy = dict(enemy)
    poly_enemy = dict(enemy)
    rect_env.enemies = [rect_enemy]
    poly_env.enemies = [poly_enemy]
    bullet = {"id": 1, "x": point[0], "y": point[1], "damage": 10}
    return {
        "case": label,
        "rect": rect_env._bullet_hit_enemy(dict(bullet)) is not None,
        "ffdec_polygon": poly_env._bullet_hit_enemy(dict(bullet)) is not None,
        "point": point,
    }


def compare() -> list[dict]:
    rect_env = _make_env(collision.COLLISION_MODEL_RECT)
    poly_env = _make_env(collision.COLLISION_MODEL_FFDEC_POLYGON)
    rows: list[dict] = []
    try:
        heli_frame_1 = _make_enemy(frame=1)
        left, top, _right, _bottom = rect_env._enemy_hit_rect(heli_frame_1)
        rows.append(_probe_enemy(rect_env, poly_env, "heli_frame_1_rect_only_top_left", (left + 1.0, top + 1.0), heli_frame_1))
        rows.append(_probe_enemy(rect_env, poly_env, "heli_frame_1_both_center", (300.0, 200.0), heli_frame_1))

        heli_frame_2 = _make_enemy(frame=2)
        rows.append(_probe_enemy(rect_env, poly_env, "heli_frame_2_mirrored_left_edge", (199.0, 149.0), heli_frame_2))
        rows.append(_probe_enemy(rect_env, poly_env, "heli_frame_2_mirrored_right_edge", (401.0, 149.0), heli_frame_2))

        heli_frame_1_rotated = _make_enemy(frame=1, rotation=30.0)
        rows.append(_probe_enemy(rect_env, poly_env, "heli_frame_1_rotated", (365.0, 155.0), heli_frame_1_rotated))

        heli_frame_2_rotated = _make_enemy(frame=2, rotation=-30.0)
        rows.append(_probe_enemy(rect_env, poly_env, "heli_frame_2_rotated", (235.0, 155.0), heli_frame_2_rotated))

        for env in (rect_env, poly_env):
            env._x = 100.0
            env._y = 50.0
            env.duck = 0
            env.playerwidth = env.defplayerwidth
            env.playerheight = env.defplayerheight
        player_points = {
            "player_standing_polygon_only_left": (115.0, 70.0),
            "player_standing_both_center": (124.0, 70.0),
        }
        for label, point in player_points.items():
            bullet = {"x": point[0], "y": point[1]}
            rows.append(
                {
                    "case": label,
                    "rect": rect_env._enemy_bullet_hit_player(dict(bullet)),
                    "ffdec_polygon": poly_env._enemy_bullet_hit_player(dict(bullet)),
                    "point": point,
                }
            )

        for env in (rect_env, poly_env):
            env.duck = 1
            env.playerwidth = 2 * env.defplayerwidth / 3
            env.playerheight = 2 * env.defplayerheight / 3
        for label, point in {
            "player_duck_inside": (115.0, 75.0),
            "player_duck_outside_low": (115.0, 97.0),
        }.items():
            bullet = {"x": point[0], "y": point[1]}
            rows.append(
                {
                    "case": label,
                    "rect": rect_env._enemy_bullet_hit_player(dict(bullet)),
                    "ffdec_polygon": poly_env._enemy_bullet_hit_player(dict(bullet)),
                    "point": point,
                }
            )
    finally:
        rect_env.close()
        poly_env.close()
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare rect and FFDEC polygon projectile probes.")
    parser.parse_args()
    for row in compare():
        print(
            f"{row['case']}: point={row['point']} "
            f"rect={row['rect']} ffdec_polygon={row['ffdec_polygon']}"
        )


if __name__ == "__main__":
    main()
