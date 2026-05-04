# Current State

Last updated: 2026-05-04 13:52 Europe/Paris

## What Appears to Work
- Python 3.11.9 is available locally; `.venv` has pytest and SB3 installed.
- Core Python files and new scripts compile.
- Headless env reset/step works and measured about 44,982 steps/sec in one local smoke run.
- `rgb_array` render smoke works with shape `(320, 450, 3)`.
- JSONL replay record/verify works for `replays/smoke.jsonl`.
- Playable GUI, replay GUI, screenshot hotkey, FFDEC tile/player rendering, and SB3 train/evaluate/watch entry points now exist.
- `play_human` startup was reduced by avoiding broad `pygame.init()`; local profile reached first render in about 0.78s.
- Scripted movement trace generation exists for idle, walk right, jump hold, double jump, duck/stand, and hyperjump.
- Charles manually exercised GUI play/replay checks after the scripted trace phase and reported they looked OK.

## What Is Unknown
- SB3 training/evaluation was not rerun after the FFDEC render change.
- Scripted traces are Python simulator traces only; they have not been compared against Flash yet.
- AS bit-for-bit parity is a goal, but no parity test harness was found.
- GIF recording still needs manual validation.

## Current Architecture
- `ha2_env.py` contains the main runtime architecture: environment state, player physics, collision checks against `const.FULL_MAP_DATA`, rendering, and state/hash debug hooks.
- `ha2_replay.py` provides deterministic JSONL replay writing/loading/verification.
- `scripts/` contains manual play, replay, screenshot, and minimal SB3 pipeline entry points.
- `tests/` contains pytest smoke tests.
- `ha2_constants.py` is generated static data for map and core movement constants.
- `extract_ha2_data.py` is the data extraction bridge from decompiled AS to generated Python constants.
- `heliattack2_scripts/` is the source-of-truth reference for original HA2 ActionScript behavior.
- `assets_ffdec/` provides current FFDEC-exported assets for rendering.

## Migration or Refactoring State
- The project appears to be in an early HA2 foundation phase.
- Minimal replay/test/training scaffolding was added; serious training is still deferred.
- No HA3 implementation was found during bootstrap inspection.

## Current Risks and Unclear Points
- Camera/parallax are a known approximation versus AS stateful `world._x/_y` threshold scrolling.
- Player bitmap registration, nested walk cadence, AS casing quirks, and edge `hitCheck` behavior remain uncertain; see `docs/parity_notes.md`.
- The generated constants file is large and should not be edited manually without a clear reason.
- Existing worktree has many modified/untracked files; future Codex sessions must avoid reverting user work.

## Manual Control Update
- `scripts.play_human` supports `F12` screenshots saved as incrementing PNG files under `screenshots/` by default.

## Handoff Behavior
- Future Codex sessions should ask clarification questions instead of making hypotheses when requirements are unclear.
- Future `docs/ai` updates should be succinct and limited to durable facts, validation, blockers, risks, and next actions.
