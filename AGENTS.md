# HeliAttack Agent Instructions

## Project Type
- Python project focused on a Heli Attack 2/3 simulator and future RL training.
- Current verified code is a small Gymnasium/Pygame HA2 environment, extracted HA2 ActionScript, generated constants, and HA2 assets.

## Primary Goals
- Build a fast HA2 and HA3 simulator.
- Reproduce original ActionScript (AS) physics and logic exactly; parity with original Flash behavior is more important than modernizing the mechanics.
- Build a graphical player to:
  - play the simulator directly,
  - watch live AI gameplay,
  - replay AI behavior from specific evaluations.
- Train an AI agent using Stable Baselines3 or a closely related SB3-based stack.

## Scope Order
1. Start with HA2 single-world simulation.
2. Expand to HA3 after HA2 is stable and validated.

## Repository Layout
- Root workspace: `C:\Users\cthin\AI\HeliAttack`
- `ha2_env.py`: current Gymnasium `HeliAttack2Env`, Pygame renderer, and deterministic state/debug hooks.
- `ha2_replay.py`: JSONL replay writer/loader/verifier for deterministic headless-to-GUI replay.
- `scripts/`: playable mode, replay tools, and minimal train/evaluate/watch entry points.
- `tests/`: pytest smoke tests for env behavior and replay roundtrip.
- `ha2_constants.py`: generated HA2 constants and map data.
- `extract_ha2_data.py`: extracts `map1` from decompiled AS into `ha2_constants.py`.
- `heliattack2_scripts/`: extracted/decompiled HA2 ActionScript source.
- `assets_ffdec/`: current FFDEC-exported HA2 image/sprite assets used by the renderer.
- `docs/ai/`: shared handoff docs between ChatGPT planning and Codex implementation.

## Coding Conventions
- Preserve direct AS-to-Python logic where parity matters, even if the resulting Python is not idiomatic.
- Keep Python edits simple, explicit, and readable; current code uses standard classes, module-level constants, direct control flow, and minimal abstraction.
- Avoid broad refactors unless the active task explicitly calls for them.
- Avoid changing generated data by hand unless the task is specifically about generated constants; prefer updating `extract_ha2_data.py` and regenerating.
- Prefer cross-platform paths for new code, but do not silently rewrite existing Windows-specific paths unless the task is about portability.

## Dependency Policy
- Do not install dependencies unless explicitly instructed.
- Do not add new runtime dependencies without documenting the reason and updating validation/setup docs.
- Dependencies are listed in `requirements.txt`.
- W&B is optional and must stay off by default.

## Testing and Validation
- Before claiming success, run the relevant commands from `docs/ai/VALIDATION.md` when possible.
- At minimum for simulator code, run Python compilation and a headless environment smoke test unless impossible.
- GUI/manual checks must be reported as manual checks; do not imply they were completed if no window was opened or no gameplay was exercised.
- If validation cannot run because dependencies, display access, or environment setup are missing, report the exact reason.

## AI Handoff Protocol
- Before every non-trivial implementation task, read:
  - `AGENTS.md`
  - `docs/ai/PROJECT_CONTEXT.md`
  - `docs/ai/CURRENT_STATE.md`
  - `docs/ai/ARCHITECTURE_DECISIONS.md`
  - `docs/ai/NEXT_CODEX_TASK.md`
  - `docs/ai/VALIDATION.md`
- Implement only the concrete task described in `docs/ai/NEXT_CODEX_TASK.md`.
- If that task is absent, unsafe, impossible, or based on a false architectural assumption, stop before broad changes and report the discrepancy.
- Ask clarification questions instead of making hypotheses when requirements, architecture, file ownership, validation expectations, or user intent are unclear.
- Do not fill gaps with speculative assumptions unless the user explicitly asks Codex to choose; if blocked by ambiguity, ask first.
- After every non-trivial coding session, update:
  - `docs/ai/CURRENT_STATE.md`
  - `docs/ai/CODEX_SESSION_LOG.md`
- Report architectural discrepancies, workarounds, failed approaches, and remaining risks explicitly.
- Keep `docs/ai` edits concise. Session logs and state updates should record only durable facts, validation results, blockers, and next actions; avoid exhaustive command transcripts unless specifically requested.
- After completing any task from `docs/ai/NEXT_CODEX_TASK.md`, create a handoff bundle zip directly under `docs/ai/`, named like `codex_task_bundle_YYYYMMDD_HHMMSS_short-task-keywords.zip`.
- Use 2 task-identifying keywords in the bundle filename when possible; use up to 4 only if needed for clarity.
- That bundle must include:
  - copies of every source/test/doc file materially impacted by the task, in its final state;
  - copies of every impacted `docs/ai` file, in its final state;
  - the complete current `git diff` output as a text file;
  - a concise final Codex report text file matching the final console response for the task.
- The bundled final report should omit working-tree or Git-management commentary unless it is directly relevant to implementation, validation, a blocker, or a risk.
- If an impacted file is very large, binary, generated, ignored, or ambiguous to include, ask for clarification instead of guessing.

## User Profile and Communication Preferences
- User is proficient in Python.
- User is relatively new to AI/RL and wants to learn in detail.
- Communication style should be direct, factual, helpful, succinct when possible, and exact when needed.
- Prefer asking precise clarification questions over guessing.

## Platform Context
- Current machine: Windows 11 laptop.
- Future target machine: Ubuntu 22 ThinkStation P3 Ultra via SSH, possibly with NoMachine.
- Prefer cross-platform choices where practical, but keep Windows-first execution steps when working locally.

## Source Control Rules
- **ALWAYS ask for explicit user confirmation before performing a `git commit` or `git push`.** Do not auto-commit changes without presenting the proposed commit message and verifying the user is ready.
