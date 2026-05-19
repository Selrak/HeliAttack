# NEXT_CODEX_TASK.md

## Goal

Freeze the current HA2 simulator as a legacy reference, then perform a bounded collision parity audit comparing the current Python simulator with the original ActionScript / Flash collision model.

The central question is:

Do the current Python rectangle-based collision checks differ from Flash `hitTest(..., ..., true)` in a way that can affect gameplay, training, or evaluation results?

This task must not yet change gameplay behavior in the main simulator. It must preserve the current simulator as a frozen legacy baseline and produce a precise audit that can justify a later simulator change.

## Non-goals

Do not implement the parachute intro.

Do not change player movement physics.

Do not change gun firing cadence, bullet speed, bullet damage, reward logic, observations, or training code.

Do not immediately replace the current Python hit rectangles with a new collision model.

Do not run long training jobs.

Do not run A/B training comparisons in this task.

Do not rewrite `docs/parity_notes.md`. Only add a small dated factual section if the audit confirms new facts.

Do not invent Flash shape behavior if the FFDEC resources are missing or inconclusive.

## Context

The project goal is exact or near-exact reproduction of Heli Attack 2 physics and gameplay logic from the original ActionScript.

The current `ha2_env.py` uses explicit Python collision approximations:

- player/map collision through `_hit_check` and tile probes;
- player bullet / enemy collision through `_enemy_hit_rect` and `_bullet_hit_enemy`;
- enemy bullet / player collision through `_player_hit_rect` and `_enemy_bullet_hit_player`;
- collision debug drawing through `_draw_collision_debug`.

The existing parity notes already identify unresolved collision questions:

- ActionScript `hitCheck` appears to index the map directly, while Python bounds-checks indexes;
- Python uses a deterministic rectangle for the Heli hit area derived from FFDEC placement data;
- Flash `hitTest(..., ..., true)` may test against the actual shape of the target clip rather than a simple axis-aligned rectangle;
- Heli rotation may affect the real Flash hit area, while the current Python Heli hit rectangle is axis-aligned.

The first step is therefore not to change gameplay blindly, but to audit the evidence and create a stable legacy simulator for later A/B comparisons.

## Files to inspect first

Inspect these files first:

- `ha2_env.py`
- `ha2_constants.py`
- `ha2_replay.py`
- `docs/parity_notes.md`
- `docs/ai/CURRENT_STATE.md`
- `docs/ai/ARCHITECTURE_DECISIONS.md`
- `docs/ai/CODEX_SESSION_LOG.md`

Then inspect the original ActionScript files under `heliattack2_scripts`, especially files containing:

- `hitCheck`
- `hitTest`
- `player.gfx.hit`
- `enemyArray`
- `bulletFrame`
- `enemyBulletFrame`
- `heliFrame`
- `heroAction`

Also inspect available FFDEC exports related to:

- the player sprite;
- player `gfx`;
- player nested `hit` clip;
- `DefineSprite_111_Heli`;
- Heli nested `hit` clip;
- bullet and enemy bullet sprites if relevant.

If the exact paths differ, search the repository and document the actual paths found.

## Files likely to modify

Verify from the repository, but likely modifications are:

- create `ha2_env_legacy.py`
- create `docs/ai/HA2_COLLISION_PARITY_AUDIT.md`
- optionally add a small test file such as `tests/test_legacy_env.py`
- update `docs/parity_notes.md` only with a small dated factual addendum if new facts are confirmed
- update `docs/ai/CURRENT_STATE.md`
- update `docs/ai/CODEX_SESSION_LOG.md`

Do not modify `ha2_env.py` unless absolutely necessary for an import or packaging issue. Any modification to `ha2_env.py` must be explicitly justified in the session log.

## Implementation plan

1. Create `ha2_env_legacy.py` as a frozen copy of the current `ha2_env.py`.

   This must be a real code copy, not an import wrapper around `ha2_env.py`, because `ha2_env.py` is expected to diverge in later parity work.

   Add only a short header comment explaining that this file is a frozen legacy baseline. Do not change simulator logic.

2. Verify that `ha2_env_legacy.py` imports independently.

   At minimum, this must work:

   `from ha2_env_legacy import HeliAttack2Env`

   Creating and resetting the environment must also work.

3. Add a minimal automated legacy smoke test.

   The test should verify at least:

   - `ha2_env_legacy.HeliAttack2Env` imports;
   - `reset(seed=0)` works;
   - a short deterministic fixed-action rollout works;
   - `get_state()` exists;
   - `state_hash()` exists;
   - the legacy environment does not import the main `HeliAttack2Env` class from `ha2_env.py`.

   Do not add a permanent test requiring `ha2_env.py` and `ha2_env_legacy.py` to stay identical. They are expected to diverge later.

4. Audit ActionScript map collision.

   Find and document the original `hitCheck` implementation and every relevant call site in player movement.

   For each relevant call site, record:

   - ActionScript file path;
   - function or block name;
   - exact expression used;
   - tile coordinates used;
   - whether the ActionScript manually guards map bounds before calling `hitCheck`;
   - whether Python currently matches the behavior or adds safety behavior.

5. Audit ActionScript bullet collision.

   Find and document the original player bullet collision logic.

   Pay special attention to expressions like:

   `enemyArray[i].hit.hitTest(this._x + world._x, this._y + world._y, true)`

   or equivalent decompiled forms.

   Record whether the ActionScript appears to use:

   - point-vs-shape collision;
   - point-vs-bounding-box collision;
   - a nested `hit` clip;
   - world-offset coordinates;
   - enemy rotation or inherited transforms.

6. Audit ActionScript enemy bullet collision.

   Find and document the original enemy bullet collision logic.

   Pay special attention to expressions like:

   `player.gfx.hit.hitTest(this._x + world._x, this._y + world._y, true)`

   or equivalent decompiled forms.

   Record whether the ActionScript appears to use the player's visible sprite, a nested `hit` clip, or a separate logical hit shape.

7. Audit the current Python collision model.

   In `ha2_env.py`, document the current behavior of:

   - `_hit_check`
   - `_player_hit_rect`
   - `_enemy_hit_rect`
   - `_bullet_hit_enemy`
   - `_enemy_bullet_hit_player`
   - `_projectile_should_remove`
   - `_map_tile_empty_at`
   - `_draw_collision_debug`

   For each function, classify it as one of:

   - likely ActionScript-equivalent;
   - deliberate robustness difference;
   - gameplay approximation;
   - visual/debug-only helper;
   - unresolved.

8. Inspect FFDEC resources for nested `hit` clips.

   Determine whether the repository contains enough data to reconstruct:

   - the player's actual Flash hit shape;
   - the Heli's actual Flash hit shape;
   - the placement and transformation of those shapes;
   - whether Heli rotation should rotate the hit area.

   If the needed FFDEC information is missing, state exactly what is missing and what Charles should extract from FFDEC.

9. Create `docs/ai/HA2_COLLISION_PARITY_AUDIT.md`.

   The report must include these sections:

   - `Summary`
   - `ActionScript evidence`
   - `Current Python model`
   - `Confirmed matches`
   - `Likely gameplay divergences`
   - `Unresolved questions`
   - `Recommended next simulator changes`
   - `FFDEC resources needed, if any`

   The `Likely gameplay divergences` section must explicitly state whether the current Python collision model could affect:

   - player survival;
   - Heli kill timing;
   - bullet hit/miss behavior;
   - training rewards;
   - evaluation comparability.

   The `Recommended next simulator changes` section must separate:

   - safe changes;
   - likely changes requiring validation;
   - changes that must wait for missing Flash/FFDEC evidence.

10. Update `docs/parity_notes.md` only if the audit confirms new facts.

   Add a small dated section such as:

   `## AS Audit - 2026-05-19 Collision / HitTest Investigation`

   Include only concise factual conclusions. Do not reorganize the whole file.

11. Update project handoff documents.

   Update:

   - `docs/ai/CURRENT_STATE.md`
   - `docs/ai/CODEX_SESSION_LOG.md`

## Validation

Run at least:

- `python -m py_compile ha2_env.py ha2_env_legacy.py ha2_replay.py`
- `python -m pytest`

If a dedicated legacy smoke test is added, also run it explicitly, for example:

- `python -m pytest tests/test_legacy_env.py`

If existing replay or scripted trace tests are relevant and already part of the test suite, let the full test suite cover them.

Do not run long training.

Do not run A/B training comparisons.

## Manual checks

No long manual graphical check is required for this task.

If practical, verify that the human player script still exposes help successfully:

- `python -m scripts.play_human --help`

Do not spend time tuning visuals in this task.

## Acceptance criteria

This task is complete if:

- `ha2_env_legacy.py` exists as a frozen, functional copy of the current simulator;
- the legacy simulator can be imported, reset, stepped, and hashed independently;
- existing tests pass;
- a collision parity audit exists at `docs/ai/HA2_COLLISION_PARITY_AUDIT.md`;
- the audit clearly distinguishes map collision, player bullet collision, enemy bullet collision, and debug collision drawing;
- the audit explicitly says whether the current Python rectangles may cause gameplay divergence;
- `docs/parity_notes.md` is updated only with confirmed facts, or left unchanged if no new fact is confirmed;
- `docs/ai/CURRENT_STATE.md` and `docs/ai/CODEX_SESSION_LOG.md` are updated.

## Stop conditions

Stop and report instead of improvising if:

- the relevant ActionScript collision functions cannot be found;
- the FFDEC resources do not expose the nested `hit` clips clearly enough;
- making `ha2_env_legacy.py` work requires non-trivial simulator changes;
- a gameplay collision change seems necessary but cannot be justified from ActionScript or FFDEC evidence;
- tests fail for reasons that are not clearly caused by this task.

## Required Codex session log

Update:

- `docs/ai/CURRENT_STATE.md`
- `docs/ai/CODEX_SESSION_LOG.md`

The session log must include:

- files inspected;
- files changed;
- commands run;
- pass/fail result for each command;
- relevant ActionScript evidence found;
- relevant FFDEC evidence found or missing;
- confirmed differences between ActionScript/Flash and Python;
- any workaround used;
- remaining risks;
- recommended next task.