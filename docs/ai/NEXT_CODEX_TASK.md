# NEXT_CODEX_TASK.md

## Goal

Finish the HA2 RL instrumentation bugfix pass by fixing the remaining concrete issues found in the current source and smoke artifacts.

This is a small bugfix/validation task. Do not run a new long experiment.

## Non-goals

Do not change simulator mechanics, rewards, observations, action space, PPO hyperparameters, training profiles, or replay semantics.

Do not add curriculum logic.

Do not rerun 500k experiments.

## Context

Current source/artifact inspection found:

1. Movement diagnostic counters are initialized and exported, but most are not incremented in `ha2_env.step()`.
   - `boost_activations` increments.
   - `frames_grounded`, `frames_airborne`, `frames_jump_pressed`, `frames_boost_pressed`, `frames_moving_left/right`, etc. remain zero in smoke reports.
   - This contradicts `marginal_action_distributions`, which show non-zero jump/boost/duck/move usage.

2. `test_rl_diagnostics.py` only checks that movement diagnostic keys exist; it does not verify that counters increase or are coherent.

3. The successful pair smoke still produced `pair_summary.json` with `timing_report_path: null`.
   - Current source may now contain a partial fix, but it was not validated after the last edit.

4. Parallel job duration reporting is wrong with stagger:
   - job B duration is measured from job A start (`start_tick_total`) instead of job B start.

5. `config.json` records `net_arch`, but `trainable_parameters` and `activation_fn` are still missing/None in the generated ZIPs.
   - Likely cause: `train_parkour.py` rewrites `config.json` without `allow_overwrite=True`, inside a silent `except`.

6. Timing PPO itself appears mostly fixed:
   - `TimedPPO` separates rollout and train update time.
   - `other_overhead` no longer subtracts overlapping train-time eval.
   - Keep this design unless a test proves it broken.

## Files to inspect first

- `ha2_env.py`
- `scripts/train_parkour.py`
- `scripts/run_experiment.py`
- `scripts/run_experiment_pair.py`
- `scripts/runtime_timing.py`
- `scripts/evaluate_model.py`
- `tests/test_benchmark_orchestration.py`
- `tests/test_rl_diagnostics.py`
- `docs/ai/CURRENT_STATE.md`
- `docs/ai/VALIDATION.md`
- `docs/ai/CODEX_SESSION_LOG.md`

## Implementation plan

### 1. Fix movement diagnostics in `ha2_env.step()`

Add actual per-step increments.

Use action-based counters:

- `frames_jump_pressed`
- `frames_boost_pressed`
- `frames_moving_left`
- `frames_moving_right`
- `frames_not_moving_horizontally`

Use actual post-physics state for:

- `frames_grounded`
- `frames_airborne`
- `min_player_x`
- `max_player_x`

Handle boost carefully:

- compute boost readiness before consuming hyperjump charge;
- increment `frames_boost_ready` from pre-action readiness;
- increment `frames_boost_pressed_ready` / `frames_boost_pressed_not_ready` from pre-action readiness;
- increment `boost_activations` only when hyperjump actually triggers.

Do not alter movement mechanics.

### 2. Fix config metadata overwrite

In `train_parkour.py`, when adding:

- `trainable_parameters`
- `activation_fn`

rewrite `config.json` with `allow_overwrite=True`.

Do not silently swallow failures. Replace `except Exception: pass` with at least a warning.

Tests must assert that `trainable_parameters` is a positive integer for a smoke run.

### 3. Fix parallel job duration reporting

In `run_experiment_pair.py`:

- record `start_tick_a`;
- record `start_tick_b`;
- compute job A duration as `end_tick_a - start_tick_a`;
- compute job B duration as `end_tick_b - start_tick_b`;
- keep `total_parallel_duration` measured from first job start to last job end.

Add a simple test or helper-level assertion so this cannot regress.

### 4. Validate/fix pair timing report paths

Ensure both sequential and parallel modes discover timing reports from `experiment_path`.

When timing reports exist, `pair_summary.json` must not leave timing fields null.

At minimum record:

- `timing_report_path`
- or better:
  - `train_timing_json`
  - `train_timing_md`
  - `orchestration_timing_json`
  - `orchestration_timing_md`

Then rerun the pair smoke after this fix.

### 5. Tighten bundle validation

The diagnostic bundle should include all existing relevant artifacts:

- `config.json`
- `git_info.txt`
- `summary.md`
- `eval_best.json` when produced
- `eval_latest.json`
- `best_eval_ep0.jsonl` when produced
- `latest_eval_ep0.jsonl`
- `train_timing.json`
- `train_timing.md`
- `orchestration_timing.json`
- `orchestration_timing.md`

Existence checks are fine because small runs with `--train-eval off` may not produce `best.zip`, `eval_best.json`, or `best_eval_ep0.jsonl`.

### 6. Strengthen tests

Update tests so they fail on the current bugs.

Required tests:

- direct env smoke:
  - reset `HeliAttack2Env(training_profile="combat_v1")`;
  - run forced actions with move/jump/duck/boost;
  - verify movement counters are not all zero;
  - verify `frames_grounded + frames_airborne` is close to number of steps;
  - verify movement left/right counters reflect forced move actions.

- evaluation/report smoke:
  - run a tiny `run_experiment`;
  - verify movement metrics in `eval_latest.json` are numeric and plausible;
  - verify they are not all zero when action marginals show non-zero actions.

- bundle smoke:
  - verify ZIP includes timing files and latest eval/replay;
  - best eval/replay optional unless produced.

- pair smoke:
  - verify pair summary has non-null timing report fields after a parallel run;
  - verify job A/B durations are individually measured from their own starts;
  - verify seed A and seed B remain explicit.

- config metadata:
  - verify `net_arch == "128,128"` or `"32,32"` in smoke config;
  - verify `trainable_parameters` is present and > 0;
  - verify `activation_fn` is present when SB3 exposes it.

Remove or replace placeholder tests that only contain `pass`.

## Validation

Run with the venv Python explicitly on Windows:

- `.venv\Scripts\python.exe -m py_compile ha2_env.py scripts/runtime_timing.py scripts/train_parkour.py scripts/run_experiment.py scripts/run_experiment_pair.py scripts/evaluate_model.py`
- `.venv\Scripts\python.exe -m pytest`

Run a fresh single-job smoke:

- `.venv\Scripts\python.exe -m scripts.run_experiment --training-profile combat_bullets_v1 --total-timesteps 1000 --n-envs 1 --vec-env dummy --wandb off --train-eval off --eval-episodes 1 --save-replays --timing-profile on --torch-num-threads 2 --net-arch 128,128`

Run a fresh pair smoke after all fixes:

- `.venv\Scripts\python.exe -m scripts.run_experiment_pair --mode parallel --profile-a combat_v1 --profile-b combat_bullets_v1 --total-timesteps 1000 --n-envs 1 --vec-env dummy --wandb off --train-eval off --eval-episodes 1 --save-replays --timing-profile on --threads-per-job 2 --net-arch 128,128 --stagger-seconds 0 --seed 0 --seed-b 0`

Then inspect and report:

- pair smoke path;
- experiment paths;
- pair timing paths;
- ZIP contents for both jobs;
- movement metric values from both `eval_latest.json`;
- action marginal distributions from both `eval_latest.json`;
- training timing split from both `train_timing.json`;
- `config.json` policy metadata;
- git status.

Run replay validation only if replay-affecting state or mechanics changed unexpectedly:

- `.venv\Scripts\python.exe -m scripts.record_random_replay --steps 300 --out replays/smoke.jsonl`
- `.venv\Scripts\python.exe -m scripts.verify_replay replays/smoke.jsonl`
- `.venv\Scripts\python.exe -m scripts.record_scripted_trace --scenario all`
- `.venv\Scripts\python.exe -m scripts.verify_replay reports/parity_traces/walk_right_120.jsonl`
- `.venv\Scripts\python.exe -m scripts.verify_replay reports/parity_traces/fire_right_60.jsonl`
- `.venv\Scripts\python.exe -m scripts.verify_replay reports/parity_traces/fire_at_heli_180.jsonl`
- `.venv\Scripts\python.exe -m scripts.verify_replay reports/parity_traces/heli_shoots_hero_240.jsonl`
- `.venv\Scripts\python.exe -m scripts.verify_replay reports/parity_traces/kill_heli_respawn_600.jsonl`

## Acceptance criteria

Complete only if:

- movement counters increment correctly in direct env stepping;
- fresh eval reports no longer show impossible all-zero movement diagnostics;
- action marginals and movement diagnostics are not contradictory;
- pair summary timing paths are non-null after a fresh post-fix pair smoke;
- parallel job durations are measured from each job’s own start time;
- diagnostic ZIPs include timing files and latest eval/replay;
- config records `net_arch`, `trainable_parameters`, and `activation_fn` when available;
- timing reports still have `train_update_count == rollout_count`;
- `other_or_unclassified_training_seconds >= 0`;
- all tests pass;
- no simulator mechanics/reward/observation/action-space/replay behavior is intentionally changed.

## Stop conditions

Stop and report if:

- making movement diagnostics reliable would require changing movement mechanics;
- timing report paths cannot be discovered robustly from experiment paths;
- config metadata cannot be recorded without broader refactor;
- model saving fails again with `TimedPPO`;
- replay hashes change unexpectedly;
- tests become long or flaky.

## Required Codex session log

Update:

- `docs/ai/CURRENT_STATE.md`
- `docs/ai/VALIDATION.md`
- `docs/ai/CODEX_SESSION_LOG.md`

Log:

- files changed;
- commands run;
- pass/fail result;
- direct movement diagnostic test result;
- single-job smoke path;
- pair smoke path;
- pair timing paths;
- ZIP contents confirmation;
- movement metric values;
- config metadata values;
- timing split values;
- remaining risks;
- suggested next step.

Le point le plus urgent est vraiment le compteur mouvement : tant que frames_* restent à zéro, on ne peut pas interpréter correctement les politiques frénétiques ni décider proprement entre “gros réseau”, “top-3/top-5 bullets” ou “curriculum mouvement avec attaque scriptée”.