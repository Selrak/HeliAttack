# Project Context

## Overview
This repository appears to be an early Python port/simulator for Heli Attack 2, intended to become a high-fidelity Gymnasium environment for reinforcement learning and later a broader HA2/HA3 simulator/player stack. The main current focus is reproducing HA2 ActionScript physics and map behavior closely enough for AI training and debugging.

## Main Technologies
- Python 3.11 verified locally.
- Gymnasium environment API in `ha2_env.py`.
- NumPy for observations and frame arrays.
- Pygame for human rendering and input.
- `imageio` is used only for optional GIF writing.
- Stable Baselines3 entry points and `requirements.txt` exist; training is still minimal/scaffold-level.

## Main Files and Directories
- `ha2_env.py`: `HeliAttack2Env`, physics step logic, renderer, debug state/hash hooks.
- `ha2_replay.py`: JSONL replay writer/loader/verifier.
- `scripts/`: playable GUI, replay record/verify/play, and minimal SB3 train/evaluate/watch scripts.
- `scripts/record_scripted_trace.py`: deterministic player movement traces for manual parity inspection.
- `tests/`: pytest smoke tests for env and replay.
- `ha2_constants.py`: generated constants and `FULL_MAP_DATA`; contains `PLAYER_SPAWN_INDEX`, tile size, screen size, and player movement constants.
- `extract_ha2_data.py`: reads decompiled AS from `heliattack2_scripts/ha2_core_logic/frame_19_DoAction_2.as` and regenerates `ha2_constants.py`.
- `heliattack2_scripts/`: decompiled/extracted HA2 ActionScript source used as parity reference.
- `assets_ffdec/`: FFDEC-exported HA2 image/sprite assets used by the Pygame renderer.
- `Summary_1.md`, `Summary_2.md`, `OLD_chatGPT_project_instructions.txt`: prior planning/context documents. They are useful but include claims not fully verified in current code.
- `docs/ai/`: AI handoff system for repeated ChatGPT planning and Codex implementation sessions.

## Run Commands
- Headless import/smoke use: instantiate `HeliAttack2Env(render_mode=None)` from Python.
- Human play/debug loop: `python -m scripts.play_human`
- Record deterministic random replay: `python -m scripts.record_random_replay --steps 300 --out replays/smoke.jsonl`
- Verify replay: `python -m scripts.verify_replay replays/smoke.jsonl`
- Watch replay: `python -m scripts.play_replay replays/smoke.jsonl`
- Record scripted parity traces: `python -m scripts.record_scripted_trace --scenario all`
- Regenerate constants from AS map data: `python extract_ha2_data.py`

## Test Commands
- Pytest tests now exist under `tests/`.
- Current canonical validation is documented in `docs/ai/VALIDATION.md`.

## Constraints and Uncertainties
- SB3 training/evaluation/watch scripts exist, but remain smoke-level and not tuned.
- The current simulator models player movement/collision and rendering with `assets_ffdec`; combat, helicopter AI, and projectile systems are not implemented.
- Minimal training/evaluation/watch scripts exist but have not been end-to-end validated in recent parity work.
- Exact AS parity has not been proven by automated tests; current validation is limited to compilation and smoke execution.
- Camera/parallax are currently approximate relative to AS threshold scrolling.
