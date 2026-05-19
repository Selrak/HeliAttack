# Flash / ActionScript Findings

Durable HA2 parity facts confirmed from static ActionScript and FFDEC exports.

## Projectile Hit Tests - 2026-05-19

- Player projectiles call `enemyArray[i].hit.hitTest(this._x + world._x, this._y + world._y, 1)` in `heliattack2_scripts/ha2_core_logic/frame_19_DoAction_2.as`.
- Enemy bullets call `player.gfx.hit.hitTest(this._x + world._x, this._y + world._y, 1)` in the same AS file.
- P-code exports under `reference_exports/ffdec_ha2/scripts_pcodehex/` and `scripts_pcode/` include the same `hitTest`, `world`, `enemyArray`, and `player/gfx/hit` call structure.
- `hitTest(x, y, true)` is point-vs-occupied-shape in global/stage coordinates; the AS adds `world._x` / `world._y` before testing.

## FFDEC Hit Shapes - 2026-05-19

- Heli `DefineSprite_111_Heli` frame 1 places `hit` character `109` with matrix translation `(-104.5, -52.55)`.
- Heli frame 2 moves the same hit child with `scaleX=-1`, `scaleY=1`, translation `(103.5, -52.0)`.
- Heli parent `_rotation` applies to the nested hit child through the Flash display-list transform chain.
- Player `DefineSprite_136` frame 1 places standing `hit` character `119` at `(12.65, 1.2)`.
- Player `DefineSprite_136` frame 2 places duck `hit` character `123` at `(12.85, 7.35)`.
- Later non-duck `DefineSprite_136` frames reuse standing `hit` character `119`.
- Player hit shapes include 1 px line strokes around their fill paths; Heli hit shape is fill-only.

## Simulator Status - 2026-05-19

- `collision_model="ffdec_polygon"` is the default simulator collision model; explicit `collision_model="rect"` remains available.
- Remaining risk: live Flash rasterization/sub-pixel behavior and full non-duck animation-frame mapping still need targeted validation.

## HeroStart / Parachute Intro - 2026-05-19

- `assignents()` clears map marker `32`, sets `player._x = x * tileWidth + tileWidth / 2`, and sets `player._y = -50`.
- `heroStart(timeStep)` forces `this.gfx.gotoAndStop(6)`, increments `stepc`, sets `yspeed=2` once `stepc > 1`, then moves `this._y += this.yspeed * timeStep` and `this._y += 5`.
- Before closing, `heroStart` expands `this.gfx.chute._xscale` up to 100 and switches to falling when `y > 0 && map[y + 5][x][0] != 0`.
- During falling, it shrinks `this.gfx.chute._xscale` by `10 * timeStep`; once below 0 it hides the chute, switches `this.action = heroAction`, sets `gamestarted = 1`, and calls `addEnemy(300)`.
- The evolving Python env now implements this as `intro_mode="as_intro"` when `skip_intro=False`; `skip_intro=True` is a deliberate fast-start mode for training/scripts.
