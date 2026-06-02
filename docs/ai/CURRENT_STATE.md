# Current State

Last updated: 2026-06-02 Europe/Paris

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
- Continuous Heli combat exists: default Heli spawns after AS intro completion or immediately in `skip_intro=True`, dead Helis are removed, kill counters update, and replacement Helis spawn with AS-style `addEnemy` coordinates.
- Heli combat includes AS-backed `heliFrame` movement/gun aiming/shoot cadence, nested Heli gun rendering, enemy bullets, player health damage, MachineGun-to-Heli damage, state hashing, and scripted traces.
- `heli_shoots_hero_240` now uses scripted fast-start (`skip_intro=True`) and deterministically shows enemy bullet damage under the current `ffdec_polygon` default: initial health 100, final health 50, first damaging enemy bullet id 5 at frame 91.
- `kill_heli_respawn_600` deterministically shows Heli death plus replacement spawn.
- Heli rendering composes visible FFDEC bitmaps `images/78.png` and `images/77.png`; the green `Heli.hit` child is not rendered by default.
- Player healthbar HUD renders with original FFDEC healthbar bitmaps and the AS bottom-anchored mask-scale rule.
- `scripts.play_human` accepts both `WASD` and `ZQSD` movement keys, and its mouse input helper falls back cleanly when no video system is active.
- `scripts/export_ffdec_reference.ps1` can export broad FFDEC reference data from a SWF and auto-detects `C:\Program Files (x86)\FFDec\ffdec-cli.exe`.
- `training_profile="combat_v1"` is available as an opt-in RL interface: 37-field bounded float32 vector observation, combat-aware reward, universal player-death termination, out-of-bounds safety termination, and max-step truncation.
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
- Replay headers now record simulator metadata (`simulator_id`, `simulator_version`, `simulation_semantics.collision_model`); replay verification/playback default to the recorded simulator semantics and can be overridden with `recorded/current/legacy`.
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
- Camera now has minimal AS-style stateful `world_x/world_y/worldpos` for Heli/projectiles; parallax remains simplified.
- MachineGun visual placement now uses Charles-provided FFDEC metadata; exact visual parity still needs manual Flash comparison.
- Projectile active-region removal uses Python `worldpos/stw/sth` plus tile collision.
- Default HA2 startup now has two modes: `skip_intro=False` runs an AS-backed `heroStart` parachute lifecycle and spawns the first Heli when the chute closes; `skip_intro=True` starts grounded near the left side and creates the first Heli immediately for training/scripts.
- Default projectile collision now uses `collision_model="ffdec_polygon"` in the evolving HA2 simulator.
- Explicit `collision_model="rect"` remains available for comparisons and legacy-style runs.
- Heli death respawn is implemented; non-training side effects remain omitted: pickups, drops, random weapon rewards, explosions, shards, blood, sounds, and bullet-time refill.
- Gameplay HUD now renders centrally from `ha2_env.py`: Time/Helis, Score, High Score, `Health:`, `HyperJump:`, `Reload:`, the starting MachineGun icon, and the existing healthbar.
- HUD rendering now uses the exact extracted font `assets_ffdec/fonts/19_standard 07_63.ttf` and original bar/icon assets for HyperJump and Reload instead of placeholder rectangles.
- HUD tests now assert that the original healthbar, HyperJump, reload, and MachineGun icon assets load, and that `play_human`, `watch_model`, and `play_replay` do not duplicate normal HUD drawing.
- High score persists in ignored local JSON at `state/ha2_high_scores.json`; rendering reads it, while human play, model watch, and evaluation update it.
- The healthbar is aligned at the original `431, 0` placement with the existing FFDEC healthbar bitmaps.
- The original extracted HUD font is copied to `assets_ffdec/fonts/19_standard 07_63.ttf` and used when available, with a small Pygame fallback.
- `combat_v1` is an RL interface layer only; it does not prove AS parity or tune PPO behavior.
- `combat_v1` defensive visibility diagnostics use bullet center plus an 8 px margin against the gameplay viewport; exact Flash sprite visibility is not proven.
- `enemy_fire_slow_2x`/`enemy_fire_slow_4x` are curriculum aids, not AS parity modes.
- Player bitmap registration, nested walk cadence, AS casing quirks, and edge `hitCheck` behavior remain uncertain; see `docs/parity_notes.md`.
- The generated constants file is large and should not be edited manually without a clear reason.
- Future sessions must check `git status` before editing and avoid reverting user work.
- Handoff bundles should include natural verification artifacts from the task, such as replay recordings, models, experiment outputs, and eval reports when those are produced by tests or smoke runs.

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
- `scripts.evaluate_model --damage-forensics on` writes separate JSON/Markdown damage-forensics reports with pre-impact windows and heuristic tags; `scripts.evaluate_matrix --damage-forensics` forwards this and bundles copied per-job reports.
- `ha2_env_legacy.py` is a frozen copy of the current rectangle-collision simulator for future A/B parity checks.
- `docs/ai/HA2_COLLISION_PARITY_AUDIT.md` and `docs/ai/FLASH_AS_FINDINGS.md` document AS/FFDEC collision evidence.
- `ha2_env.py` defaults to `collision_model="ffdec_polygon"` for projectile hits against FFDEC-derived Heli, standing-player, and duck-player hit shapes. Heli transforms are frame-aware, frame 2 is mirrored, parent rotation is applied, and player 1 px outline strokes are included. Explicit `collision_model="rect"` remains available.
- `ha2_env.py` defaults to `skip_intro=False`; runtime training/evaluation config defaults to `skip_intro=True`.
- Player health depletion is a universal evolving-simulator gameplay death rule: `health <= 0` terminates with `termination_reason="player_death"` for `legacy`, `combat_v1`, and `combat_bullets_v1`. `training_profile` no longer controls whether death exists; it only affects observations, rewards, and reward penalties.
- Normal HA2 gameplay should not have a sideways fall-death rule. The evolving env treats left/right world sides as collision bounds; any remaining out-of-bounds termination is `out_of_bounds_safety` or legacy replay compatibility unless later AS evidence proves otherwise.
- Evolving simulator `ENV_VERSION` is `1.0` after universal player death and out-of-bounds safety semantics.
- `ha2_env_legacy.py` is used as the replay-compatible legacy simulator for old pre-split `env_version <= 0.6` replays without explicit simulator metadata.
- `scripts.compare_collision_models` reports deterministic synthetic probe differences between rectangle and FFDEC polygon collision.
- `scripts/build_ffdec_parity_bundle.py` builds `reports/ffdec_parity_core_ha2/ffdec_parity_core_ha2.zip` plus `manifest.json` and `manifest.md` for HA2 FFDEC parity analysis.
- Damage forensics is diagnostic only: terrain blockage, world-right-edge distance, exact boost cooldown, and exact grounded-state-change fields are marked unavailable/null until a future simulator-diagnostics task.
- New experiment and matrix outputs record reproducibility metadata: `argv.json`, `command.txt`, `invocation_metadata.json`, and `resolved_config.json`.
- `scripts.run_experiment` also records child command metadata such as `train_command.txt` and `eval_latest_command.txt`.
- `scripts.run_experiment --label` is an alias for `--experiment-name`; conflicting values fail clearly.
- `command.txt` is a best-effort reconstruction from argv; `argv.json` is the authoritative argument record.

## Handoff Behavior
- Future Codex sessions should ask clarification questions instead of making hypotheses when requirements are unclear.
- Future `docs/ai` updates should be succinct and limited to durable facts, validation, blockers, risks, and next actions.
