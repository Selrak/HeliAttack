# Current State

Last updated: 2026-05-14 Europe/Paris

## What Appears to Work
- Python 3.11.9 is available locally; `.venv` has pytest and SB3 installed.
- Core Python files and new scripts compile.
- Headless env reset/step works and measured about 44,982 steps/sec in one local smoke run.
- `rgb_array` render smoke works with shape `(320, 450, 3)`.
- JSONL replay record/verify works for `replays/smoke.jsonl`.
- Playable GUI, replay GUI, screenshot hotkey, side-panel debug display, FFDEC tile/player rendering, and SB3 train/evaluate/watch entry points now exist.
- `play_human` startup was reduced by avoiding broad `pygame.init()`; local profile reached first render in about 0.78s.
- Scripted movement trace generation exists for idle, walk right, jump hold, double jump, duck/stand, and hyperjump.
- Default MachineGun firing exists with AS constants, deterministic env-local spread RNG, bullet state hashing/replay debug, Pygame bullet rendering, and `fire_right_60` scripted trace.
- MachineGun is rendered from `assets_ffdec/sprites/DefineSprite_107/1.png` and uses FFDEC gun/barrel placement data for visual registration. Bullet spawn logic was not changed in the visual placement pass.
- Continuous Heli combat exists: default Heli queues on reset and spawns after first ground contact, dead Helis are removed, kill counters update, and replacement Helis spawn with AS-style `addEnemy` coordinates.
- Heli combat includes AS-backed `heliFrame` movement/gun aiming/shoot cadence, nested Heli gun rendering, enemy bullets, player health damage, MachineGun-to-Heli damage, state hashing, and scripted traces.
- `heli_shoots_hero_240` now deterministically shows enemy bullet damage: initial health 100, final health 90, first damaging enemy bullet id 12 at frame 240.
- `kill_heli_respawn_600` deterministically shows Heli death plus replacement spawn.
- Heli rendering composes visible FFDEC bitmaps `images/78.png` and `images/77.png`; the green `Heli.hit` child is not rendered by default.
- Player healthbar HUD renders with original FFDEC healthbar bitmaps and the AS bottom-anchored mask-scale rule.
- `scripts.play_human` accepts both `WASD` and `ZQSD` movement keys, and its mouse input helper falls back cleanly when no video system is active.
- `scripts/export_ffdec_reference.ps1` can export broad FFDEC reference data from a SWF and auto-detects `C:\Program Files (x86)\FFDec\ffdec-cli.exe`.
- `training_profile="combat_v1"` is available as an opt-in RL interface: 37-field bounded float32 vector observation, combat-aware reward, player-death/fall termination, and max-step truncation.
- `training_profile="combat_bullets_v1"` is available, extending the observation to 84 dimensions by replacing the single nearest bullet with a top-10 visible bullet block to enable defensive maneuvering.
- `scripts.train_parkour`, `scripts.evaluate_model`, and `scripts.watch_model` default to `combat_v1` with `max_episode_steps=1800` but support `combat_bullets_v1`.
- Experiments are now the default unit of RL artifact storage: `scripts.train_parkour` creates `experiments/ha2_000001_YYYYMMDD_HHMM_combat-v1_1k/`-style runs with `config.json`, `git_info.txt`, `summary.md`, `models/`, `reports/`, `replays/`, and `tensorboard/`.
- `scripts.evaluate_model` can resolve `best` and `latest` model files from an experiment and writes eval reports/replays inside that experiment by default.
- `scripts.watch_model` can resolve experiment-scoped `best` and `latest` models and can auto-name optional replay/GIF outputs under the experiment.
- `scripts.play_replay` and `scripts.watch_model` now support an `F` fast-forward toggle for faster GUI inspection.
- Visual startup was profiled again on 2026-05-14. Normal env first-render startup is still mostly import-bound at about `0.68-0.72s` in dummy video mode; `watch_model` with a real model is dominated by SB3 import and model load at about `5.8s` total.
- `watch_model` now defers Pygame/env/replay imports until after model path resolution and SB3 model load, and GIF NumPy import remains lazy.
- Pygame support prompt output is suppressed before Pygame import in the visual entry points and env module.
- `scripts.run_experiment` is now available as a bounded training orchestration layer that runs training and then evaluation on both the `best` and `latest` models, producing a complete experiment folder and an updated `summary.md`.
- `scripts.train_parkour` and `scripts.run_experiment` support optional `--vec-env dummy|subproc`; the default remains `dummy`.
- `scripts.train_parkour` supports `--train-eval on|off`, `--eval-freq`, `--train-eval-episodes`, and `--eval-vec-env dummy|subproc|same`.
- `scripts.benchmark_vec_envs` supports `--mode train-only|workflow|both`, records eval wrapper match/warning status, and writes JSON/Markdown reports under `reports/vec_env_benchmarks/`.
- `ha2_env.py` tracks detailed firing metrics and movement diagnostics (grounded/airborne frames, boost activations, lateral range).
- `scripts.train_parkour` and `scripts.run_experiment` support `--net-arch` for custom PPO policy network sizes.
- `scripts.evaluate_model` produces an evaluation JSON report that includes aggregate combat diagnostics, movement metrics, and policy capacity metadata.
- Evaluation now includes visible enemy-bullet diagnostics, top-10 visible-bullet pressure counters, damage timing, and damage-free streak metrics. Off-screen enemy bullets are excluded from the player-visible defensive denominator.
- `docs/ai/OBSERVATION_AUDIT.md` documents that `combat_v1` exposes one nearest engine-side enemy bullet, including velocity, but not all visible bullets.
- Experiments can now be synchronized across machines using WandB Artifacts. `scripts.run_experiment` (with `--wandb on`) automatically uploads the experiment folder, and `scripts.sync_experiment` downloads it to other machines.
- Local configuration via `.env` is supported for setting `WANDB_API_KEY`, `WANDB_ENTITY`, and `WANDB_PROJECT` on a per-folder basis.
- Charles manually exercised GUI play/replay checks after the scripted trace phase and reported they looked OK.

## What Is Unknown
- SB3 smoke runs, but model quality is not meaningful from the 1000-step validation run.
- Scripted traces are Python simulator traces only; they have not been compared against Flash yet.
- AS bit-for-bit parity is a goal, but no parity test harness was found.
- GIF recording still needs manual validation.
- MachineGun GUI firing/replay rendering still needs Charles manual feel/parity checks.
- New Heli gun/enemy-bullet GUI feel still needs Charles manual checks.
- `scripts.watch_model` manual GUI validation was not run during the experiment-directory pass.
- Fast-forward GUI behavior has not yet been manually evaluated for feel or frame pacing.
- SubprocVecEnv works in Windows smoke runs, including `--eval-vec-env same`; local tiny benchmarks still favor DummyVecEnv by wall-clock.
- The new defensive diagnostics need review on real 500k experiments; current validation only used a 1000-step smoke model.

## Current Architecture
- `ha2_env.py` contains the main runtime architecture: environment state, player physics, default MachineGun/bullets, one default Heli enemy target, collision checks against `const.FULL_MAP_DATA`, rendering, and state/hash debug hooks.
- `ha2_replay.py` provides deterministic JSONL replay writing/loading/verification.
- `scripts/` contains manual play, replay, screenshot, and SB3 pipeline entry points plus `scripts/experiment_utils.py` for experiment directory/path resolution.
- `tests/` contains pytest smoke tests.
- `ha2_constants.py` is generated static data for map and core movement constants.
- `extract_ha2_data.py` is the data extraction bridge from decompiled AS to generated Python constants.
- `heliattack2_scripts/` is the source-of-truth reference for original HA2 ActionScript behavior.
- `assets_ffdec/` provides current FFDEC-exported assets for rendering.

## Migration or Refactoring State
- The project appears to be in an early HA2 foundation phase.
- Minimal replay/test/training scaffolding was added; serious training is still deferred.
- The RL artifact layout has moved from root-level `models/` and `reports/` outputs to experiment-scoped directories by default; root-level compatibility remains only for ad hoc/manual use.
- No HA3 implementation was found during bootstrap inspection.

## Current Risks and Unclear Points
- Camera now has minimal AS-style stateful `world_x/world_y/worldpos` for Heli/projectiles; parallax and full `heroStart` lifecycle remain simplified.
- MachineGun visual placement now uses Charles-provided FFDEC metadata; exact visual parity still needs manual Flash comparison.
- Projectile active-region removal uses Python `worldpos/stw/sth` plus tile collision.
- Heli spawn timing is now a first-ground-contact proxy for AS `heroStart`, not the full parachute/start lifecycle.
- Heli hitbox still uses FFDEC `Heli.hit` placement metadata but remains a rectangle approximation of Flash `hitTest`.
- Heli death respawn is implemented; non-training side effects remain omitted: pickups, drops, random weapon rewards, explosions, shards, blood, sounds, and bullet-time refill.
- Only the original player healthbar HUD is implemented; score/time/ammo/reload/hyperjump HUD composition remains future work.
- `combat_v1` is an RL interface layer only; it does not prove AS parity or tune PPO behavior.
- `combat_v1` defensive visibility diagnostics use bullet center plus an 8 px margin against the gameplay viewport; exact Flash sprite visibility is not proven.
- Player bitmap registration, nested walk cadence, AS casing quirks, and edge `hitCheck` behavior remain uncertain; see `docs/parity_notes.md`.
- The generated constants file is large and should not be edited manually without a clear reason.
- Future sessions must check `git status` before editing and avoid reverting user work.

## Manual Control Update
- `scripts.play_human` supports `F12` screenshots saved as incrementing PNG files under `screenshots/` by default.
- Debug text is rendered in a right-side panel so it does not cover the game area.

## Handoff Behavior
- Future Codex sessions should ask clarification questions instead of making hypotheses when requirements are unclear.
- Future `docs/ai` updates should be succinct and limited to durable facts, validation, blockers, risks, and next actions.
