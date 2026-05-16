# NEXT_CODEX_TASK.md

## Goal

Fix horizontal-movement diagnostics and clarify training-time eval frequency.

This is diagnostics/reporting only. Do not change simulator mechanics, rewards, observations, action spaces, PPO defaults, replay determinism, or curriculum control modes.

## Context

Replay inspection suggests the movement-curriculum agents may camp near the world edge rather than performing useful lateral dodging.

Source inspection found concrete diagnostic issues:

- `min_player_x` and `max_player_x` are initialized/exported but not updated during `step()`.
- `frames_moving_left/right` currently count requested movement inputs, not actual post-physics horizontal movement.
- `evaluate_model.py` tracks `max_x` locally, but not `min_x`, true x-range, actual dx, or edge-camping.
- `--eval-freq` is still confusing because SB3 counts VecEnv callback calls, not raw environment transitions.

## Non-goals

Do not add anti-wall-camping reward shaping yet.

Do not penalize jumping, ducking, boosting, or edge usage.

Do not rerun long 100k/500k experiments unless explicitly asked.

## Files to inspect first

- `ha2_env.py`
- `scripts/evaluate_model.py`
- `scripts/train_parkour.py`
- `scripts/run_experiment.py`
- `scripts/run_experiment_pair.py`
- `tests/test_rl_diagnostics.py`
- `tests/test_curriculum.py`

## Implementation plan

### 1. Fix `min_player_x` / `max_player_x`

In `ha2_env.step()`, after physics/collision resolution and before returning `info`, update:

- `min_player_x`
- `max_player_x`
- `player_x_range`

Use the actual final post-physics `self._x`.

### 2. Split requested movement from actual movement

Keep backward compatibility if useful, but make semantics explicit.

Preferred new metrics:

- `frames_pressing_left`
- `frames_pressing_right`
- `frames_pressing_neutral`

and separately:

- `frames_actual_moving_left`
- `frames_actual_moving_right`
- `frames_actual_not_moving_horizontally`
- `mean_abs_player_dx`
- `sum_abs_player_dx`

Compute actual movement from:

- `previous_x` saved at the start of `step()`;
- `dx = self._x - previous_x` after physics/collision.

Use a small epsilon to avoid floating noise.

### 3. Add wall/edge-camping diagnostics

Track:

- `frames_at_left_edge`
- `frames_at_right_edge`
- `fraction_at_left_edge`
- `fraction_at_right_edge`
- `max_consecutive_frames_at_left_edge`
- `max_consecutive_frames_at_right_edge`
- `frames_pressing_left_at_left_edge`
- `frames_pressing_right_at_right_edge`

Compute edge state from actual position with a documented tolerance.

Prefer using helpers based on the same boundary formulas implied by collision handling, not arbitrary magic values.

### 4. Add input-vs-motion mismatch diagnostics

Add derived metrics:

- `left_press_effective_motion_rate`
- `right_press_effective_motion_rate`
- `horizontal_action_without_motion_fraction`

This must catch the case where the policy holds left while blocked by the world edge.

### 5. Update evaluation reports

Update `scripts/evaluate_model.py` so `eval_latest.json`, `eval_best.json`, `episodes_detail`, and aggregate `metrics` include:

- `episode_min_x`
- `episode_max_x`
- `episode_x_range`
- `player_x_range`
- actual movement counters;
- edge-camping counters;
- input-vs-motion mismatch rates.

The report should make it obvious whether the agent is actually traversing the map or just pressing directions while stuck.

### 6. Clarify eval frequency semantics

Do not silently change existing `--eval-freq`.

Add:

- `--eval-freq-timesteps`

If provided, convert raw timesteps to SB3 VecEnv callback steps:

- `eval_freq_vec_steps = max(1, eval_freq_timesteps // n_envs)`

If both `--eval-freq` and `--eval-freq-timesteps` are passed, fail clearly.

Record in config/summary/timing:

- `eval_freq`
- `eval_freq_timesteps`
- `effective_eval_freq_vec_steps`
- `n_envs`
- estimated expected training eval count.

Pass this through `run_experiment.py` and `run_experiment_pair.py`.

### 7. Add replay-inspection convenience

In experiment and pair summaries, include concise copy-paste replay commands for produced latest eval replays, for example:

- `.venv\Scripts\python.exe -m scripts.play_replay <path>`

Keep this short.

### 8. Tests

Add or update tests that fail on the current bug:

- `min_player_x/max_player_x` update when the player moves.
- `episode_min_x/max_x/x_range` are correct in an eval smoke.
- requested movement counters and actual movement counters are distinct.
- holding left against the left edge increments edge/blocked diagnostics.
- `horizontal_action_without_motion_fraction` is nonzero when pressing into a wall.
- `--eval-freq-timesteps` converts correctly for `n_envs=1` and `n_envs=4`.
- passing both `--eval-freq` and `--eval-freq-timesteps` fails clearly.
- reports contain the new metrics.

Keep tests short.

## Validation

Run:

- `.venv\Scripts\python.exe -m py_compile ha2_env.py scripts/evaluate_model.py scripts/train_parkour.py scripts/run_experiment.py scripts/run_experiment_pair.py`
- `.venv\Scripts\python.exe -m pytest`

Run a small M0/M1 smoke:

- `.venv\Scripts\python.exe -m scripts.run_experiment_pair --mode parallel --profile-a combat_bullets_v1 --profile-b combat_bullets_v1 --control-mode-a movement_no_boost_scripted_attack_direct --control-mode-b movement_scripted_attack_direct --label-a M0_no_boost --label-b M1_boost --total-timesteps 10000 --n-envs 4 --vec-env dummy --wandb off --train-eval on --eval-freq-timesteps 5000 --train-eval-episodes 1 --eval-episodes 2 --save-replays --net-arch 128,128 --threads-per-job 6 --timing-profile on --seed 0 --seed-b 0`

Inspect and report:

- pair path;
- M0/M1 experiment paths;
- effective eval frequency;
- train eval count;
- min/max/range X;
- actual horizontal movement fractions;
- edge-camping fractions;
- max consecutive edge frames;
- input-vs-motion mismatch;
- replay commands.

Verify generated eval replays.

## Acceptance criteria

Complete only if:

- `min_player_x/max_player_x/player_x_range` are trustworthy.
- Reports distinguish requested movement from actual movement.
- Edge-camping is explicitly measured.
- Pressing into a wall is measurable.
- `--eval-freq-timesteps` works and is recorded.
- Summaries include replay commands.
- All tests pass.
- Existing full-action and curriculum training still work.
- No mechanics/reward/observation/action-space changes are made.

## Stop conditions

Stop and report if:

- true edge detection is ambiguous without changing collision mechanics;
- new diagnostics would change replay hashes/state;
- `--eval-freq-timesteps` conflicts with SB3 behavior in a non-obvious way;
- tests become slow or flaky;
- fixing this would require reward shaping.

## Required log update

Update:

- `docs/ai/CURRENT_STATE.md`
- `docs/ai/VALIDATION.md`
- `docs/ai/CODEX_SESSION_LOG.md`

Log:

- files changed;
- commands run;
- pass/fail result;
- smoke paths;
- new diagnostic values;
- eval-frequency behavior;
- replay commands;
- remaining risks;
- suggested next step.