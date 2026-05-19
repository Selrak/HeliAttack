from __future__ import annotations

import math
from typing import Iterable

Point = tuple[float, float]

COLLISION_MODEL_RECT = "rect"
COLLISION_MODEL_FFDEC_POLYGON = "ffdec_polygon"
COLLISION_MODELS = {COLLISION_MODEL_RECT, COLLISION_MODEL_FFDEC_POLYGON}

# Source: reference_exports/ffdec_ha2/sprites_svg/DefineSprite_109/1.svg
HELI_HIT_OFFSET: Point = (-104.5, -52.55)
HELI_HIT_POLYGON: tuple[Point, ...] = (
    (205.25, 0.05),
    (205.25, 9.3),
    (114.15, 9.3),
    (114.15, 20.55),
    (141.95, 20.55),
    (207.15, 59.5),
    (207.15, 78.4),
    (161.2, 92.3),
    (96.4, 92.3),
    (24.5, 76.85),
    (18.4, 47.5),
    (0.25, 36.55),
    (2.6, 0.05),
)

# Source: reference_exports/ffdec_ha2/sprites_svg/DefineSprite_119/1.svg
PLAYER_STANDING_HIT_OFFSET: Point = (12.65, 1.2)
PLAYER_STANDING_HIT_POLYGON: tuple[Point, ...] = (
    (1.3, 19.85),
    (3.35, 16.15),
    (0.2, 11.95),
    (0.2, 7.85),
    (6.6, 0.3),
    (16.1, 0.2),
    (21.45, 7.45),
    (21.45, 13.05),
    (19.35, 16.65),
    (22.05, 20.65),
    (22.05, 46.8),
    (1.2, 46.8),
)

# Source: reference_exports/ffdec_ha2/sprites_svg/DefineSprite_123/1.svg
PLAYER_DUCK_HIT_OFFSET: Point = (12.85, 7.35)
PLAYER_DUCK_HIT_POLYGON: tuple[Point, ...] = (
    (-0.1, 8.65),
    (5.6, 0.6),
    (16.0, 0.6),
    (21.65, 8.65),
    (21.75, 36.6),
    (-0.2, 36.6),
)


def translate_polygon(points: Iterable[Point], dx: float, dy: float) -> list[Point]:
    return [(float(x) + float(dx), float(y) + float(dy)) for x, y in points]


def rotate_point(point: Point, degrees: float) -> Point:
    x, y = point
    radians = math.radians(float(degrees))
    return (
        math.cos(radians) * x - math.sin(radians) * y,
        math.sin(radians) * x + math.cos(radians) * y,
    )


def transform_polygon(
    points: Iterable[Point],
    *,
    offset: Point = (0.0, 0.0),
    origin: Point = (0.0, 0.0),
    rotation: float = 0.0,
) -> list[Point]:
    ox, oy = offset
    tx, ty = origin
    transformed: list[Point] = []
    for px, py in points:
        local = (float(px) + ox, float(py) + oy)
        rx, ry = rotate_point(local, rotation)
        transformed.append((tx + rx, ty + ry))
    return transformed


def point_in_polygon(point: Point, polygon: Iterable[Point]) -> bool:
    x, y = point
    vertices = list(polygon)
    if len(vertices) < 3:
        return False

    inside = False
    prev_x, prev_y = vertices[-1]
    for curr_x, curr_y in vertices:
        if _point_on_segment((x, y), (prev_x, prev_y), (curr_x, curr_y)):
            return True
        crosses = (curr_y > y) != (prev_y > y)
        if crosses:
            x_intersect = (prev_x - curr_x) * (y - curr_y) / (prev_y - curr_y) + curr_x
            if x <= x_intersect:
                inside = not inside
        prev_x, prev_y = curr_x, curr_y
    return inside


def _point_on_segment(point: Point, a: Point, b: Point, *, eps: float = 1e-9) -> bool:
    px, py = point
    ax, ay = a
    bx, by = b
    cross = (px - ax) * (by - ay) - (py - ay) * (bx - ax)
    if abs(cross) > eps:
        return False
    return (
        min(ax, bx) - eps <= px <= max(ax, bx) + eps
        and min(ay, by) - eps <= py <= max(ay, by) + eps
    )


def heli_hit_polygon_world(x: float, y: float, rotation: float = 0.0) -> list[Point]:
    return transform_polygon(
        HELI_HIT_POLYGON,
        offset=HELI_HIT_OFFSET,
        origin=(float(x), float(y)),
        rotation=float(rotation),
    )


def player_hit_polygon_world(x: float, y: float, *, duck: bool = False) -> list[Point]:
    if duck:
        return transform_polygon(
            PLAYER_DUCK_HIT_POLYGON,
            offset=PLAYER_DUCK_HIT_OFFSET,
            origin=(float(x), float(y)),
        )
    return transform_polygon(
        PLAYER_STANDING_HIT_POLYGON,
        offset=PLAYER_STANDING_HIT_OFFSET,
        origin=(float(x), float(y)),
    )
