# HA2 Parity Notes

## AS Audit - 2026-05-04

Inspected source: `heliattack2_scripts/ha2_core_logic/frame_19_DoAction_2.as`.

- Player setup/spawn: `drawMap`, `assignents`, `heroSetup`, and `heroStart` create `hero`, clear map collision marker `32`, set `player._x = x * tileWidth + tileWidth / 2`, set `player._y = -50`, and initialize `width=48`, `height=48`, `defplayerwidth=10`, `defplayerheight=42`, `jump`, `jump2`, `duck`, `hyperjump=150`. Python now models the AS-backed parachute/start transition when `skip_intro=False`.
- Movement/jump/duck/hyperjump: `heroAction` uses `leftkey`, `rightkey`, `duckKey`, `jumpkey`, and `boostKey`; acceleration, damping, velocity clamps, jump hold, double-jump gating, hyperjump charge/use, and ground/ceiling snap formulas are closely mirrored in Python. Status: mostly matching.
- Casing quirk: setup defines lowercase `defplayerwidth`/`defplayerheight`, while action code reads mixed-case `defPlayerWidth`, `playerWidth`, and lowercase `playerwidth`/`playerheight`. As decompiled, this is internally inconsistent. Python normalizes to working lowercase fields, which likely preserves intended behavior but masks the exact Flash/decompiler casing question. Status: unresolved without bytecode or live Flash traces.
- Collision and bounds: AS `hitCheck(mapa, cy, cx, cy2, cx2, type, equal, hold)` directly indexes `mapa[y][x][0]`; `heroAction` manually guards horizontal world bounds before `hitCheck` but not every vertical probe. Python bounds-checks in `_hit_check`, so it is safer than the literal AS and may hide edge quirks. Player health depletion is now a universal evolving-simulator death rule, but sideways world escape is not treated as a normal HA2 fall-death rule. Status: movement collisions are close, edge behavior uncertain.
- Animation frames: AS sets `this.gfx.gotoAndStop(1)` idle, `2` duck, `3` first jump, `4` walk, `5` double jump, `6` chute/start; walk advances nested `this.gfx.gfx.nextFrame()` once per movement tick. Python uses colored FFDEC bitmap exports for idle/duck/jump/walk/double-jump and alternates walk bitmaps by tick cadence. Status: state-frame mapping is justified; exact nested walk cadence and registration remain uncertain.
- Mirroring: inspected player body animation code does not set player/gfx `_xscale`; only gun/chute-related scales appear. Python not mirroring the body appears AS-backed. Status: matching.
- Camera/background: AS updates `world._x/_y` only when `heroAction` threshold checks trigger, then clamps through `scrollMap`; `bglayer1._x` scrolls by half the world delta and wraps, and `bglayer1._y` depends on `(-world._y) / maxheight`. Python now keeps stateful `world_x/world_y/worldpos` for Heli/projectile logic and rendering, but parallax remains simplified.
- Map/tile rendering: AS `drawMap` attaches `(stw + 1) x (sth + 1)` reusable tiles at `x * tileWidth - 1`, `y * tileHeight - 1`, using `arr[y][x][1] + 1`. Python uses the same FFDEC tile frame mapping and `-1` offset but draws visible tiles directly instead of recycling movie clips. Status: visual mapping likely close; scrolling implementation differs.
- MachineGun: AS `heroSetup` initializes `guns[0]` with infinite bullets and `cgun=0`; global `guns[0]` is `MachineGun` with `reloadtime=5`, `speed=8`, and `damage=10`. AS firing uses `mouseD`, increments reload while the game is moving, fires when reload is ready, uses `gun.barrell.localToGlobal`, and `machineGun` spawns `bulletFrame` frame `1` with `rot - 2 + random(4)`. Python now mirrors the cadence, constants, deterministic local spread, bullet velocity, tile/world-bounds removal, and replay hashing. Status: functional first slice.
- Heli enemy: Python queues the default Heli during AS intro and spawns it when the chute closes; `skip_intro=True` starts grounded and spawns the Heli immediately for training/scripts. It implements AS-style `heliFrame` target/acceleration/damping/gun-aim/shoot cadence, deterministic env-local spread, enemy bullets, player damage, player-bullet damage, score/hit/kill counters, and Heli/enemy-bullet state hashing. Status: AS-backed first combat loop.
- Heli visual: FFDEC `DefineSprite_111_Heli` has two stopped frames and is rendered from visible body `images/78.png` plus pilot `77.png`; the green hidden `hit` child is collision-only. The nested gun uses `DefineSprite_107/1.png`, Heli gun placement `(11,7)` / `(-9,7)`, and MachineGun `barrell` `(22.7,-7.4)`. No rotor animation is implemented: current FFDEC/AS evidence indicates the apparent rotor motion is static blur baked into the two Heli body frames.

## AS Audit - 2026-05-05 Heli Combat Loop

- Implemented equations from AS `heliFrame`: `stepc`, `xt/yt`, `xdif`, `tx/ty`, offscreen acceleration divisors, `rotation=floor(xspeed/20*15)`, damping, gun target angle, shortest-angle smoothing by `max(1,10-level)`, y-flip, and shoot cadence `shoot++ % max(10,16-level) == 1`.
- Implemented AS `addEnemyBullet` / `enemyBulletFrame` behavior for speed 7, `rotation - 5 + random(10)`, solid-tile/active-region removal, player hit detection, and `health -= 10`. Player damage now emits GUI-only `shurt` and spawns three render-only Blood clips with AS pause offsets `0`, `2`, and `4`; red hit flash/color transform remains omitted.
- Implemented gameplay-essential Heli death/respawn from AS `heliFrame`: remove dead Heli, increment `helis`/`rthelis`, and call AS-style `addEnemy(300)` for the next target. Visual-only Heli destruction effects now spawn AS-backed shards, a burned pilot, a falling Heli wreck, and boom frames. Random weapon popup, powerup/drop handling, and bullet-time refill remain omitted. Heli destruction now emits GUI-only `sheliboom`; broader sound parity remains deferred.
- P-code confirms the decompiled `timeSetp` typo exists. Python uses `timeStep=1` for Heli y-damping rather than reproducing an undefined-name failure; exact Flash runtime effect still needs live comparison.
- AS reads both `onScreen` and `onscreen`; Python uses lowercase `onscreen` consistently so the Heli combat loop remains functional. This casing quirk needs Flash verification.

## AS Audit - 2026-05-05 Heli Startup/Damage Fix

- AS `heroStart` calls `addEnemy(300)` only after the chute closes and gameplay switches to `heroAction`; Python now implements this in the default `skip_intro=False` mode.
- The startup dart was caused by reset-time Heli spawn: early `heliFrame` Y targeting used the still-falling player Y, producing a large negative target before the Heli came back down.
- Enemy bullet damage was mechanically present, but not visible enough in traces/overlay. Debug state and scripted summaries now report player health, last damage, and the first damaging enemy bullet/frame.

## AS Audit - 2026-05-05 Continuous Heli Combat

- AS `heliFrame` calls `addEnemy(300)` after Heli death if `!gameover`; Python now respawns a replacement Heli immediately in the same simulator step.
- AS increments `helis` and `rthelis` on death. Python increments both once per killed Heli; `rthelis` is the total-kill counter shown in trace summaries.
- AS HUD updates `HUD.score`, `HUD.time`, and `HUD.health.mask._yscale`; Python now renders Time/Helis, Score, High Score, `Health:`, `HyperJump:`, `Reload:`, the starting MachineGun icon, and the player healthbar from FFDEC bitmaps `170.png`/`174.png`, using the extracted `standard 07_63` HUD font.
- Python now terminates the evolving simulator with `termination_reason="player_death"` whenever player health reaches `<= 0`, independent of `training_profile`. Rewards remain profile-specific.

## AS Audit - 2026-05-19 Collision / HitTest Investigation

- AS player projectiles use `enemyArray[i].hit.hitTest(this._x + world._x,this._y + world._y,1)` against the Heli nested `hit` clip, not a Python-style rectangle test.
- AS enemy projectiles use `player.gfx.hit.hitTest(this._x + world._x,this._y + world._y,1)` against the current player graphics nested `hit` clip.
- FFDEC SVG exports now confirm non-rectangular hidden hit shapes for Heli `DefineSprite_109`, standing player `DefineSprite_119`, and duck player `DefineSprite_123`.
- Current Python projectile collision defaults to FFDEC polygon hit shapes; explicit rectangle collision remains available for comparisons.

## AS Audit - 2026-05-19 FFDEC Polygon Collision Model

- `collision_model="ffdec_polygon"` is now the evolving simulator default for projectile hit tests.
- `collision_model="rect"` remains available explicitly for comparisons and legacy-style runs.
- Heli frame 1 applies the `hit` child matrix translation `(-104.5,-52.55)`.
- Heli frame 2 applies the `hit` child matrix `scaleX=-1`, `scaleY=1`, translation `(103.5,-52.0)`.
- Heli parent rotation is applied around the current Heli registration point before world translation.
- Player polygon placement uses the standing `gfx.hit` offset `(12.65,1.2)` for non-duck states and the duck offset `(12.85,7.35)` for duck.
- Player polygon hit tests include the exported 1 px outline stroke as a deterministic 0.5 px segment-distance check. Heli hit tests are fill-only.
- Exact Flash `hitTest` semantics still need targeted Flash validation; `ffdec_polygon` is the current default but may still need parity refinements.

## AS Audit - 2026-06-02 Heli Visual Destruction

- `symbols.csv` maps `111;"Heli"`, and `DefineSprite_111_Heli` has `frameCount="2"`. Frame 1 places visible Heli body character `79`, gun `107`, and hit `109`; frame 2 places visible Heli body character `110`, the same gun, and mirrored hit. The Heli frame scripts call `stop()` and hide `hit`; the main AS creates Helis with `gotoAndStop(random(2) + 1)`. Status: no rotor animation is evidenced; rotor blur appears baked into static body frames.
- On Heli death, AS attaches 3 `Shard` clips, then `GuyBurned`, then `HeliDestroyed`, then `boom`. Python now preserves that render order in a visual-only `visual_effects` list using original FFDEC assets.
- Destruction assets used: `DefineSprite_237_Shard/1.png` through `6.png`, `DefineSprite_76_guyBurned/1.png`, `DefineSprite_115_HeliDestroyed/1.png` and `2.png`, and `DefineSprite_34_Boom/1.png` through `10.png`.
- Python implements AS-style shard gravity/rotation/bounces, burned-pilot falling/bouncing, Heli wreck gravity/rotation, terrain-triggered secondary wreck boom/shards, and boom frame advancement. Effects do not collide with gameplay objects and are excluded from `state_hash` so old replay hash semantics remain compatible.
- AS death setup assigns `temp.yseed = this.yspeed`, while `heliFall` reads `this.yspeed`. Python preserves the source value as `as_yseed` metadata and starts the wreck's effective `yspeed` at `0.0`; live Flash behavior of this typo remains a visual parity risk.
- Heli-death visual random values use deterministic hash-based visual sampling so debris does not consume the gameplay RNG used for Heli respawn or combat.
- Guardrail audit: `visual_effects` and `next_visual_effect_id` are render/replay-only state. They may be serialized in `get_state()` and restored by `set_state()` for deterministic visual playback, but observations, rewards, termination, score, projectile/player/enemy collisions, Heli AI, and gameplay state hashes do not read them. Old states without these fields load with an empty visual-effect list.

## AS Audit - 2026-06-10 Player Death Presentation

- Main AS gameover logic checks `Key.isDown(suicideKey) || player.health <= 0 || gameover`. On `gameover == 1`, it stores the player center/depth, removes the player clip, attaches `guyBurned` as `player`, sets `player.action = heroDie`, assigns `xspeed = -10 + random(20)` and `yspeed = -random(10)`, and attaches `boom` at the same position with `_xscale = _yscale = 800`.
- Python implements this as render-only state: player death spawns a `player_burned` visual effect using `assets_ffdec/sprites/DefineSprite_76_guyBurned/1.png` and an 800% boom using `assets_ffdec/sprites/DefineSprite_34_Boom/1.png` through `10.png`. The live player/gun are suppressed only during rendering while the burned-player effect is active; gameplay state is unchanged.
- `heroDie` updates gravity, rotation, x/y movement, and tile bounces, and recenters the Flash world on the burned player. Python advances the burned-player effect with the same visual fall/bounce style but deliberately does not move `world_x`, `world_y`, camera, player, Helis, bullets, score, health, or rewards during render-only advancement.
- `advance_visual_effects_only()` exists for viewers to animate terminal visual effects after Gym termination. It updates only `visual_effects` / `next_visual_effect_id`; gameplay hashes exclude those fields.
- Live player/gun rendering is suppressed whenever the env is already terminal for `player_death`, using `last_terminated` and `last_termination_reason`. This keeps the live player from reappearing after finite render-only effects expire, and reset restores normal live-player rendering. No new serialized render flag is used.
- Original AS eventually attaches `stats` after `gameover > 200` or entity cleanup. Python does not implement the stats/gameover menu yet. `scripts.play_human` instead holds the terminal presentation and restarts manually with `R` or `Enter`.

## GUI Viewer Policy - 2026-06-12

- `ha2_gui.py` centralizes common GUI behavior for `scripts.play_human`, `scripts.watch_model`, and `scripts.play_replay`.
- Common GUI speed factors are `0.25x`, `0.5x`, `1x`, `2x`, `4x`, and `8x`. `F` increases speed, `Shift+F` decreases speed, and `1` resets to `1x`.
- Common GUI keys are: `Esc` quit; `Enter`/`R` restart from terminal state; `P`/`Space` pause; `N` single-step; `F1` debug/help overlay; `F3` collision overlay where applicable. `play_human` keeps its mode-specific mouse aim/fire and `F12` screenshot behavior.
- During active gameplay/replay, GUI speed changes only wall-clock presentation cadence. It does not change `env.step()`, physics, observations, rewards, collisions, score, RNG, replay verification, or `state_hash()`.
- During post-`player_death` GUI presentation, Python composes `effective_visual_speed = user_gui_speed_factor * gameover_slowdown_factor`. The GUI-only slowdown factor tends toward `0.2x`, matching the AS evidence that `gameover` lowers `sendGameSpeed` down to `0.2`.
- Post-player-death GUI presentation does not call normal `env.step()`; it advances only render-only effects through `advance_visual_effects_only()`. `watch_model` now holds terminal player death like `play_human`; `play_replay` holds terminal replay states and restarts from the beginning with `Enter`/`R`.
- HUD remains centralized through `ha2_env.render()`. The GUI scripts pass debug/help lines into the existing render path and do not draw duplicate gameplay HUD elements.
- `sheli` diagnosis/repair: the runtime manifest and `sheli.mp3` exist, loop channels start through `SoundPlayer.start_loop(..., loops=-1)`, and `set_loop_volume()` updates the active channel. The viewer-side volume calculation returns nonzero volume for close live Helis and zero volume for no live Heli or terminal state. Manual host-audio audibility still needs GUI verification.

## AS Audit - 2026-06-10 Sound Assets And First GUI Playback

- Manually exported SWF sounds live in `reference_exports/ffdec_ha2/sounds/`; committed runtime sounds now live in `assets_ffdec/sounds/` and are described by `assets_ffdec/sounds/manifest.json`.
- Exported filenames already include SWF sound ids and AS names. The copied runtime subset is: `sgun.mp3`, `sheliboom.mp3`, `shurt.mp3`, `sboom.mp3`, `sbigboom.mp3`, `shjump.mp3`, `sheli.mp3`, `smusic.mp3`, and `smetal0.mp3` through `smetal3.mp3`.
- AS sound setup in `frame_19_DoAction.as` maps `sboom`, `ssmallboom`, `sheliboom`, `sbigboom`, `shurt`, `sgun`, `shjump`, `smetal0` through `smetal3`, `sheli`, and `smusic` through `SoundBoard.newSound(...)`. `ssmallboom` uses `sboom` at volume 50, and `shit0` through `shit3` alias the metal sounds at volume 75.
- Current runtime event playback remains narrower than the manifest. `ha2_env.py` emits transient sound events only for currently implemented gameplay events: `sgun` for the starting MachineGun, `sheliboom` for Heli destruction, `shurt` for player damage, and `shjump` only for HyperJump / boost when the AS-backed `yspeed = -32` branch runs.
- Inspected AS evidence does not show footstep, ordinary-jump, or landing sound triggers in the current movement path. Python therefore does not emit movement sounds for walking, normal jump, falling, landing, or ducking.
- `smusic` and `sheli` are first-pass GUI loops owned by `ha2_sound.SoundPlayer`, not by the env. `smusic` starts in GUI viewers at AS volume 50. `sheli` starts in GUI viewers and uses a viewer-side read-only approximation of the AS distance formula `75 * (1 - clamp(distance / 800, 0, 1))`, taking the loudest live Heli and using volume 0 when terminal or no live Heli exists.
- `sboom`, `sbigboom`, and metal-hit sounds are documented/deferred but not emitted yet. Unimplemented weapons, powerups, and flamethrower loop sound are not wired for playback.
- Sound events and loops are GUI-only presentation signals. They are not serialized into replay state, are not part of `state_hash()`, and do not affect observations, rewards, termination, score, collisions, Heli AI, or gameplay RNG. `pygame.mixer` is initialized only by `ha2_sound.SoundPlayer` when a viewer script requests playback.

## AS Audit - 2026-06-10 Player Damage Blood

- `symbols.csv` maps `30;"Blood"`, and runtime blood frames are available at `assets_ffdec/sprites/DefineSprite_30_Blood/1.png` through `12.png`.
- AS `enemyBulletFrame` reduces player health by `10` and attaches three `blood` clips at `player._x + player.width / 2`, `player._y + player.height / 2`, with `random(360)` rotation, `action = animationFrame`, `stop()`, and pause offsets `i * 2`.
- Python now spawns exactly three render-only `blood` effects on the existing enemy-bullet damage site. Blood rotation uses the existing deterministic visual-only hash sampler, not gameplay RNG.
- Blood effects are stored in `visual_effects` for rendering/replay state and are excluded from gameplay state hashes, observations, rewards, termination, score, collisions, physics, and gameplay RNG.

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
- Dead Helis spawn visual-only destruction effects in AS attach order; these effects are stored/restored in state but excluded from gameplay state hashes.
- Player healthbar HUD uses original FFDEC healthbar assets and the AS `HUD.health.mask._yscale` rule.
- Health depletion terminates the evolving simulator universally with `player_death`; `training_profile` no longer controls whether the player can die.

## Uncertain
- Decompiled AS uses mixed variable casing such as `defplayerwidth` in setup and `defPlayerWidth` in action, plus `playerWidth`/`playerwidth`. Current Python uses the lowercase working fields from the previous port; exact Flash runtime behavior needs verification.
- `hitCheck` in AS assumes map indexes are valid. Current Python bounds-checks indexes, preserving prior port behavior but possibly hiding original edge behavior.
- Normal HA2 gameplay should not have a sideways fall-death rule. Current Python horizontal movement treats the left/right world sides as collision bounds; any out-of-bounds termination in the evolving simulator is a Python safety condition or legacy replay compatibility behavior unless later AS evidence proves otherwise.
- Player rendering uses colored FFDEC bitmap image exports centered in the logical 48x48 hero box. Exact Flash registration point and walk animation cadence should still be verified.
- Camera/parallax is only partly AS-style: Heli/projectiles now use stateful `world_x/world_y/worldpos`, but background parallax is still simplified.
- Gun visual registration now uses FFDEC placement data provided by Charles: hero `gun` at `(24.0, 29.0)` and MachineGun `barrell` at `(22.7, -7.4)`, giving zero-rotation visual barrel origin `(46.7, 21.6)` from the Flash hero origin. Bullet spawn registration was left unchanged in this visual-only task.
- Bullet active-region removal now uses Python `worldpos/stw/sth` plus solid-tile checks.
- `skip_intro=True` is intentionally non-AS: it starts the player grounded near the left side of the world and creates the first Heli immediately so training and scripted traces avoid intro dead time.
- Heli death side effects that are not required for MachineGun-only training are mostly omitted: random weapon rewards, powerups/drops, and bullet-time refill are not implemented. Visual-only shards, burned pilot, destroyed Heli wreck, boom, enemy-hit blood, and GUI-only `sheliboom` are implemented.
- Time/Helis, Score, High Score, original player healthbar, HyperJump, Reload, weapon icon, and ammo HUD elements are implemented. Exact Flash decorative HUD details remain future work.
- Default Heli projectile hit detection now uses the FFDEC nested `hit` shape with frame-aware mirroring and parent rotation. The legacy rectangle remains available through explicit `collision_model="rect"` and `ha2_env_legacy.py`.
- Heli movement and gun logic now use the inspected AS formulas, but exact parity is still blocked by unresolved casing/typo quirks and live Flash validation of the new `heroStart` approximation.

## Intentionally Simplified For Now
- No crates, health drops, ammo drops, weapon switching, non-basic weapons, bullet time, or full gameover/HUD simulation. First-pass visual explosions/shards/blood and GUI-only sound playback exist, but full AS sound/gameover parity remains future work.
- Gun rendering uses the original FFDEC weapon sprite frame `DefineSprite_107/1.png`; bullet rendering uses `assets_ffdec/images/35.png`.
- Reward is a simple survival baseline.
- Replay schema records actions and state hashes for the current Python simulator; it is not an AS parity trace format.
- `scripts.record_scripted_trace` generates deterministic Python-only movement traces for manual Flash comparison; these traces do not prove AS parity by themselves.

## Needs Later Verification
- Compare scripted traces for idle, walk right, jump, double jump, duck/stand, and hyperjump against original Flash behavior before freezing golden traces.
- Player bitmap registration and walk animation cadence.
- Headless-to-GUI replay determinism after combat/enemies are added.
- Exact camera and background scroll behavior.
