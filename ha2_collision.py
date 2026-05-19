from __future__ import annotations

import math
from typing import Iterable

Point = tuple[float, float]
Matrix = tuple[float, float, float, float, float, float]

COLLISION_MODEL_RECT = "rect"
COLLISION_MODEL_FFDEC_POLYGON = "ffdec_polygon"
COLLISION_MODELS = {COLLISION_MODEL_RECT, COLLISION_MODEL_FFDEC_POLYGON}

# Sources:
# - reference_exports/ffdec_ha2/swf_xml/heli_attack_2.swf.xml
# - reference_exports/ffdec_ha2/sprites_svg/DefineSprite_111_Heli/{1,2}.svg
# - reference_exports/ffdec_ha2/sprites_svg/DefineSprite_109/1.svg
HELI_HIT_FRAME_1_MATRIX: Matrix = (1.0, 0.0, 0.0, 1.0, -104.5, -52.55)
HELI_HIT_FRAME_2_MATRIX: Matrix = (-1.0, 0.0, 0.0, 1.0, 103.5, -52.0)
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

# Sources:
# - reference_exports/ffdec_ha2/swf_xml/heli_attack_2.swf.xml
# - reference_exports/ffdec_ha2/sprites_svg/DefineSprite_136/1.svg
# - reference_exports/ffdec_ha2/sprites_svg/DefineSprite_119/1.svg
PLAYER_HIT_STROKE_WIDTH = 1.0
PLAYER_HIT_STROKE_RADIUS = PLAYER_HIT_STROKE_WIDTH / 2.0
PLAYER_STANDING_HIT_MATRIX: Matrix = (1.0, 0.0, 0.0, 1.0, 12.65, 1.2)
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

# Sources:
# - reference_exports/ffdec_ha2/swf_xml/heli_attack_2.swf.xml
# - reference_exports/ffdec_ha2/sprites_svg/DefineSprite_136/2.svg
# - reference_exports/ffdec_ha2/sprites_svg/DefineSprite_123/1.svg
PLAYER_DUCK_HIT_MATRIX: Matrix = (1.0, 0.0, 0.0, 1.0, 12.85, 7.35)
PLAYER_DUCK_HIT_OFFSET: Point = (12.85, 7.35)
PLAYER_DUCK_HIT_POLYGON: tuple[Point, ...] = (
    (-0.1, 8.65),
    (5.6, 0.6),
    (16.0, 0.6),
    (21.65, 8.65),
    (21.75, 36.6),
    (-0.2, 36.6),
)


def translation_matrix(dx: float, dy: float) -> Matrix:
    return (1.0, 0.0, 0.0, 1.0, float(dx), float(dy))


def rotation_matrix(degrees: float) -> Matrix:
    radians = math.radians(float(degrees))
    cos_v = math.cos(radians)
    sin_v = math.sin(radians)
    return (cos_v, sin_v, -sin_v, cos_v, 0.0, 0.0)


def compose_matrix(parent: Matrix, child: Matrix) -> Matrix:
    """Return a Flash-style affine matrix applying child first, then parent."""
    pa, pb, pc, pd, ptx, pty = parent
    ca, cb, cc, cd, ctx, cty = child
    return (
        pa * ca + pc * cb,
        pb * ca + pd * cb,
        pa * cc + pc * cd,
        pb * cc + pd * cd,
        pa * ctx + pc * cty + ptx,
        pb * ctx + pd * cty + pty,
    )


def apply_matrix(point: Point, matrix: Matrix) -> Point:
    x, y = point
    a, b, c, d, tx, ty = matrix
    return (
        a * float(x) + c * float(y) + tx,
        b * float(x) + d * float(y) + ty,
    )


def transform_polygon_by_matrix(points: Iterable[Point], matrix: Matrix) -> list[Point]:
    return [apply_matrix(point, matrix) for point in points]


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


def point_in_polygon_or_stroke(
    point: Point,
    polygon: Iterable[Point],
    *,
    stroke_radius: float = 0.0,
) -> bool:
    vertices = list(polygon)
    if point_in_polygon(point, vertices):
        return True
    if stroke_radius <= 0.0 or len(vertices) < 2:
        return False
    prev = vertices[-1]
    for curr in vertices:
        if _distance_point_to_segment(point, prev, curr) <= stroke_radius:
            return True
        prev = curr
    return False


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


def _distance_point_to_segment(point: Point, a: Point, b: Point) -> float:
    px, py = point
    ax, ay = a
    bx, by = b
    abx = bx - ax
    aby = by - ay
    length_sq = abx * abx + aby * aby
    if length_sq == 0.0:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * abx + (py - ay) * aby) / length_sq
    t = max(0.0, min(1.0, t))
    closest_x = ax + t * abx
    closest_y = ay + t * aby
    return math.hypot(px - closest_x, py - closest_y)


def heli_hit_matrix_world(x: float, y: float, *, frame: int = 1, rotation: float = 0.0) -> Matrix:
    frame_matrix = HELI_HIT_FRAME_2_MATRIX if int(frame) == 2 else HELI_HIT_FRAME_1_MATRIX
    world_matrix = compose_matrix(translation_matrix(float(x), float(y)), rotation_matrix(float(rotation)))
    return compose_matrix(world_matrix, frame_matrix)


def heli_hit_polygon_world(
    x: float,
    y: float,
    *,
    frame: int = 1,
    rotation: float = 0.0,
) -> list[Point]:
    return transform_polygon_by_matrix(
        HELI_HIT_POLYGON,
        heli_hit_matrix_world(float(x), float(y), frame=frame, rotation=rotation),
    )


def player_hit_polygon_world(x: float, y: float, *, duck: bool = False) -> list[Point]:
    if duck:
        return transform_polygon_by_matrix(
            PLAYER_DUCK_HIT_POLYGON,
            compose_matrix(translation_matrix(float(x), float(y)), PLAYER_DUCK_HIT_MATRIX),
        )
    return transform_polygon_by_matrix(
        PLAYER_STANDING_HIT_POLYGON,
        compose_matrix(translation_matrix(float(x), float(y)), PLAYER_STANDING_HIT_MATRIX),
    )


def point_in_player_hit_shape_world(point: Point, x: float, y: float, *, duck: bool = False) -> bool:
    return point_in_polygon_or_stroke(
        point,
        player_hit_polygon_world(float(x), float(y), duck=duck),
        stroke_radius=PLAYER_HIT_STROKE_RADIUS,
    )
