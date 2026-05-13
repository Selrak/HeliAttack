# NEXT_CODEX_TASK.md

## Goal

Set up a robust first real HA2 RL training workflow around the existing `combat_v1` environment.

The goal is not to make the model good yet. The goal is to make every training run produce enough diagnostics to decide whether the policy is learning useful combat behavior, merely surviving, dying, standing still, firing randomly, or failing because of reward/observation/action-space issues.

Implement a bounded training orchestration and diagnostics layer so that Charles can run one command, get an experiment folder, WandB logs/artifacts, evaluation reports, saved replays, and clear combat metrics.

## Non-goals

Do not change HA2 simulator physics, collision, Heli behavior, bullet behavior, player movement, rendering, AS parity logic, or scripted parity traces unless a bug directly prevents training from running.

Do not tune the reward yet except for exposing/reporting its components more clearly.

Do not add HA3 work.

Do not add CNN/image observations.

Do not switch to GPU-specific code yet. The same scripts must still run on the Windows laptop CPU and later on Linux with GPU.

Do not broaden scope into pickups, weapons, full HUD, sounds, gameover, or full original game progression.

## Context

Current state:

- `training_profile="combat_v1"` exists and is the current RL profile.
- `combat_v1` has a fixed 37-field float32 vector observation.
- Current reward is approximately:
  - survival step reward;
  - score delta reward;
  - Heli kill reward;
  - player damage penalty;
  - termination penalty.
- `scripts.train_parkour`, `scripts.evaluate_model`, and `scripts.watch_model` already exist.
- Experiment directories already exist under `experiments/<run>/`.
- WandB artifact upload/download already exists through the training script and `scripts.sync_experiment`.
- `scripts.run_experiment.py` was previously deferred.
- Current model quality is unknown; smoke training only proves that SB3 runs, not that the policy learns.

The next architecture point is:

Training runs must become inspectable. Every run should produce structured metrics that answer:
- Did the model kill Helis?
- Did it hit Helis?
- Did it fire?
- Did it take damage?
- Did it die?
- Did it fall?
- Did it survive only by doing nothing?
- How long did episodes last?
- What actions did it choose?
- Was `best.zip` actually better than `latest.zip` under combat metrics?

## Files to inspect first

- `ha2_env.py`
- `ha2_replay.py`
- `scripts/train_parkour.py`
- `scripts/evaluate_model.py`
- `scripts/watch_model.py`
- `scripts/experiment_utils.py`
- `scripts/sync_experiment.py`
- `tests/test_rl_interface.py`
- `tests/test_experiment_outputs.py`
- `docs/ai/CURRENT_STATE.md`
- `docs/ai/ARCHITECTURE_DECISIONS.md`
- `docs/ai/VALIDATION.md`
- `docs/ai/CODEX_SESSION_LOG.md`

## Files likely to modify

Codex should verify from the repo, but likely:

- Add `scripts/run_experiment.py`
- Update `scripts/evaluate_model.py`
- Possibly update `scripts/train_parkour.py`
- Possibly update `ha2_env.py` only to expose already-existing episode/debug metrics more cleanly through `info`
- Add or update tests under `tests/`
- Update `docs/ai/CURRENT_STATE.md`
- Update `docs/ai/VALIDATION.md`
- Update `docs/ai/CODEX_SESSION_LOG.md`
- Possibly update `docs/ai/ARCHITECTURE_DECISIONS.md` if a durable training-pipeline decision is made

## Implementation plan

1. Inspect the current training/evaluation scripts and experiment utilities.

2. Add or improve per-step and per-episode `info` reporting for `combat_v1`, without changing simulator behavior.

   The `info` dict should allow evaluation code to compute at least:
   - episode return;
   - episode length;
   - termination reason;
   - player health at end;
   - total player damage taken;
   - Heli kills;
   - Heli hits if already tracked;
   - player bullets fired if already tracked, or add a counter if safe;
   - enemy bullets hit player;
   - score;
   - whether the episode ended by fall, player death, or time limit.

   If some metrics are not currently available, add the smallest safe counters needed. Do not alter game mechanics.

3. Improve `scripts.evaluate_model.py` so its JSON report contains aggregate combat diagnostics, not only mean reward.

   The report should include, when available:
   - mean/std/min/max episode reward;
   - mean/std/min/max episode length;
   - total and mean Heli kills;
   - total and mean Heli hits;
   - total and mean bullets fired;
   - hit rate if both hits and shots exist;
   - total and mean player damage;
   - death count;
   - fall count;
   - timeout/truncation count;
   - termination reason histogram;
   - per-episode rows with the same fields.

   Keep the existing behavior of saving replays.

4. Add `scripts/run_experiment.py`.

   It should orchestrate:
   - one training run using `scripts.train_parkour` internals or shared functions;
   - evaluation of `latest.zip`;
   - evaluation of `best.zip` if it exists;
   - optional saved evaluation replays;
   - optional WandB upload through existing mechanisms;
   - one final printed summary showing experiment path, model paths, report paths, replay paths, and key combat metrics.

   Prefer importing/refactoring existing code over shelling out to subprocesses, but do not do a large refactor if it risks breaking existing scripts.

5. Add useful CLI arguments to `run_experiment.py`.

   Include at least:
   - `--total-timesteps`
   - `--n-envs`
   - `--seed`
   - `--wandb`
   - `--experiment-name`
   - `--eval-episodes`
   - `--save-replays`
   - `--max-episode-steps`
   - `--device` if already supported by the train script or easy to pass through
   - `--watch` optional, default false

6. Preserve existing standalone scripts.

   `train_parkour.py`, `evaluate_model.py`, and `watch_model.py` must still work independently.

7. Add a small smoke validation path.

   A command such as:

   python -m scripts.run_experiment --total-timesteps 1000 --n-envs 1 --wandb off --eval-episodes 1 --save-replays

   must create a complete experiment folder with:
   - config;
   - git info;
   - latest model;
   - best model if SB3 produced one;
   - evaluation report for latest;
   - evaluation report for best if available;
   - at least one replay when `--save-replays` is used;
   - summary file updated with final metrics.

8. Add or update tests.

   Tests should verify:
   - `combat_v1` `info` contains the expected stable keys after reset/step and at episode end where practical.
   - evaluation report JSON contains the new aggregate sections.
   - `run_experiment.py` smoke run creates expected files.
   - existing replay/parity tests still pass.

9. Update docs.

   Update `docs/ai/VALIDATION.md` with the new canonical smoke command.

   Update `docs/ai/CURRENT_STATE.md` with what now works and what remains unknown.

   Append to `docs/ai/CODEX_SESSION_LOG.md`.

   If a durable decision is made that `run_experiment.py` is now the canonical local training entry point, append it to `docs/ai/ARCHITECTURE_DECISIONS.md`.

## Validation

Run from repo root.

Required validation:

python -m py_compile ha2_env.py ha2_replay.py extract_ha2_data.py ha2_constants.py
python -m py_compile scripts/experiment_utils.py scripts/train_parkour.py scripts/evaluate_model.py scripts/watch_model.py scripts/run_experiment.py
python -m pytest
python -m scripts.record_random_replay --steps 300 --out replays/smoke.jsonl
python -m scripts.verify_replay replays/smoke.jsonl
python -m scripts.record_scripted_trace --scenario all
python -m scripts.verify_replay reports/parity_traces/walk_right_120.jsonl
python -m scripts.verify_replay reports/parity_traces/fire_right_60.jsonl
python -m scripts.verify_replay reports/parity_traces/fire_at_heli_180.jsonl
python -m scripts.verify_replay reports/parity_traces/heli_shoots_hero_240.jsonl
python -m scripts.verify_replay reports/parity_traces/kill_heli_respawn_600.jsonl
python -c "from stable_baselines3.common.env_checker import check_env; from ha2_env import HeliAttack2Env; env=HeliAttack2Env(render_mode=None, training_profile='combat_v1', max_episode_steps=300); check_env(env, warn=True); env.close(); print('check_env passed')"
python -m scripts.run_experiment --total-timesteps 1000 --n-envs 1 --wandb off --eval-episodes 1 --save-replays

Also run, if possible:

python -m scripts.evaluate_model --experiment experiments/<created_experiment> --model-choice latest --episodes 1 --save-replays

Do not require a good model from the 1000-step run. This is a pipeline validation only.

## Manual checks

After the smoke experiment is created, Charles should be able to run:

python -m scripts.watch_model --experiment experiments/<created_experiment> --model-choice latest

If `best.zip` exists:

python -m scripts.watch_model --experiment experiments/<created_experiment> --model-choice best

Manual watch expectations:

- The model loads.
- The GUI opens.
- The selected experiment model is used.
- Fast-forward still works if already implemented.
- Saved evaluation replays can be opened with `scripts.play_replay`.
- Reports make it clear whether the model did anything useful.

## Acceptance criteria

The task is complete only if:

- Existing validation still passes.
- `scripts.run_experiment.py` exists and works.
- A smoke run creates a complete experiment directory.
- Evaluation reports include combat diagnostics, not just reward.
- Reports distinguish at least death, fall, and time-limit/truncation outcomes.
- The pipeline remains cross-platform Python and does not assume PowerShell-only behavior.
- Standalone `train_parkour`, `evaluate_model`, and `watch_model` still work.
- No simulator behavior is changed except for adding safe counters/info fields.
- Docs in `docs/ai` are updated.

## Stop conditions

Stop and report instead of improvising if:

- Adding metrics requires changing core simulator mechanics.
- Current train/evaluate scripts are too coupled for a safe small refactor.
- `best.zip` creation behavior is ambiguous or unreliable.
- WandB upload breaks previously working local/offline training.
- The new run script would require deleting or restructuring existing experiment folders.
- Tests reveal nondeterministic replay hashes after the changes.
- Any change threatens AS parity or replay determinism.

## Required Codex session log

Update:

- `docs/ai/CURRENT_STATE.md`
- `docs/ai/CODEX_SESSION_LOG.md`
- `docs/ai/VALIDATION.md`

Also update:

- `docs/ai/ARCHITECTURE_DECISIONS.md` only if `run_experiment.py` becomes the canonical local training entry point.

The log must include:

- files changed;
- commands run;
- pass/fail result;
- experiment folder created by the smoke run;
- metrics present in the new evaluation report;
- bugs encountered;
- workarounds used;
- architectural discrepancies discovered;
- remaining risks;
- suggested next step.