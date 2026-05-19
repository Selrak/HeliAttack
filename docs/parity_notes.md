# HA2 Parity Notes

## AS Audit - 2026-05-04

Inspected source: `heliattack2_scripts/ha2_core_logic/frame_19_DoAction_2.as`.

- Player setup/spawn: `drawMap`, `assignents`, `heroSetup`, and `heroStart` create `hero`, clear map collision marker `32`, set `player._x = x * tileWidth + tileWidth / 2`, set `player._y = -50`, and initialize `width=48`, `height=48`, `defplayerwidth=10`, `defplayerheight=42`, `jump`, `jump2`, `duck`, `hyperjump=150`. Python appears matching for steady-state spawn/setup, but does not model the AS parachute/start transition before `heroAction`.
- Movement/jump/duck/hyperjump: `heroAction` uses `leftkey`, `rightkey`, `duckKey`, `jumpkey`, and `boostKey`; acceleration, damping, velocity clamps, jump hold, double-jump gating, hyperjump charge/use, and ground/ceiling snap formulas are closely mirrored in Python. Status: mostly matching.
- Casing quirk: setup defines lowercase `defplayerwidth`/`defplayerheight`, while action code reads mixed-case `defPlayerWidth`, `playerWidth`, and lowercase `playerwidth`/`playerheight`. As decompiled, this is internally inconsistent. Python normalizes to working lowercase fields, which likely preserves intended behavior but masks the exact Flash/decompiler casing question. Status: unresolved without bytecode or live Flash traces.
- Collision and bounds: AS `hitCheck(mapa, cy, cx, cy2, cx2, type, equal, hold)` directly indexes `mapa[y][x][0]`; `heroAction` manually guards horizontal world bounds before `hitCheck` but not every vertical probe. Python bounds-checks in `_hit_check`, so it is safer than the literal AS and may hide edge quirks. Status: movement collisions are close, edge behavior uncertain.
- Animation frames: AS sets `this.gfx.gotoAndStop(1)` idle, `2` duck, `3` first jump, `4` walk, `5` double jump, `6` chute/start; walk advances nested `this.gfx.gfx.nextFrame()` once per movement tick. Python uses colored FFDEC bitmap exports for idle/duck/jump/walk/double-jump and alternates walk bitmaps by tick cadence. Status: state-frame mapping is justified; exact nested walk cadence and registration remain uncertain.
- Mirroring: inspected player body animation code does not set player/gfx `_xscale`; only gun/chute-related scales appear. Python not mirroring the body appears AS-backed. Status: matching.
- Camera/background: AS updates `world._x/_y` only when `heroAction` threshold checks trigger, then clamps through `scrollMap`; `bglayer1._x` scrolls by half the world delta and wraps, and `bglayer1._y` depends on `(-world._y) / maxheight`. Python now keeps stateful `world_x/world_y/worldpos` for Heli/projectile logic and rendering, but parallax remains simplified.
- Map/tile rendering: AS `drawMap` attaches `(stw + 1) x (sth + 1)` reusable tiles at `x * tileWidth - 1`, `y * tileHeight - 1`, using `arr[y][x][1] + 1`. Python uses the same FFDEC tile frame mapping and `-1` offset but draws visible tiles directly instead of recycling movie clips. Status: visual mapping likely close; scrolling implementation differs.
- MachineGun: AS `heroSetup` initializes `guns[0]` with infinite bullets and `cgun=0`; global `guns[0]` is `MachineGun` with `reloadtime=5`, `speed=8`, and `damage=10`. AS firing uses `mouseD`, increments reload while the game is moving, fires when reload is ready, uses `gun.barrell.localToGlobal`, and `machineGun` spawns `bulletFrame` frame `1` with `rot - 2 + random(4)`. Python now mirrors the cadence, constants, deterministic local spread, bullet velocity, tile/world-bounds removal, and replay hashing. Status: functional first slice.
- Heli enemy: Python queues the default Heli on reset, then spawns it after first ground contact using AS-style `addEnemy` offscreen coordinates. It implements AS-style `heliFrame` target/acceleration/damping/gun-aim/shoot cadence, deterministic env-local spread, enemy bullets, player damage, player-bullet damage, score/hit/kill counters, and Heli/enemy-bullet state hashing. Status: AS-backed first combat loop, not exact Flash lifecycle.
- Heli visual: FFDEC `DefineSprite_111_Heli` is rendered from visible body `images/78.png` plus pilot `77.png`; the green hidden `hit` child is collision-only. The nested gun uses `DefineSprite_107/1.png`, Heli gun placement `(11,7)` / `(-9,7)`, and MachineGun `barrell` `(22.7,-7.4)`.

## AS Audit - 2026-05-05 Heli Combat Loop

- Implemented equations from AS `heliFrame`: `stepc`, `xt/yt`, `xdif`, `tx/ty`, offscreen acceleration divisors, `rotation=floor(xspeed/20*15)`, damping, gun target angle, shortest-angle smoothing by `max(1,10-level)`, y-flip, and shoot cadence `shoot++ % max(10,16-level) == 1`.
- Implemented AS `addEnemyBullet` / `enemyBulletFrame` behavior for speed 7, `rotation - 5 + random(10)`, solid-tile/active-region removal, player hit detection, and `health -= 10`; blood/sounds are intentionally omitted.
- Implemented gameplay-essential Heli death/respawn from AS `heliFrame`: remove dead Heli, increment `helis`/`rthelis`, and call AS-style `addEnemy(300)` for the next target. Random weapon popup, powerup/drop handling, shards, burned pilot, destroyed Heli, boom, bullet-time refill, and sounds remain omitted.
- P-code confirms the decompiled `timeSetp` typo exists. Python uses `timeStep=1` for Heli y-damping rather than reproducing an undefined-name failure; exact Flash runtime effect still needs live comparison.
- AS reads both `onScreen` and `onscreen`; Python uses lowercase `onscreen` consistently so the Heli combat loop remains functional. This casing quirk needs Flash verification.

## AS Audit - 2026-05-05 Heli Startup/Damage Fix

- AS `heroStart` calls `addEnemy(300)` only after the chute closes and gameplay switches to `heroAction`; Python now delays the default Heli until first ground contact as a minimal proxy.
- The startup dart was caused by reset-time Heli spawn: early `heliFrame` Y targeting used the still-falling player Y, producing a large negative target before the Heli came back down.
- Enemy bullet damage was mechanically present, but not visible enough in traces/overlay. Debug state and scripted summaries now report player health, last damage, and the first damaging enemy bullet/frame.

## AS Audit - 2026-05-05 Continuous Heli Combat

- AS `heliFrame` calls `addEnemy(300)` after Heli death if `!gameover`; Python now respawns a replacement Heli immediately in the same simulator step.
- AS increments `helis` and `rthelis` on death. Python increments both once per killed Heli; `rthelis` is the total-kill counter shown in trace summaries.
- AS HUD updates `HUD.score`, `HUD.time`, and `HUD.health.mask._yscale`; Python now renders the player healthbar from FFDEC bitmaps `170.png`/`174.png` near `HUD.health` placement `(431,0)`, with a small left offset so the bar no longer hugs the screen edge. Score/time/ammo HUD composition remains unimplemented.

## AS Audit - 2026-05-19 Collision / HitTest Investigation

- AS player projectiles use `enemyArray[i].hit.hitTest(this._x + world._x,this._y + world._y,1)` against the Heli nested `hit` clip, not a Python-style rectangle test.
- AS enemy projectiles use `player.gfx.hit.hitTest(this._x + world._x,this._y + world._y,1)` against the current player graphics nested `hit` clip.
- FFDEC SVG exports now confirm non-rectangular hidden hit shapes for Heli `DefineSprite_109`, standing player `DefineSprite_119`, and duck player `DefineSprite_123`.
- Current Python projectile collision remains rectangle-based; see `docs/ai/HA2_COLLISION_PARITY_AUDIT.md` before changing simulator behavior.

## Believed To Match Current AS Translation
- Player spawn uses `map[y][x][0] == 32`, sets `x = tile * 50 + 25`, and starts at `y = -50`.
- Runtime map setup now clears `32` spawn markers to `0`, matching AS `assignents()`.
- Core movement values currently match the inspected AS2 constants: width `48`, height `48`, player hitbox `10 x 42`, gravity increment `+1`, walk acceleration `1`, walk clamp near `5`, velocity clamp near `6`, jump hold `6`, jump impulse `-8`, hyperjump charge `150`, and hyperjump impulse `-32`.
- Current collision math follows the inspected `heroAction` tile probes and pixel snap formulas.
- Tile rendering uses FFDEC `DefineSprite_318_tiles` frames with AS mapping `map_graphic_index + 1` and the original `-1` draw offset.
- The left world boundary can leave part of the visible sprite outside the world because AS collision uses a narrow centered hitbox and snaps `_x` using the logical `width=48`, not the full visible body.
- Player body rendering does not mirror on left/right movement; inspected AS did not show a hero body `_xscale` flip. Walking currently alternates colored bitmap exports `126.png` and `128.png`.
- Default MachineGun constants and reload cadence match inspected AS. MachineGun spread uses the Gymnasium/env-local RNG (`self.np_random`), not Python global randomness, so seeded replay remains deterministic.
- Player MachineGun bullets damage the default Heli, remove on hit, and update score/hit counters deterministically.
- Dead Helis are removed and replacement Helis spawn deterministically with AS-style `addEnemy` positioning when `respawn_helis=True`.
- Player healthbar HUD uses original FFDEC healthbar assets and the AS `HUD.health.mask._yscale` rule.

## Uncertain
- Decompiled AS uses mixed variable casing such as `defplayerwidth` in setup and `defPlayerWidth` in action, plus `playerWidth`/`playerwidth`. Current Python uses the lowercase working fields from the previous port; exact Flash runtime behavior needs verification.
- `hitCheck` in AS assumes map indexes are valid. Current Python bounds-checks indexes, preserving prior port behavior but possibly hiding original edge behavior.
- Player rendering uses colored FFDEC bitmap image exports centered in the logical 48x48 hero box. Exact Flash registration point and walk animation cadence should still be verified.
- Camera/parallax is only partly AS-style: Heli/projectiles now use stateful `world_x/world_y/worldpos`, but `heroStart` parachute startup and background parallax are still simplified.
- Gun visual registration now uses FFDEC placement data provided by Charles: hero `gun` at `(24.0, 29.0)` and MachineGun `barrell` at `(22.7, -7.4)`, giving zero-rotation visual barrel origin `(46.7, 21.6)` from the Flash hero origin. Bullet spawn registration was left unchanged in this visual-only task.
- Bullet active-region removal now uses Python `worldpos/stw/sth` plus solid-tile checks.
- Heli spawn is delayed until first ground contact as a minimal proxy for AS `heroStart`; the actual parachute/start lifecycle is still not modeled.
- Heli death side effects that are not required for MachineGun-only training are omitted: random weapon rewards, powerups/drops, shards, destroyed-Heli debris, blood, sounds, and bullet-time refill.
- Only the original player healthbar HUD is implemented; score/time/ammo/reload/hyperjump HUD elements remain future work.
- Heli hit detection uses the FFDEC nested `hit` placement from `DefineSprite_111_Heli` and the exported hit sprite size as a deterministic rectangle, not Flash's exact `hitTest`.
- Heli movement and gun logic now use the inspected AS formulas, but exact parity is still blocked by missing AS `heroStart` lifecycle and unresolved casing/typo quirks.

## Intentionally Simplified For Now
- No crates, health drops, ammo drops, weapon switching, non-basic weapons, explosions, shards, blood, sounds, bullet time, or full gameover/HUD simulation.
- Gun rendering uses the original FFDEC weapon sprite frame `DefineSprite_107/1.png`; bullet rendering uses `assets_ffdec/images/35.png`.
- Reward is a simple survival baseline.
- Replay schema records actions and state hashes for the current Python simulator; it is not an AS parity trace format.
- `scripts.record_scripted_trace` generates deterministic Python-only movement traces for manual Flash comparison; these traces do not prove AS parity by themselves.

## Needs Later Verification
- Compare scripted traces for idle, walk right, jump, double jump, duck/stand, and hyperjump against original Flash behavior before freezing golden traces.
- Player bitmap registration and walk animation cadence.
- Headless-to-GUI replay determinism after combat/enemies are added.
- Exact camera and background scroll behavior.
