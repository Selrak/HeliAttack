# NEXT_CODEX_TASK.md

## Goal

Add PPO policy-capacity controls and boost/jump diagnostics for HA2 RL experiments.

The immediate reason is that `combat_bullets_v1` performed worse than matched `combat_v1` at 500k, despite exposing richer visible-bullet information. Before changing rewards or adding a curriculum, we need to test whether the richer 84-dimensional observation needs a larger policy network and whether the current policies are overusing boost/jump in a frantic, poorly timed way.

This task must add experiment knobs and diagnostics only. It must not change simulator mechanics, rewards, observations, action space, or default training behavior.

## Non-goals

Do not change HA2 physics, collision, rendering, Heli behavior, enemy bullet behavior, player movement, replay determinism, or AS parity logic.

Do not change `combat_v1` observation layout.

Do not change `combat_bullets_v1` observation layout.

Do not change any reward formula.

Do not add `combat_defense_v1`.

Do not add a no-boost or pure-jump curriculum profile yet.

Do not tune PPO defaults implicitly.

Do not change the default policy architecture unless the user explicitly selects a new architecture.

Do not change the default VecEnv; keep `dummy`.

Do not verify dual-computer sync.

## Context

Current state:

- `combat_v1` is the baseline RL profile with a 37-field observation.
- `combat_bullets_v1` is now available with an 84-field observation.
- `combat_bullets_v1` preserves the same reward and mechanics as `combat_v1`.
- `combat_bullets_v1` replaces the single nearest enemy-bullet fields with a top-10 visible-bullet block.
- Recent matched 500k runs showed `combat_bullets_v1` did not improve defense and was worse than `combat_v1`.
- Manual inspection suggests all current candidate models are frantic:
  - frequent boost/jump;
  - seemingly useless ducking;
  - no clear lateral “dancing” with bullets;
  - little use of the full map width;
  - no obviously timed evasion pattern.
- The observation audit says the profiles expose hyperjump charge, but we need to verify and document whether this field is enough to represent boost readiness/reload timing for the policy.
- It is too early to add reward shaping or curriculum. First, make policy capacity and boost-use behavior measurable.

## Files to inspect first

- `ha2_env.py`
- `scripts/train_parkour.py`
- `scripts/run_experiment.py`
- `scripts/evaluate_model.py`
- `scripts/watch_model.py`
- `scripts/experiment_utils.py`
- `tests/test_rl_interface.py`
- `tests/test_experiment_outputs.py`
- `docs/ai/OBSERVATION_AUDIT.md`
- `docs/ai/CURRENT_STATE.md`
- `docs/ai/VALIDATION.md`
- `docs/ai/CODEX_SESSION_LOG.md`

## Files likely to modify

Codex should verify from the repo, but likely:

- `scripts/train_parkour.py`
- `scripts/run_experiment.py`
- `scripts/evaluate_model.py`
- `scripts/watch_model.py`, only if model-loading metadata or help text needs updating
- `ha2_env.py`, only for extra diagnostics exposed in `info`; do not change observation/reward/mechanics
- tests under `tests/`
- `docs/ai/OBSERVATION_AUDIT.md`
- `docs/ai/CURRENT_STATE.md`
- `docs/ai/VALIDATION.md`
- `docs/ai/CODEX_SESSION_LOG.md`

## Implementation plan

### 1. Add policy network architecture CLI support

Add a CLI option to `train_parkour.py` and pass it through from `run_experiment.py`:

- `--net-arch 64,64`
- `--net-arch 128,128`
- `--net-arch 256,256`

The option should accept a comma-separated list of positive integers.

Default behavior must remain exactly the current SB3 default unless the user passes `--net-arch`.

If the current code already sets a custom policy architecture, preserve that as the effective default and document it.

When `--net-arch` is provided, pass the corresponding `policy_kwargs` to PPO.

### 2. Record policy configuration in experiment artifacts

Record in `config.json` and `summary.md`:

- selected policy class;
- selected `net_arch`, or `default` if not provided;
- activation function if explicitly set or if easy to extract;
- approximate trainable parameter count if easy to compute after model creation;
- observation dimension;
- training profile.

Do not fail if parameter count is difficult, but prefer to include it.

### 3. Add policy metadata to evaluation reports

Add report metadata to `evaluate_model.py` where possible:

- training profile;
- observation dimension;
- policy architecture from config, if available;
- model choice: best/latest;
- model path.

Do not change the metric structure incompatibly.

### 4. Audit boost/hyperjump observation semantics

Inspect `ha2_env.py` and document exactly what the existing hyperjump/boost-related observation field means.

Answer in `docs/ai/OBSERVATION_AUDIT.md`:

- Is boost/hyperjump readiness exposed?
- Is cooldown or reload progress exposed?
- Is the value normalized?
- Does the value tell the policy when boost is usable now?
- Does it differ between grounded, airborne, and boost-flight phases?
- Is there any separate field indicating that the player is currently in boost/hyperjump motion?
- Is there any separate field indicating standard jump availability or double-jump availability?

Do not change the observation in this task. If the current observation is ambiguous or insufficient, document that as a future design issue.

### 5. Add boost/jump behavior diagnostics

Extend evaluation diagnostics with action-state metrics that help distinguish frantic movement from timed movement.

Add per-episode and aggregate metrics such as:

- fraction of frames grounded;
- fraction of frames airborne;
- fraction of frames where boost/hyperjump is ready, if measurable;
- fraction of frames where boost action is pressed;
- fraction of frames where boost action is pressed while boost is ready;
- fraction of frames where boost action is pressed while boost is not ready;
- number of actual boost/hyperjump activations, if distinguishable from merely pressing the boost action;
- mean frames between boost activations;
- fraction of frames where jump is pressed;
- jump presses while grounded;
- jump presses while airborne;
- duck fraction, already present if action marginals exist, but keep or surface it in the summary;
- horizontal movement distribution, already present if action marginals exist, but keep or surface it in the summary.

Use stable names and JSON null where a denominator is zero or a metric is undefined.

Do not change movement mechanics.

### 6. Add lateral movement / map-width diagnostics

Add simple diagnostics to tell whether the model uses the map width or stays in a narrow band:

- min player x during episode;
- max player x during episode;
- player x range;
- mean player x;
- fraction of frames moving left;
- fraction of frames moving right;
- fraction of frames with no horizontal movement;
- optionally fraction of frames near left/right map boundaries if those bounds are already reliable.

Do not alter camera or map logic.

### 7. Extend summary.md compact comparison

Extend the best/latest summary table with compact rows for:

- net architecture;
- observation dimension;
- mean player x range;
- grounded fraction;
- airborne fraction;
- boost action fraction;
- boost-ready fraction, if available;
- boost-pressed-while-ready fraction, if available;
- actual boost activations per episode, if available;
- jump action fraction;
- duck action fraction.

Keep this readable. Do not dump every diagnostic into summary.md.

### 8. Add tests

Tests should verify:

- `--net-arch 128,128` is parsed correctly.
- invalid `--net-arch` values fail clearly.
- `run_experiment.py` passes `--net-arch` through to training.
- experiment `config.json` records the selected net architecture.
- summary/report metadata includes the selected net architecture.
- default behavior remains unchanged when `--net-arch` is omitted.
- `combat_v1` observation shape remains 37.
- `combat_bullets_v1` observation shape remains 84.
- boost/jump diagnostic keys are present in evaluation reports.
- diagnostics handle episodes with no boost activations cleanly.
- existing replay/scripted trace validation still passes.

### 9. Do not train a real model in this task

Only run smoke training.

The matched 500k experiments will be run after this task.

## Validation

Run from repo root:

- `python -m py_compile ha2_env.py ha2_replay.py extract_ha2_data.py ha2_constants.py`
- `python -m py_compile scripts/experiment_utils.py scripts/train_parkour.py scripts/evaluate_model.py scripts/watch_model.py scripts/run_experiment.py scripts/benchmark_vec_envs.py`
- `python -m pytest`
- `python -m scripts.record_random_replay --steps 300 --out replays/smoke.jsonl`
- `python -m scripts.verify_replay replays/smoke.jsonl`
- `python -m scripts.record_scripted_trace --scenario all`
- `python -m scripts.verify_replay reports/parity_traces/walk_right_120.jsonl`
- `python -m scripts.verify_replay reports/parity_traces/fire_right_60.jsonl`
- `python -m scripts.verify_replay reports/parity_traces/fire_at_heli_180.jsonl`
- `python -m scripts.verify_replay reports/parity_traces/heli_shoots_hero_240.jsonl`
- `python -m scripts.verify_replay reports/parity_traces/kill_heli_respawn_600.jsonl`
- `python -c "from stable_baselines3.common.env_checker import check_env; from ha2_env import HeliAttack2Env; env=HeliAttack2Env(render_mode=None, training_profile='combat_bullets_v1', max_episode_steps=300); check_env(env, warn=True); env.close(); print('check_env combat_bullets_v1 passed')"`
- `python -m scripts.run_experiment --training-profile combat_bullets_v1 --total-timesteps 1000 --n-envs 1 --vec-env dummy --wandb off --eval-episodes 1 --save-replays --net-arch 128,128`

Optional, if quick:

- `python -m scripts.run_experiment --training-profile combat_v1 --total-timesteps 1000 --n-envs 1 --vec-env dummy --wandb off --eval-episodes 1 --save-replays --net-arch 128,128`

## Manual checks

No GUI check is required.

After the task, Charles should run matched experiments, for example:

- `python -m scripts.run_experiment --training-profile combat_v1 --total-timesteps 500000 --n-envs 4 --vec-env dummy --wandb off --train-eval on --eval-freq 50000 --train-eval-episodes 2 --eval-episodes 10 --save-replays --net-arch 128,128`

- `python -m scripts.run_experiment --training-profile combat_bullets_v1 --total-timesteps 500000 --n-envs 4 --vec-env dummy --wandb off --train-eval on --eval-freq 50000 --train-eval-episodes 2 --eval-episodes 10 --save-replays --net-arch 128,128`

Then compare against the previous matched 64-ish/default policy runs.

## Acceptance criteria

The task is complete only if:

- `--net-arch` exists and works.
- Default behavior remains unchanged when `--net-arch` is omitted.
- Selected net architecture is recorded in experiment config and summary.
- Evaluation report metadata includes policy/profile/observation information where available.
- Boost/hyperjump observation semantics are documented.
- Boost/jump/lateral movement diagnostics are present in evaluation reports.
- `combat_v1` observation shape remains unchanged.
- `combat_bullets_v1` observation shape remains unchanged.
- No reward shaping is introduced.
- No simulator mechanics are changed.
- Existing tests and replay validations pass.
- A 1000-step `combat_bullets_v1 --net-arch 128,128` smoke experiment succeeds.

## Stop conditions

Stop and report instead of improvising if:

- current policy architecture is not accessible or is already custom in a non-obvious way;
- `--net-arch` requires a larger training-script refactor than expected;
- boost readiness/reload semantics are unclear in the simulator state;
- actual boost activation cannot be distinguished from boost button press without changing mechanics;
- adding diagnostics risks changing replay state hashes;
- observation shapes change unexpectedly;
- reward or observation changes seem necessary;
- tests become nondeterministic;
- any replay verification changes unexpectedly.

## Required Codex session log

Update:

- `docs/ai/CURRENT_STATE.md`
- `docs/ai/VALIDATION.md`
- `docs/ai/CODEX_SESSION_LOG.md`
- `docs/ai/OBSERVATION_AUDIT.md`

The log must include:

- files changed;
- commands run;
- pass/fail result;
- default policy architecture behavior;
- how `--net-arch` is parsed and recorded;
- final observation dimensions for `combat_v1` and `combat_bullets_v1`;
- boost/hyperjump observation audit summary;
- boost/jump/lateral diagnostics added;
- smoke experiment path;
- remaining risks;
- suggested next step.