# Architecture Decisions

This is an append-only decision log. Future ChatGPT/Codex decisions should be added with date, decision, rationale, and consequences.

## 2026-05-03 - Bootstrap Handoff System Only
- Decision: Codex made no new simulator architecture decision during bootstrap.
- Rationale: The requested Phase 0 scope was documentation and repository handoff setup, not feature work.
- Consequences: Existing apparent architecture is documented in `PROJECT_CONTEXT.md` and `CURRENT_STATE.md`; future architecture changes should be explicitly logged here.

## Prior Context From Existing Summaries, Not Revalidated As Formal Codex Decisions
- `Summary_1.md` and `Summary_2.md` describe intended directions: bit-for-bit AS parity, Gymnasium interface, multi-discrete keyboard-like actions, vector/RAM observations, and future SB3 training.
- Some summary claims are not verified in current code, including W&B integration, threaded/asynchronous GIF recording, and complete training/checkpoint pipelines.
- Treat these summaries as useful planning context, not authoritative implementation state.

## 2026-05-03 - Deterministic Replay Foundation
- Decision: Use simple JSONL replays with one header plus one action/state-hash record per tick.
- Rationale: Human-inspectable and enough to verify headless-to-GUI determinism before adding combat.
- Consequences: Schema v1 does not yet support mid-replay reset events or full AS parity traces.

## 2026-05-04 - Extend Action Space For Basic Aiming/Firing
- Decision: Extend HA2 actions to `[move, jump, duck, boost, aim_bin, fire]` with 32 discrete aim bins, while accepting legacy 4-field actions internally.
- Rationale: Needed deterministic MachineGun replay/testing without adding a broad input system.
- Consequences: New replays use env version `0.3`; old replay hashes should be regenerated if needed.

## 2026-05-04 - Reset-Time Default Heli Target
- Decision: Spawn one deterministic default Heli on `reset()` for the first combat target slice.
- Rationale: The AS `heroStart`/parachute lifecycle is not modeled yet, but replayable MachineGun hit validation needs a stable enemy target now.
- Consequences: Heli spawn timing is an explicit approximation and should be revisited when AS startup/camera lifecycle is implemented.

## 2026-05-05 - AS-Backed First Heli Combat Loop
- Decision: Keep reset-time Heli spawn as debug/training mode while adding AS-backed Heli movement, gun aiming, enemy bullets, player damage, and state hashing.
- Rationale: This completes a deterministic playable/replayable combat slice without broad `heroStart`, pickups, drops, or gameover work.
- Consequences: Heli behavior is closer to AS but not exact until `heroStart` timing and decompiled casing/`timeSetp` quirks are verified.

## 2026-05-05 - Delayed Default Heli Spawn Proxy
- Decision: Queue the default Heli on reset and spawn it after first ground contact using AS-style `addEnemy` side/top coordinates; env version is now `0.5`.
- Rationale: AS spawns the first Heli after `heroStart`, not at reset. Reset-time spawn let early Heli targeting use the falling player's negative Y and caused the visible startup dart.
- Consequences: Initial state has no enemy plus `pending_default_heli=true`; existing 0.4 replay hashes should be regenerated. This is still a proxy, not the full AS parachute/start lifecycle.

## 2026-05-05 - Continuous Default Heli Respawn
- Decision: Enable deterministic default Heli respawn after Heli death by default (`respawn_helis=True`); env version is now `0.6`.
- Rationale: AS `heliFrame` calls `addEnemy(300)` after death, and early training needs continuous MachineGun-only targets.
- Consequences: Death removes the Heli, increments kill counters once, and spawns a replacement using AS-style positioning. Visual rewards/drops/explosions/sounds remain omitted.

## 2026-05-05 - Opt-In Combat Training Profile
- Decision: Keep legacy env behavior as the default and add `training_profile="combat_v1"` for SB3 training/evaluation/watch.
- Rationale: Existing replay/parity traces need stable legacy observations and rewards, while RL needs a bounded fixed-size vector observation, combat reward, and episode endings.
- Consequences: Models are profile-specific; `combat_v1` replays record profile metadata, and old replays remain legacy by default.

## 2026-05-13 - WandB Artifacts for Dual-Computer Sync
- Decision: Use WandB Artifacts as the primary mechanism for synchronizing experiment directories (including replays) across machines.
- Rationale: Provides a central "Source of Truth" tied to the training dashboard, ensures experiment folders remain identical across machines, and avoids the "scattered" feeling of generic cloud drives.
- Consequences: `train_parkour.py` now uploads full experiment folders to WandB; `sync_experiment.py` is required to download them on other machines. Local `.env` support added for per-folder WandB identity.

## 2026-05-14 - run_experiment.py as Canonical Entry Point
- Decision: Use `scripts.run_experiment` as the canonical local entry point for training and evaluation.
- Rationale: Ensures that every training run is immediately evaluated using a standard set of metrics and the resulting artifacts (models, logs, reports, replays) are packaged and uploaded together, reducing manual orchestration errors.
- Consequences: `train_parkour.py` and `evaluate_model.py` are now primarily called as sub-modules via `args_list` during standard workflows, though they can still be run standalone.

## 2026-05-05 - Experiment Directories as RL Artifact Boundary
- Decision: Make `experiments/<run>/` the default unit for training, evaluation, replay, report, checkpoint, and TensorBoard outputs.
- Rationale: Root-level `models/`, `reports/`, and `replays/` outputs were easy to overwrite or mix across runs; self-contained experiment folders make runs reproducible and easier to inspect.
- Consequences: `train_parkour` now creates a new experiment directory by default, `evaluate_model` and `watch_model` prefer experiment-scoped paths, and repeat evaluation on an existing report/replay file fails clearly rather than clobbering it. Root-level compatibility remains only for ad hoc/manual use.
