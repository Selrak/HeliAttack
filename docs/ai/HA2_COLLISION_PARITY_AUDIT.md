# HA2 Collision Parity Audit

Date: 2026-05-19 Europe/Paris

## Summary

The current Python simulator is frozen in `ha2_env_legacy.py` for later A/B checks. No gameplay behavior was changed in `ha2_env.py`.

The audit confirms that Python map collision is close to the inspected `heroAction` tile probes, but Python adds index bounds safety that literal ActionScript `hitCheck` does not. Player/enemy projectile collision is a gameplay approximation: ActionScript uses Flash `hitTest(x, y, true)` against nested `hit` clips, while Python tests projectile points against axis-aligned rectangles.

## ActionScript Evidence

Primary file: `heliattack2_scripts/ha2_core_logic/frame_19_DoAction_2.as`.

- `hitCheck` at lines 3089-3136 loops `y = cy..cy2`, `x = cx..cx2`, and reads `mapa[y][x][0]` directly. It counts tiles where `0 <= value < 100` and either `value == type` when `equal` is true or `value != type` otherwise.
- Right movement, lines 1942-1948: guards `tile2x >= width`, otherwise calls `hitCheck(map,this.tiley,this.tile2x,this.tile2y,this.tile2x,1,1,1)`.
- Left movement, lines 1962-1968: guards `tilex < 0`, otherwise calls `hitCheck(map,this.tiley,this.tilex,this.tile2y,this.tilex,1,1,1)`.
- Falling, line 1989: calls `hitCheck(map,this.tile2y,this.tilex,this.tile2y,this.tile2x,0)` without an explicit local bounds guard.
- Rising, line 2003: calls `hitCheck(map,this.tiley,this.tilex,this.tiley,this.tile2x,0)` without an explicit local bounds guard.
- Player bullets, `bulletFrame` lines 241-280: moves the projectile point, tests `enemyArray[i].hit.hitTest(this._x + world._x,this._y + world._y,1)`, then removes on enemy hit, solid tile, or active-region exit.
- The same enemy `hit.hitTest(...,1)` pattern is used by other weapon projectile frames at lines 667, 746, 820, 911, 984, 1076, 1193, and 1368.
- Enemy bullets, `enemyBulletFrame` lines 1551-1579: moves the projectile point, tests `player.gfx.hit.hitTest(this._x + world._x,this._y + world._y,1)`, then applies `player.health -= 10`.
- Heli setup hides the hit child: `reference_exports/ffdec_ha2/scripts_as/scripts/DefineSprite_111_Heli/frame_1/DoAction.as` contains `hit._visible = 0`.

## Current Python Model

- `ha2_env.py::_hit_check`: mirrors the AS tile count rules but ignores out-of-range indexes instead of directly indexing the map. Classification: deliberate robustness difference.
- Player movement tile probes around `ha2_env.py:1555-1655`: mirrors the inspected AS horizontal and vertical probe formulas and snap formulas. Classification: likely ActionScript-equivalent except for `_hit_check` bounds safety.
- `ha2_env.py::_map_tile_empty_at`: helper with explicit out-of-bounds false result. Classification: deliberate robustness difference.
- `ha2_env.py::_projectile_should_remove`: removes projectiles on out-of-bounds, nonzero map tile, or active-region exit. Classification: likely close to AS for normal in-map shots; safer near invalid indexes.
- `ha2_env.py::_enemy_hit_rect`: returns an axis-aligned rectangle from `HELI_HIT_OFFSET_X/Y/WIDTH/HEIGHT`. Classification: gameplay approximation.
- `ha2_env.py::_bullet_hit_enemy`: tests bullet point inside `_enemy_hit_rect`, then applies damage/score/hit. Classification: gameplay approximation.
- `ha2_env.py::_player_hit_rect`: returns a centered logical `playerwidth x playerheight` rectangle. Classification: gameplay approximation for projectile damage.
- `ha2_env.py::_enemy_bullet_hit_player`: tests bullet point inside `_player_hit_rect`. Classification: gameplay approximation.
- `ha2_env.py::_draw_collision_debug`: draws rectangles and bullet markers only. Classification: visual/debug-only helper.

## Confirmed Matches

- Horizontal player movement has the same explicit AS left/right bounds guards before map collision.
- The player movement snap formulas in Python match the inspected AS formulas.
- Player and enemy bullets are modeled as points for hit tests and removal checks.
- Bullet removal checks include solid tiles and active-region bounds, matching the AS structure.
- FFDEC confirms nested collision-only hit clips exist:
- Heli: `reference_exports/ffdec_ha2/sprites_svg/DefineSprite_111_Heli/1.svg` has `id="hit"` using character `109` at transform `(-104.5, -52.55)`.
- Heli hit shape: `reference_exports/ffdec_ha2/sprites_svg/DefineSprite_109/1.svg` contains a non-rectangular polygon with width `206.9` and height `92.25`.
- Hero: `reference_exports/ffdec_ha2/sprites_svg/DefineSprite_137_hero/1.svg` has `id="gfx"` and nested `id="hit"` using character `119`.
- Standing hero hit shape: `reference_exports/ffdec_ha2/sprites_svg/DefineSprite_119/1.svg` is a non-rectangular polygon with width `22.85` and height `47.6`.
- Duck hit shape: `reference_exports/ffdec_ha2/sprites_svg/DefineSprite_123/1.svg` is a shorter non-rectangular polygon with width `22.95` and height `37.0`.

## Likely Gameplay Divergences

- Player survival: yes, current enemy-bullet/player collision can differ because Python uses the logical rectangle while Flash tests the nested `player.gfx.hit` shape for the current frame.
- Heli kill timing: yes, current player-bullet/Heli collision can differ because Python uses an axis-aligned rectangle instead of the exported Heli hit polygon.
- Bullet hit/miss behavior: yes, both player and enemy projectiles can hit or miss differently near the non-rectangular hit-shape edges.
- Training rewards: yes, reward and episode metrics depend on damage, kills, survival, and max progress, so collision differences can change learning signals.
- Evaluation comparability: yes, policies evaluated under rectangle collision may not compare cleanly to later shape-accurate collision.
- Heli rotation risk: likely, because AS calls `enemyArray[i].hit.hitTest(...)` on a child of the Heli clip; Flash inherited transforms may include the Heli rotation. Python `_enemy_hit_rect` is axis-aligned and does not rotate the Heli hit area.

## Unresolved Questions

- Whether Flash `hitTest(x, y, true)` in this SWF uses the exact non-rectangular vector shape after all nested transforms, or whether any export/decompiler detail changes that interpretation.
- Exact current-frame player `gfx.hit` frame selection for every hero state. FFDEC shows standing and duck hit shapes, but Python projectile damage currently does not switch to those shapes.
- Exact treatment of out-of-range `mapa[y][x][0]` in live Flash near vertical edge cases.
- Whether the Heli child `hit` transform should be rotated with the visible Heli for collision, and if so around which effective registration point.

## Recommended Next Simulator Changes

Safe changes:

- Keep `ha2_env_legacy.py` untouched as the rectangle-collision baseline.
- Add focused collision unit tests around current rectangle behavior before changing `ha2_env.py`.
- Add deterministic scripted traces that isolate near-edge player bullet hits, enemy bullet hits, Heli rotation angles, standing player hits, and ducking player hits.

Likely changes requiring validation:

- Replace player projectile collision with point-in-FFDEC-polygon checks for Heli `DefineSprite_109`, including nested placement and likely Heli rotation.
- Replace enemy projectile collision with point-in-FFDEC-polygon checks for `player.gfx.hit`, choosing the active `gfx` frame.
- Preserve deterministic replay hashes by making all new collision computations pure and deterministic.
- Compare new behavior against `ha2_env_legacy.py` on targeted traces before using it for RL conclusions.

Changes that must wait for evidence:

- Reproducing exact Flash `hitTest` transform semantics if SVG placement data is insufficient.
- Changing vertical map-edge behavior to literal AS behavior without live Flash or bytecode confirmation.
- Treating Heli rotation as collision-rotating unless validated against Flash or FFDEC/SWF transform semantics.

## FFDEC Resources Needed, If Any

Available now:

- `reference_exports/ffdec_ha2/sprites_svg/DefineSprite_111_Heli/1.svg`
- `reference_exports/ffdec_ha2/sprites_svg/DefineSprite_109/1.svg`
- `reference_exports/ffdec_ha2/sprites_svg/DefineSprite_137_hero/1.svg`
- `reference_exports/ffdec_ha2/sprites_svg/DefineSprite_136/*.svg`
- `reference_exports/ffdec_ha2/sprites_svg/DefineSprite_119/1.svg`
- `reference_exports/ffdec_ha2/sprites_svg/DefineSprite_123/1.svg`

Still useful later:

- A concise FFDEC/SWF transform table for `DefineSprite_137_hero -> gfx -> hit` by hero frame.
- A concise transform table for `DefineSprite_111_Heli -> hit` and Heli parent registration/rotation behavior.
- If possible, Flash-side point probes or screenshots for bullets near Heli/player hit-shape edges to validate shape and transform interpretation.
