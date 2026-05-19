# NEXT_CODEX_TASK.md

## Goal

Add replay metadata so HA2 replay files record which simulator semantics produced them, and make replay verification/playback use those recorded semantics by default.

This is needed because `ha2_env.py` and `ha2_env_legacy.py` can now diverge, and `collision_model="rect"` vs `collision_model="ffdec_polygon"` can change replay hashes and visible hit/damage behavior.

## Non-goals

Do not change gameplay, collisions, rewards, observations, action spaces, training, animation, HUD, fullscreen, or debug-panel behavior.

Do not make `ffdec_polygon` the default.

Do not modify `ha2_env_legacy.py` gameplay logic.

## Files to inspect

- `ha2_replay.py`
- `ha2_env.py`
- `ha2_env_legacy.py`
- `scripts/play_replay.py`
- any replay verification script
- scripts that create `JsonlReplayWriter`, especially `scripts/play_human.py` and `scripts/watch_model.py`
- existing replay tests

## Implementation plan

1. Run `git status --short` and record any pre-existing changes in the session log.

2. Extend new replay headers with:

   - `simulator_id`
   - `simulator_version`
   - `simulation_semantics`

   `simulation_semantics` must include at least `collision_model`.

   Example header fields:

       {
         "simulator_id": "ha2_env",
         "simulator_version": "0.7",
         "simulation_semantics": {
           "collision_model": "rect"
         }
       }

3. Preserve compatibility with old replay files.

   For old headers without `simulator_id`, infer:

   - `simulator_id = "ha2_env_legacy"`
   - `collision_model = "rect"`

   when the old `env_version` clearly corresponds to the pre-split simulator.

   If the mapping is unclear, fail with a clear error.

4. Add a small explicit simulator resolver for replay use.

   It should support:

   - `recorded`: use the simulator and semantics from the replay header;
   - `current`: force `ha2_env`;
   - `legacy`: force `ha2_env_legacy`.

5. Update `verify_replay_file()`.

   By default, strict verification must use the recorded simulator semantics.

   Add an override parameter for intentional cross-simulator comparison.

6. Update `scripts/play_replay.py`.

   Default: replay with recorded simulator semantics.

   Add an option such as:

   - `--replay-env recorded`
   - `--replay-env current`
   - `--replay-env legacy`

   If the chosen simulator differs from the recorded one, print a clear warning that replay hashes and visual hit/damage behavior may diverge.

7. Ensure replay-producing scripts get the new metadata automatically through `JsonlReplayWriter`.

8. Add focused tests for:

   - new headers contain `simulator_id`, `simulator_version`, and `simulation_semantics.collision_model`;
   - old headers are inferred as legacy/rect when possible;
   - strict verification uses recorded semantics by default;
   - explicit override to current/legacy is possible;
   - invalid simulator or collision metadata fails clearly.

9. Update:

   - `docs/ai/CURRENT_STATE.md`
   - `docs/ai/CODEX_SESSION_LOG.md`
   - `docs/ai/VALIDATION.md` if commands changed

## Validation

Run:

- `python -m py_compile ha2_env.py ha2_env_legacy.py ha2_replay.py scripts/play_replay.py`
- `python -m pytest tests/test_replay_metadata.py`
- `python -m pytest`
- `python -m scripts.play_replay --help`

Do not run training.

## Acceptance criteria

- New replay files contain simulator provenance and collision semantics.
- Old replay files remain loadable with clear legacy/rect inference.
- Strict verification uses recorded semantics by default.
- Graphical replay uses recorded semantics by default.
- Cross-simulator replay is possible only through an explicit option and prints a warning.
- Tests pass.
- Project state/log docs are updated.

## Stop conditions

Stop and report if:

- old replay compatibility cannot be preserved cleanly;
- `ha2_env_legacy.py` cannot be imported;
- simulator identity cannot be determined from wrapped environments;
- this requires gameplay or replay hash changes beyond metadata;
- unrelated uncommitted changes make the task unsafe to isolate.

## Required Codex session log

Update `docs/ai/CURRENT_STATE.md` and `docs/ai/CODEX_SESSION_LOG.md` with:

- files changed;
- commands run;
- pass/fail results;
- new replay metadata fields;
- old replay compatibility rule;
- tests added;
- remaining risks;
- recommended next step.