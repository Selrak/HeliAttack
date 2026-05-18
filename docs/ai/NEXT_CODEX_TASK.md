# NEXT_CODEX_TASK.md

## Goal

Implement a dedicated Python evaluation-matrix runner.

Create a script, preferably:

- `scripts/evaluate_matrix.py`

The script should run cross-evaluation matrices such as:

- M0 latest evaluated under slow4 / slow2 / normal
- M1 best evaluated under slow4 / slow2 / normal

It must replace fragile ad hoc PowerShell matrix scripts.

## Recommended Codex model / reasoning level

Use the best available full Codex/GPT model, not the mini model.

Recommended:

- Model: GPT-5.5 full / best available full Codex model
- Reasoning: medium-high
- Priority: correctness over token economy

Reason: this is orchestration/tooling, not simulator physics, but it touches subprocess execution, Windows paths, parallelism, report naming, bundle generation, experiment metadata, and reproducibility. Bugs here can make evaluation results ambiguous or misleading.

## Non-goals

Do not change simulator behavior.

Do not change rewards, observations, action spaces, pressure profiles, replay semantics, training behavior, or model loading behavior.

Do not implement full multi-phase curriculum training yet.

Do not modify PPO training logic.

Do not require PowerShell-specific behavior. The script should be cross-platform Python.

## Context

We are now repeatedly running evaluation matrices across different models and pressure profiles.

The current PowerShell approach has problems:

- parallel job output appears in confusing order;
- progress messages like `eval 6/6 START` are not globally meaningful;
- auto-detecting experiment/model paths is fragile;
- uploaded eval reports from different experiments can have identical or ambiguous filenames;
- manually bundling results is error-prone.

We need a dedicated script that produces a self-contained, unambiguous result bundle.

## Required CLI

Add a script runnable as:

    python -m scripts.evaluate_matrix ...

Support entries via repeated `--entry` arguments.

Use a robust entry format that works with Windows paths. For example:

    --entry "label=M0;experiment=experiments\...\m0_exp;model=latest"
    --entry "label=M1;experiment=experiments\...\m1_exp;model=best"

Support at least:

- `--matrix-name NAME`
- `--entry "label=...;experiment=...;model=..."`
- `--pressure-profiles enemy_fire_slow_4x,enemy_fire_slow_2x,normal`
- `--episodes 20`
- `--max-episode-steps 3600`
- `--max-parallel 6`
- `--threads-per-job 3`
- `--save-replays` / `--no-save-replays`
- `--output-root experiments\eval_matrices`
- `--dry-run`

Optional but useful:

- `--reward-profile` override
- `--control-mode` override
- `--training-profile` override
- `--timeout-seconds`
- `--fail-fast`

CLI explicit overrides must be recorded clearly in the matrix metadata.

## Current-use example

The following kind of command should work for the current slow2-finetuned models:

    python -m scripts.evaluate_matrix --matrix-name slow2_transfer_3600 --entry "label=M0;experiment=experiments\20260518_150236_combat_bullets_v1_movement_no_boost_scripted_attack_direct_defense_v1_enemy_fire_slow_2x_500000_a;model=latest" --entry "label=M1;experiment=experiments\20260518_150236_combat_bullets_v1_movement_scripted_attack_direct_defense_v1_enemy_fire_slow_2x_500000_b;model=best" --pressure-profiles enemy_fire_slow_4x,enemy_fire_slow_2x,normal --episodes 20 --max-episode-steps 3600 --max-parallel 6 --threads-per-job 3 --no-save-replays

## Output structure

Create a unique matrix output directory, for example:

    experiments\eval_matrices\slow2_transfer_3600_YYYYMMDD_HHMMSS\

Inside it, create:

    matrix_config.json
    matrix_manifest.json
    matrix_summary.json
    matrix_summary.md
    matrix_summary.csv
    logs\
    jobs\
    slow2_transfer_3600_YYYYMMDD_HHMMSS_bundle.zip

Each individual eval should have its own unambiguous job directory, for example:

    jobs\
      001_M0_latest_pressure-enemy_fire_slow_4x\
        eval_report.json
        stdout.log
        stderr.log
        command.txt
        metadata.json
        parent_config.json, if available
      002_M1_best_pressure-enemy_fire_slow_4x\
        eval_report.json
        stdout.log
        stderr.log
        command.txt
        metadata.json
        parent_config.json, if available

The job directory name should be reasonably short but unambiguous.

If a name would be too long, use a short stable hash suffix and record the full details in `metadata.json` and `matrix_manifest.json`.

## Bundle requirements

At the end, create a zip bundle containing the full matrix output except the zip file itself.

The bundle must be self-describing when opened outside the repo.

The bundle must include:

- matrix config;
- matrix manifest;
- matrix summaries;
- every eval report;
- stdout/stderr logs for every eval;
- command line used for every eval;
- per-job metadata;
- parent experiment config for every entry, if available;
- a README or `matrix_summary.md` that explains how to identify each result.

The bundle must make it impossible to confuse which eval result came from which:

- source experiment;
- model choice;
- model path;
- control mode;
- training profile;
- reward profile;
- pressure profile used for evaluation;
- parent pressure profile;
- max episode steps;
- number of episodes;
- timestamp / matrix name.

Do not rely only on the original report filenames from source experiment folders.

## Naming / identity rules

Every eval job should have a stable `eval_id`, for example:

    001_M0_latest_pressure-enemy_fire_slow_4x

The manifest must map every `eval_id` to:

- label;
- experiment path;
- model choice;
- resolved model path;
- resolved config path;
- source experiment runtime config;
- evaluation overrides;
- pressure profile used during eval;
- control mode;
- reward profile;
- training profile;
- max episode steps;
- episodes;
- report path inside original experiment, if generated there;
- copied report path inside matrix output;
- stdout/stderr log paths;
- exit code;
- start/end timestamps;
- duration seconds.

## Execution behavior

The script may call `scripts.evaluate_model` as a subprocess for each eval.

Set per-job environment variables:

- `OMP_NUM_THREADS`
- `MKL_NUM_THREADS`
- `NUMEXPR_NUM_THREADS`
- `HA2_TORCH_NUM_THREADS`

Use `--threads-per-job` for these values.

Run at most `--max-parallel` subprocesses concurrently.

Do not interleave full subprocess logs into the console.

Detailed logs go to per-job stdout/stderr files.

Console output should show clear global progress only, for example:

    Matrix: slow2_transfer_3600_20260518_1600
    Total evals: 6
    Running with max_parallel=6, threads_per_job=3
    Progress: 0/6 complete, 6 running, 0 failed
    Progress: 1/6 complete, 5 running, 0 failed
    Progress: 2/6 complete, 4 running, 0 failed
    ...
    Progress: 6/6 complete, 0 running, 0 failed
    Bundle: experiments\eval_matrices\...\slow2_transfer_3600_..._bundle.zip

If a job fails, the console should say which `eval_id` failed and point to its stderr log.

## Report collection

If `evaluate_model` writes its report into the source experiment’s `reports` directory, use a unique report name containing:

- matrix name;
- run timestamp or matrix id;
- eval id.

Then copy that report into the matrix job directory as:

    eval_report.json

The matrix output should remain readable even if the source experiment folder is later moved.

## Summary generation

Generate `matrix_summary.json`, `matrix_summary.csv`, and `matrix_summary.md`.

At minimum, summarize these metrics per eval when available:

- mean reward;
- mean episode length;
- mean player damage;
- mean damage events;
- death rate;
- fall rate;
- timeout rate;
- damage-free episode rate;
- visible bullet hit rate;
- mean Heli kills;
- enemy bullets spawned;
- time to first damage;
- longest damage-free streak;
- boost activations;
- boost pressed frames;
- frames grounded / airborne;
- sum_abs_player_dx;
- left/right edge camping rates;
- input-motion mismatch rate;
- pressure profile;
- control mode;
- reward profile;
- model choice;
- experiment path.

If a metric is missing, write `null` / `n/a`, not a fake value.

## Tests

Add tests for:

- parsing repeated `--entry` values;
- rejecting malformed entries;
- generating short unambiguous eval IDs;
- creating the matrix output tree;
- writing matrix config/manifest;
- command construction for `scripts.evaluate_model`;
- per-job env thread settings;
- copying eval reports into job directories;
- generating summary JSON/CSV/MD from small fake reports;
- bundle zip contains all expected files;
- duplicate labels or ambiguous entries are rejected or disambiguated clearly;
- dry-run does not launch eval subprocesses but writes planned config/manifest.

Use fake reports and mocked subprocesses for most tests. Do not make the normal test suite run expensive PPO evals.

## Validation

Run:

    .venv\Scripts\python.exe -m py_compile scripts/evaluate_matrix.py scripts/evaluate_model.py scripts/runtime_config.py
    .venv\Scripts\python.exe -m pytest -q

Run a dry-run smoke:

    .venv\Scripts\python.exe -m scripts.evaluate_matrix --matrix-name smoke_matrix --entry "label=M0;experiment=experiments\20260518_150236_combat_bullets_v1_movement_no_boost_scripted_attack_direct_defense_v1_enemy_fire_slow_2x_500000_a;model=latest" --entry "label=M1;experiment=experiments\20260518_150236_combat_bullets_v1_movement_scripted_attack_direct_defense_v1_enemy_fire_slow_2x_500000_b;model=best" --pressure-profiles enemy_fire_slow_4x,enemy_fire_slow_2x,normal --episodes 1 --max-episode-steps 200 --max-parallel 2 --threads-per-job 1 --dry-run

If the local parent experiments exist, run a tiny real smoke:

    .venv\Scripts\python.exe -m scripts.evaluate_matrix --matrix-name smoke_matrix_real --entry "label=M0;experiment=experiments\20260518_150236_combat_bullets_v1_movement_no_boost_scripted_attack_direct_defense_v1_enemy_fire_slow_2x_500000_a;model=latest" --entry "label=M1;experiment=experiments\20260518_150236_combat_bullets_v1_movement_scripted_attack_direct_defense_v1_enemy_fire_slow_2x_500000_b;model=best" --pressure-profiles enemy_fire_slow_4x --episodes 1 --max-episode-steps 200 --max-parallel 2 --threads-per-job 1 --no-save-replays

Verify that the produced bundle opens and that each eval report is clearly traceable to its model/pressure/control/reward/training config.

## Acceptance criteria

Complete only if:

- `python -m scripts.evaluate_matrix` exists and works.
- Matrix entries can refer to different experiment folders and model choices.
- Parallel eval execution works with clean global progress output.
- Detailed logs are written per eval.
- Reports are copied into unambiguous per-job directories.
- Matrix summaries are generated.
- A self-contained zip bundle is produced at the end.
- The bundle clearly identifies every eval result.
- Dry-run works.
- Tests pass.
- Existing `evaluate_model` behavior remains compatible.

## Stop conditions

Stop and report if:

- `evaluate_model` cannot be safely called as a subprocess;
- report paths cannot be made unique without modifying `evaluate_model`;
- model/experiment identity cannot be recovered reliably;
- bundling would require a broad experiment-directory refactor;
- parallel subprocess handling becomes unreliable on Windows;
- the task starts turning into full curriculum orchestration.

## Required Codex session log

Update:

- `docs/ai/CURRENT_STATE.md`
- `docs/ai/VALIDATION.md`
- `docs/ai/CODEX_SESSION_LOG.md`

Log:

- files changed;
- commands run;
- pass/fail result;
- smoke matrix path;
- bundle path;
- example command for the current M0/M1 slow2 transfer matrix;
- known limitations;
- suggested next step.