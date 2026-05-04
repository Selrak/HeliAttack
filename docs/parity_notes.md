# HA2 Parity Notes

## AS Audit - 2026-05-04

Inspected source: `heliattack2_scripts/ha2_core_logic/frame_19_DoAction_2.as`.

- Player setup/spawn: `drawMap`, `assignents`, `heroSetup`, and `heroStart` create `hero`, clear map collision marker `32`, set `player._x = x * tileWidth + tileWidth / 2`, set `player._y = -50`, and initialize `width=48`, `height=48`, `defplayerwidth=10`, `defplayerheight=42`, `jump`, `jump2`, `duck`, `hyperjump=150`. Python appears matching for steady-state spawn/setup, but does not model the AS parachute/start transition before `heroAction`.
- Movement/jump/duck/hyperjump: `heroAction` uses `leftkey`, `rightkey`, `duckKey`, `jumpkey`, and `boostKey`; acceleration, damping, velocity clamps, jump hold, double-jump gating, hyperjump charge/use, and ground/ceiling snap formulas are closely mirrored in Python. Status: mostly matching.
- Casing quirk: setup defines lowercase `defplayerwidth`/`defplayerheight`, while action code reads mixed-case `defPlayerWidth`, `playerWidth`, and lowercase `playerwidth`/`playerheight`. As decompiled, this is internally inconsistent. Python normalizes to working lowercase fields, which likely preserves intended behavior but masks the exact Flash/decompiler casing question. Status: unresolved without bytecode or live Flash traces.
- Collision and bounds: AS `hitCheck(mapa, cy, cx, cy2, cx2, type, equal, hold)` directly indexes `mapa[y][x][0]`; `heroAction` manually guards horizontal world bounds before `hitCheck` but not every vertical probe. Python bounds-checks in `_hit_check`, so it is safer than the literal AS and may hide edge quirks. Status: movement collisions are close, edge behavior uncertain.
- Animation frames: AS sets `this.gfx.gotoAndStop(1)` idle, `2` duck, `3` first jump, `4` walk, `5` double jump, `6` chute/start; walk advances nested `this.gfx.gfx.nextFrame()` once per movement tick. Python uses colored FFDEC bitmap exports for idle/duck/jump/walk/double-jump and alternates walk bitmaps by tick cadence. Status: state-frame mapping is justified; exact nested walk cadence and registration remain uncertain.
- Mirroring: inspected player body animation code does not set player/gfx `_xscale`; only gun/chute-related scales appear. Python not mirroring the body appears AS-backed. Status: matching.
- Camera/background: AS updates `world._x/_y` only when `heroAction` threshold checks trigger, then clamps through `scrollMap`; `bglayer1._x` scrolls by half the world delta and wraps, and `bglayer1._y` depends on `(-world._y) / maxheight`. Python uses a stateless centered/clamped camera and simpler parallax. Status: known mismatch/approximation; not changed here because a faithful fix needs stateful Flash-style camera variables.
- Map/tile rendering: AS `drawMap` attaches `(stw + 1) x (sth + 1)` reusable tiles at `x * tileWidth - 1`, `y * tileHeight - 1`, using `arr[y][x][1] + 1`. Python uses the same FFDEC tile frame mapping and `-1` offset but draws visible tiles directly instead of recycling movie clips. Status: visual mapping likely close; scrolling implementation differs.

## Believed To Match Current AS Translation
- Player spawn uses `map[y][x][0] == 32`, sets `x = tile * 50 + 25`, and starts at `y = -50`.
- Runtime map setup now clears `32` spawn markers to `0`, matching AS `assignents()`.
- Core movement values currently match the inspected AS2 constants: width `48`, height `48`, player hitbox `10 x 42`, gravity increment `+1`, walk acceleration `1`, walk clamp near `5`, velocity clamp near `6`, jump hold `6`, jump impulse `-8`, hyperjump charge `150`, and hyperjump impulse `-32`.
- Current collision math follows the inspected `heroAction` tile probes and pixel snap formulas.
- Tile rendering uses FFDEC `DefineSprite_318_tiles` frames with AS mapping `map_graphic_index + 1` and the original `-1` draw offset.
- The left world boundary can leave part of the visible sprite outside the world because AS collision uses a narrow centered hitbox and snaps `_x` using the logical `width=48`, not the full visible body.
- Player body rendering does not mirror on left/right movement; inspected AS did not show a hero body `_xscale` flip. Walking currently alternates colored bitmap exports `126.png` and `128.png`.

## Uncertain
- Decompiled AS uses mixed variable casing such as `defplayerwidth` in setup and `defPlayerWidth` in action, plus `playerWidth`/`playerwidth`. Current Python uses the lowercase working fields from the previous port; exact Flash runtime behavior needs verification.
- `hitCheck` in AS assumes map indexes are valid. Current Python bounds-checks indexes, preserving prior port behavior but possibly hiding original edge behavior.
- Player rendering uses colored FFDEC bitmap image exports centered in the logical 48x48 hero box. Exact Flash registration point and walk animation cadence should still be verified.
- Camera/parallax currently approximates visible behavior and does not match the stateful AS `world._x/_y` threshold camera.

## Intentionally Simplified For Now
- No crates, health drops, ammo drops, weapon switching, non-basic weapons, helicopter AI, projectile systems, or score/combat simulation.
- Reward is a simple survival baseline.
- Replay schema records actions and state hashes for the current Python simulator; it is not an AS parity trace format.
- `scripts.record_scripted_trace` generates deterministic Python-only movement traces for manual Flash comparison; these traces do not prove AS parity by themselves.

## Needs Later Verification
- Compare scripted traces for idle, walk right, jump, double jump, duck/stand, and hyperjump against original Flash behavior before freezing golden traces.
- Player bitmap registration and walk animation cadence.
- Headless-to-GUI replay determinism after combat/enemies are added.
- Exact camera and background scroll behavior.
