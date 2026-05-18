# Current State

Last updated: 2026-05-17 Europe/Paris

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
- `reward_profile` logic supports `combat_default` (base rewards) and `defense_v1` (heavy penalties for player damage, edge camping, and inefficient inputs).
- Reward profiles are now propagated through training, train-time eval, final eval, watch, and replay verification. New replay headers include `reward_profile`; replay step debug and eval reports include `reward_breakdown`.
- `pressure_profile` is available as an opt-in fire-pressure curriculum: `normal` default, `enemy_fire_slow_2x`, and `enemy_fire_slow_4x`. It scales enemy Heli fire interval only.
- Shared runtime CLI/config plumbing for `training_profile`, `control_mode`, `reward_profile`, `pressure_profile`, and `max_episode_steps` is centralized in `scripts/runtime_config.py`.
- `scripts.train_parkour`, `scripts.evaluate_model`, `scripts.watch_model`, `scripts.run_experiment`, `scripts.run_experiment_pair`, and `scripts.play_human` support `--pressure-profile`.
- Curriculum `ActionWrapper`s are implemented in `ha2_env.py`: `movement_scripted_attack_direct` (agent controls 4 movement axes) and `movement_no_boost_scripted_attack_direct` (agent controls 3 axes). Both use a deterministic heuristic to aim and fire at the primary Heli.
- Experiments are now the default unit of RL artifact storage: `scripts.train_parkour` creates `experiments/ha2_000001_YYYYMMDD_HHMM_combat-v1_1k/`-style runs with `config.json`, `git_info.txt`, `summary.md`, `models/`, `reports/`, `replays/`, and `tensorboard/`.
- `scripts.evaluate_model` and `scripts.watch_model` resolve `best`/`latest` models from an experiment and auto-detect the correct `control_mode` from `config.json`.
- `scripts.play_replay` and `scripts.watch_model` now support an `F` fast-forward toggle for faster GUI inspection.
- New replay headers include `pressure_profile`; replay verification and GUI replay instantiate with the recorded profile.
- `scripts.run_experiment` orchestrates training and evaluation, supporting `--net-arch`, `--control-mode`, `--eval-freq-timesteps`, and producing consolidated diagnostic bundles.
- `scripts.run_experiment_pair` supports comparative A/B benchmarks with individual `duration_seconds` reporting and consolidated Super-Bundles, including a `rich` TUI for parallel live monitoring.
- `ha2_env.py` tracks 25+ movement and edge-camping diagnostics (grounded/airborne frames, boost activations, lateral range, consecutive edge frames, mismatch rates), evaluated after physics execution.
- Policy architecture and parameter counts are recorded in `config.json`.
- PPO runtime timing (rollout vs training vs overhead) is tracked and reported using the `TimedPPO` subclass.
- Experiments can now be synchronized across machines using WandB Artifacts.
- `experiments/latest_experiment.txt` (or symlink) is updated at every run to point to the newest artifact directory.
- Pytest suite is optimized via `SMOKE_STEPS=16` and `@pytest.mark.slow` categorization, reducing quick-pass time from >2min to ~10s.
- Charles manually exercised GUI play/replay checks and reported they looked OK.

## What Is Unknown
- SB3 model quality is not meaningful from the 100k curriculum runs; agents mostly learn to charge right with the auto-aim.
- The 2026-05-17 slow4 100k M0/M1 run completed; M1 used boost and had lower damage than M0, but this is not yet proof of robust learned dodging.
- Scripted traces have not been compared against Flash yet.
- AS bit-for-bit parity is a goal, but no parity test harness was found.
- MachineGun/Heli combat GUI feel still needs Charles manual checks.
- Exact Flash sprite visibility is not proven for defensive diagnostics.
- Model pickling errors during `EvalCallback` checkpoints are resolved via `TimedPPO`, but broad cross-platform serialization needs further verification.

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
- `enemy_fire_slow_2x`/`enemy_fire_slow_4x` are curriculum aids, not AS parity modes.
- Player bitmap registration, nested walk cadence, AS casing quirks, and edge `hitCheck` behavior remain uncertain; see `docs/parity_notes.md`.
- The generated constants file is large and should not be edited manually without a clear reason.
- Future sessions must check `git status` before editing and avoid reverting user work.

## Manual Control Update
- `scripts.play_human` supports `F12` screenshots saved as incrementing PNG files under `screenshots/` by default.
- Debug text is rendered in a right-side panel so it does not cover the game area.
- Pytest runtime is now ~36s full-suite locally; the slowest remaining tests are the subproc VecEnv smoke, curriculum training smoke, runtime CLI acceptance, and the parallel benchmark orchestration test.
- Some coverage was shortened by replacing expensive subprocess `--help` loops and full PPO smoke runs with narrower parser-level or direct VecEnv smoke checks.
- `scripts.watch_model` and `scripts.evaluate_model` now infer experiment config from a model path inside `experiments/.../models/` even when `--experiment` is omitted, preventing env/model observation-shape mismatches for direct experiment model paths.
- `scripts.watch_model` now renders through `env.unwrapped`, so wrapper-based control modes such as `movement_no_boost_scripted_attack_direct` can still show the GUI debug overlay.
- Human-friendly numeric CLI parsing now accepts underscore-separated integers and `k`/`M` suffixes for step/timestep style arguments such as `--total-timesteps`, `--eval-freq`, `--max-episode-steps`, `--steps`, and scripted trace frame counts.
- `scripts.train_parkour`, `scripts.run_experiment`, and `scripts.run_experiment_pair` support resume/fine-tune from SB3 model zip files. Resumed runs create new experiment directories, default to `reset_num_timesteps=False`, reject `--net-arch`, validate model/env spaces before training, and record parent lineage in configs/summaries.
- Resume/fine-tune runs with `--timing-profile on` now load through `TimedPPO`, so rollout/update timing remains instrumented after resume.
- `scripts.evaluate_matrix` runs cross-evaluation matrices across experiment/model entries and pressure profiles. It writes per-job logs/reports/metadata, matrix JSON/CSV/MD summaries, and a self-contained bundle under `experiments/eval_matrices/`. Replay saving is opt-in via `--save-replays`.
- New experiment and matrix outputs record reproducibility metadata: `argv.json`, `command.txt`, `invocation_metadata.json`, and `resolved_config.json`.
- `scripts.run_experiment` also records child command metadata such as `train_command.txt` and `eval_latest_command.txt`.
- `scripts.run_experiment --label` is an alias for `--experiment-name`; conflicting values fail clearly.
- `command.txt` is a best-effort reconstruction from argv; `argv.json` is the authoritative argument record.

## Handoff Behavior
- Future Codex sessions should ask clarification questions instead of making hypotheses when requirements are unclear.
- Future `docs/ai` updates should be succinct and limited to durable facts, validation, blockers, risks, and next actions.
