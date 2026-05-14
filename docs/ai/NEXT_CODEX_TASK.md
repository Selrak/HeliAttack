## Goal

Improve the VecEnv benchmark and training/evaluation controls so we can accurately measure HA2 PPO wall-clock speed before moving on to defensive diagnostics.

The previous benchmark showed that:

- `DummyVecEnv` works and is currently fastest at `n_envs=4` in wall-clock time.
- `SubprocVecEnv` works on Windows, but is not faster in the measured 8192-step benchmark.
- SB3-reported fps can be misleading compared with measured wall-clock steps/s.
- Subproc training currently triggers an SB3 warning because the training env is `SubprocVecEnv` while the training-time eval env is `DummyVecEnv`.

This task should make the benchmark answer three separate questions:

1. How fast is pure PPO training with no training-time evaluation?
2. How expensive is training-time evaluation?
3. How fast is the normal workflow that includes periodic EvalCallback and best-model saving?

Do not add defensive metrics yet.

## Non-goals

Do not change HA2 simulator physics, collision, rendering, player movement, Heli behavior, bullet behavior, reward formula, observations, action space, replay determinism, or AS parity logic.

Do not add defensive diagnostics in this task.

Do not add reward shaping.

Do not add `combat_defense_v1`.

Do not switch the default vector env. Keep `dummy` as the default.

Do not optimize CUDA in this task.

Do not verify dual-computer sync.

## Context

Current state:

- `training_profile="combat_v1"` is the current RL profile.
- `scripts.run_experiment` is the canonical training/evaluation entry point.
- `scripts.train_parkour` and `scripts.run_experiment` now support `--vec-env dummy|subproc`.
- `scripts.benchmark_vec_envs` writes JSON/Markdown reports under `reports/vec_env_benchmarks/`.
- Current default remains `dummy`.
- Larger benchmark result with `8192` timesteps, two repeats:
  - `dummy`, `n_envs=4`: about `323-325` computed steps/s.
  - `subproc`, `n_envs=4`: about `306-308` computed steps/s.
  - `dummy`, `n_envs=8`: about `255-264` computed steps/s.
  - `subproc`, `n_envs=8`: about `247-248` computed steps/s.
- SB3 fps was much higher for `subproc n_envs=8`, but measured wall-clock was worse, so benchmark reports must prioritize wall-clock.
- SB3 warning observed with subproc:
  - training env: `SubprocVecEnv`
  - eval env: `DummyVecEnv`
  - training still completes, but the warning means the benchmark is not clean.

## Files to inspect first

- `scripts/train_parkour.py`
- `scripts/run_experiment.py`
- `scripts/benchmark_vec_envs.py`
- `scripts/evaluate_model.py`
- `scripts/experiment_utils.py`
- `tests/test_vec_env_benchmark.py`
- `tests/test_experiment_outputs.py`
- `docs/ai/CURRENT_STATE.md`
- `docs/ai/VALIDATION.md`
- `docs/ai/CODEX_SESSION_LOG.md`

## Files likely to modify

Codex should verify from the repo, but likely:

- `scripts/train_parkour.py`
- `scripts/run_experiment.py`
- `scripts/benchmark_vec_envs.py`
- `tests/test_vec_env_benchmark.py`
- possibly `tests/test_experiment_outputs.py`
- `docs/ai/CURRENT_STATE.md`
- `docs/ai/VALIDATION.md`
- `docs/ai/CODEX_SESSION_LOG.md`

## Implementation plan

1. Inspect how `train_parkour.py` currently creates:
   - training env;
   - training-time evaluation env for `EvalCallback`;
   - evaluation frequency;
   - number of training-time eval episodes;
   - model saving/checkpointing.

2. Add explicit training-time evaluation controls to `train_parkour.py`.

   Add CLI options:

   ```text
   --train-eval on|off
   --eval-freq <int>
   --train-eval-episodes <int>
   --eval-vec-env dummy|subproc|same

Requirements:

Default behavior should preserve current behavior as closely as possible.
--train-eval off must disable EvalCallback entirely.
--eval-vec-env same should use the same VecEnv class as training.
--eval-vec-env dummy should force DummyVecEnv for eval.
--eval-vec-env subproc should force SubprocVecEnv for eval.
If --vec-env subproc --eval-vec-env same, the SB3 warning about mismatched env types should disappear.
If keeping DummyVecEnv eval with SubprocVecEnv training, the benchmark report should record that wrapper types differ.

Add equivalent pass-through options to run_experiment.py.

run_experiment.py should pass the new training-eval arguments through to train_parkour.py.

Keep final evaluation behavior unchanged unless a tiny refactor is needed.

Improve scripts.benchmark_vec_envs.

Add benchmark modes:

--mode train-only
--mode workflow
--mode both

Definitions:

train-only: runs PPO training with --train-eval off; measures pure training wall-clock.
workflow: runs PPO training with training-time EvalCallback enabled; measures realistic training workflow wall-clock.
both: runs both modes for each matrix case.

Default should be train-only or both; choose the safer default for speed, but document it in --help.

Benchmark report improvements.

JSON and Markdown reports should include, per run:

mode: train-only or workflow;
vec_env;
eval_vec_env;
n_envs;
repeat;
requested_timesteps;
actual total timesteps if available;
wall-clock seconds;
computed requested steps/s;
computed actual steps/s if actual timesteps are available;
SB3 reported fps if available;
whether training-time eval was enabled;
eval frequency;
train eval episodes;
whether training/eval VecEnv wrapper types matched;
whether SB3 emitted the wrapper mismatch warning, if detectable;
experiment path;
exception, if any.

Make warning handling explicit.

Do not simply suppress the SB3 warning globally.

Either:

fix it when --eval-vec-env same is selected; or
capture/report that wrapper mismatch occurred.

It is acceptable for --eval-vec-env dummy with --vec-env subproc to still warn, but the benchmark report must make this clear.

Add a compact summary section.

Markdown report should include:

best wall-clock result per mode;
best result per vec_env;
average computed steps/s by (mode, vec_env, n_envs);
short note that wall-clock is the primary metric, not SB3 fps.

Keep benchmark runs bounded.

The existing benchmark command should still work:

python -m scripts.benchmark_vec_envs --total-timesteps 8192 --repeats 2 --vec-envs dummy subproc --n-envs 1 2 4 8 --wandb off --device cpu

But now it should be possible to run:

python -m scripts.benchmark_vec_envs --mode train-only --total-timesteps 8192 --repeats 2 --vec-envs dummy subproc --n-envs 1 2 4 8 --wandb off --device cpu

and:

python -m scripts.benchmark_vec_envs --mode workflow --total-timesteps 8192 --repeats 2 --vec-envs dummy subproc --n-envs 1 2 4 8 --eval-vec-env same --wandb off --device cpu

Add tests.

Tests should verify:

train_parkour --train-eval off works for a tiny dummy run.
train_parkour --vec-env subproc --eval-vec-env same works for a tiny run.
benchmark_vec_envs --mode train-only writes JSON/Markdown.
benchmark_vec_envs --mode workflow writes JSON/Markdown.
benchmark report includes mode, eval settings, and wrapper-match fields.
invalid mode or invalid eval vec env fails clearly.
Documentation.

Update docs/ai/VALIDATION.md with a short validation command for:

train-only benchmark;
workflow benchmark.

Update docs/ai/CURRENT_STATE.md with the new benchmark modes and eval controls.

Append to docs/ai/CODEX_SESSION_LOG.md.

Do not add an architecture decision unless changing defaults, which this task should not do.

Validation

Run from repo root:

python -m py_compile ha2_env.py ha2_replay.py extract_ha2_data.py ha2_constants.py
python -m py_compile scripts/experiment_utils.py scripts/train_parkour.py scripts/evaluate_model.py scripts/watch_model.py scripts/run_experiment.py scripts/benchmark_vec_envs.py
python -m pytest

Run small training/eval-control smokes:

python -m scripts.train_parkour --total-timesteps 1024 --n-envs 1 --vec-env dummy --train-eval off --wandb off
python -m scripts.train_parkour --total-timesteps 1024 --n-envs 2 --vec-env subproc --eval-vec-env same --train-eval on --train-eval-episodes 1 --wandb off

Run benchmark smokes:

python -m scripts.benchmark_vec_envs --mode train-only --total-timesteps 2048 --repeats 1 --vec-envs dummy subproc --n-envs 1 2 --wandb off --device cpu
python -m scripts.benchmark_vec_envs --mode workflow --total-timesteps 2048 --repeats 1 --vec-envs dummy subproc --n-envs 1 2 --eval-vec-env same --wandb off --device cpu

Run replay determinism checks:

python -m scripts.record_random_replay --steps 300 --out replays/smoke.jsonl
python -m scripts.verify_replay replays/smoke.jsonl
python -m scripts.record_scripted_trace --scenario all
python -m scripts.verify_replay reports/parity_traces/walk_right_120.jsonl
python -m scripts.verify_replay reports/parity_traces/fire_right_60.jsonl
python -m scripts.verify_replay reports/parity_traces/fire_at_heli_180.jsonl
python -m scripts.verify_replay reports/parity_traces/heli_shoots_hero_240.jsonl
python -m scripts.verify_replay reports/parity_traces/kill_heli_respawn_600.jsonl
Manual checks

No GUI check is required.

After this task, Charles should run:

python -m scripts.benchmark_vec_envs --mode both --total-timesteps 8192 --repeats 2 --vec-envs dummy subproc --n-envs 1 2 4 8 --eval-vec-env same --wandb off --device cpu

Then compare:

train-only speed;
workflow speed;
evaluation overhead;
wrapper-matched SubprocVecEnv behavior;
best wall-clock configuration.
Acceptance criteria

The task is complete only if:

existing tests pass;
replay/scripted trace verification still passes;
current defaults remain stable;
--train-eval off works;
--eval-vec-env same works for SubprocVecEnv without the SB3 wrapper mismatch warning, or the remaining warning is explained and logged;
benchmark reports distinguish train-only from workflow mode;
benchmark reports include eval settings and wrapper-match status;
Markdown reports identify the best wall-clock configuration;
no reward, observation, action-space, simulator, or replay behavior changes are made.
Stop conditions

Stop and report instead of improvising if:

matching eval VecEnv type requires a large refactor;
SubprocVecEnv eval cannot work reliably on Windows;
EvalCallback setup becomes too coupled to training code;
disabling training-time eval breaks model saving in an unclear way;
benchmark tests become slow or flaky;
any replay hash changes unexpectedly;
reward/observation/simulator changes seem necessary.
Required Codex session log

Update:

docs/ai/CURRENT_STATE.md
docs/ai/VALIDATION.md
docs/ai/CODEX_SESSION_LOG.md

The log must include:

files changed;
commands run;
pass/fail result;
benchmark report paths;
train-only benchmark summary;
workflow benchmark summary;
whether eval wrapper mismatch warning remains;
recommended local training configuration based on measured wall-clock;
remaining risks;
suggested next step.

Suggested next step after this task, not part of this task:

add defensive diagnostics only:
enemy bullets spawned;
enemy bullet hit rate against player;
damage event frames;
time to first damage;
frames between damage events;
longest damage-free streak;
damage-free episode count.

The current provisional conclusion remains: **do not switch to SubprocVecEnv yet**. Dummy with `n_envs=4`