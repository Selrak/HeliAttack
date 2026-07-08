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

## Heli Visual Frames And Destruction - 2026-06-02

- `reference_exports/ffdec_ha2/symbol_class/symbols.csv` maps `111;"Heli"`.
- `DefineSprite_111_Heli` has two stopped frames. Frame 1 places visible Heli body character `79`, gun `107`, and hit `109`; frame 2 places visible Heli body character `110`, the same gun, and mirrored hit.
- `DefineSprite_111_Heli/frame_1/DoAction.as` contains `stop();` and `hit._visible = 0;`; frame 2 hides `hit`.
- Main AS creates Helis with `temp.gotoAndStop(random(2) + 1)`.
- Current finding: HA2 Helis do not have proven rotor animation. The apparent rotor motion is static blur baked into the visible Heli body frames; do not add rotor animation unless later evidence contradicts this.
- Heli death in `heliFrame` attaches visual clips in order: 3 `Shard`, `GuyBurned`, `HeliDestroyed`, then `boom`.
- The HeliDestroyed setup assigns `temp.yseed = this.yspeed`; exported p-code also uses `yseed`, while `heliFall` reads `this.yspeed`. Treat this as a real AS typo until live Flash evidence proves otherwise.

## Player Death Presentation - 2026-06-10

- Main AS `frame_19_DoAction_2.as` checks `Key.isDown(suicideKey) || player.health <= 0 || gameover` in the gameover branch.
- On `gameover == 1`, AS records the player center and depth, removes the player clip, attaches `guyBurned` as `player`, places it at the recorded center, assigns `player.action = heroDie`, sets `player.xspeed = -10 + random(20)`, and sets `player.yspeed = -random(10)`.
- The same branch attaches `boom` at the player center, sets `_xscale = _yscale = 800`, calls `stop()`, and assigns `animationFrame`.
- `heroDie(timeStep)` clears HUD ammo/reload/bullet-time/hyperjump/powerup visuals, applies gravity, rotates by `abs(xspeed + yspeed)`, moves and bounces against map tiles, and recenters `world._x` / `world._y` on the burned player.
- Main game speed logic slows the SWF while `gameover` is true by reducing `sendGameSpeed` toward a floor of `0.2`.
- After `gameover > 200` or when enemy/entity arrays are empty, AS stops `onEnterFrame` and attaches `stats` at `(81, 80)`. Python currently implements only the render-only burned-player plus boom presentation and leaves stats/gameover UI for a later task.
- Symbols/assets: `symbols.csv` maps `76;"guyBurned"`, `137;"hero"`, and `303;"stats"`. Python uses `assets_ffdec/sprites/DefineSprite_76_guyBurned/1.png` and `assets_ffdec/sprites/DefineSprite_34_Boom/1.png` through `10.png`.

## Sound Mappings - 2026-06-10

- Manual FFDEC sound exports were inspected under `reference_exports/ffdec_ha2/sounds/`.
- Exported filenames include SWF sound ids and AS names; runtime copies now live under `assets_ffdec/sounds/`.
- Runtime sound files copied: `sgun.mp3` from `370_sgun.mp3`, `sheliboom.mp3` from `380_sheliboom.mp3`, `shurt.mp3` from `369_shurt.mp3`, `sboom.mp3` from `365_sboom.mp3`, `sbigboom.mp3` from `378_sbigboom.mp3`, `sheli.mp3` from `379_sheli.mp3`, `smusic.mp3` from `381_smusic.mp3`, `shjump.mp3` from `382_shjump.mp3`, and `smetal0.mp3` through `smetal3.mp3` from `374_smetal0.mp3` through `377_smetal3.mp3`.
- `heliattack2_scripts/ha2_core_logic/frame_19_DoAction.as` initializes `sboom`, `ssmallboom`, `sheliboom`, `sbigboom`, `shurt`, `sgun`, `shjump`, `smetal0` through `smetal3`, `sheli`, and `smusic` through `SoundBoard.newSound(...)`.
- `ssmallboom` aliases `sboom` at volume 50. `shit0` through `shit3` alias `smetal0` through `smetal3` at volume 75.
- AS use sites confirmed in `frame_19_DoAction_2.as`: MachineGun uses `sgun`; Heli death calls `sheliboom.start(0,0)`; player damage calls `shurt.start(0,0)`; HyperJump calls `shjump.start(0,0)` in the same branch that sets `this.yspeed = -32`.
- AS starts `sheli` as a long loop at volume 0 during `game()` setup and updates per-Heli volume with `75 * (1 - clamp(distance / 800, 0, 1))`. AS starts `smusic` as a long loop at volume 50 in menu/end-game paths.
- Current Python runtime emits current implemented one-shot gameplay sound events: `sgun`, `sheliboom`, `shurt`, and HyperJump-only `shjump`. Generic explosion, metal-hit, unimplemented weapon, and powerup sounds are documented/deferred and are not emitted by the event queue.
- Current Python GUI viewers implement first-pass `smusic` and `sheli` loops in `ha2_sound.SoundPlayer`. Loop state is viewer-only and not part of HA2 env state.
- No footstep, ordinary-jump, or landing sound trigger was observed in the inspected AS movement path.
- `ha2_gui.py` uses the `gameover` speed finding only for GUI-side post-player-death presentation: user GUI speed and gameover slowdown are multiplied, and render-only effects advance without delaying Gym/RL termination.

## Player Damage Blood - 2026-06-10

- `symbols.csv` maps `30;"Blood"`.
- `frame_19_DoAction_2.as` `enemyBulletFrame` subtracts `10` health from the player on enemy-bullet hit, then attaches three `blood` clips.
- Each blood clip is placed at `player._x + player.width / 2`, `player._y + player.height / 2`, gets `random(360)` rotation, uses `action = animationFrame`, calls `stop()`, and gets `pause = i * 2`.
- Runtime blood frames are present at `assets_ffdec/sprites/DefineSprite_30_Blood/1.png` through `12.png`.
- Python implements these as render-only `visual_effects` using deterministic visual-only rotation sampling and pause offsets `0`, `2`, and `4`.
