# NEXT_CODEX_TASK.md

## Goal

Add a damage / impact forensics report for evaluation runs.

The goal is to understand why the agent still gets hit in normal pressure, without changing training or simulator behavior.

For each player damage event, record a compact pre-impact context window and event summary so we can classify likely causes:

- bullet density too high;
- bad boost usage;
- bad trajectory reading;
- terrain / edge / blockage issue;
- panic / camping / ineffective input;
- missing observation information.

## Recommended Codex model / reasoning level

Use the best available full Codex/GPT model.

Recommended:

- Model: GPT-5.5 full / best available full Codex model
- Reasoning: medium-high
- Priority: correctness over token economy

Reason: this task is diagnostic infrastructure. It should not alter simulator behavior, but it touches eval loops, replay/debug info, report generation, matrix bundling, and episode-step metadata. A misleading forensics report would lead to bad RL decisions.

## Non-goals

Do not change simulator physics.

Do not change rewards, observations, action spaces, pressure profiles, model loading, PPO training, or replay semantics.

Do not implement a new curriculum.

Do not add terrain/topology observations yet.

Do not claim definitive counterfactual avoidability unless a real deterministic branch/replay counterfactual is implemented. For now, report “avoidability hints” / “available options”, not a proof that an impact was avoidable.

## Context

The current champion branch is M1 movement with scripted attack and boost, trained through:

    slow4 1M
    -> slow2 500k
    -> normal 500k

Further +500k normal did not improve robustly and degraded transfer. Before changing reward, observation, or curriculum, we need to know why the remaining normal-pressure impacts happen.

The useful report is: for every hit, what was the hero doing in the seconds before impact, what bullets were nearby, whether boost/jump/duck were available, whether the hero was blocked/camping, and whether this looks like a pressure problem, boost misuse, trajectory problem, terrain problem, or policy panic.

## CLI additions

Add optional damage forensics to `scripts.evaluate_model`:

    --damage-forensics on/off
    --damage-forensics-window N

Default:

    --damage-forensics off
    --damage-forensics-window 60

Add forwarding support in `scripts.evaluate_matrix`:

    --damage-forensics
    --damage-forensics-window N

When enabled in `evaluate_matrix`, every child eval should produce and bundle its own damage forensics report.

Optional, only if simple and safe:

- forward equivalent flags through `run_experiment` final evals;
- forward through `run_experiment_pair`.

If forwarding through training orchestration is not trivial, keep this task focused on `evaluate_model` and `evaluate_matrix`.

## Output files

For `evaluate_model`, when enabled, write next to the eval report:

    reports/damage_forensics_<report_stem>.json
    reports/damage_forensics_<report_stem>.md

or a similarly unambiguous name.

The eval report JSON should include paths to these files, if produced.

For `evaluate_matrix`, copy each job’s forensics files into:

    jobs/<eval_id>/damage_forensics.json
    jobs/<eval_id>/damage_forensics.md

and include them in the matrix bundle.

The matrix summary should mention whether forensics is available for each eval.

## Data collection design

Do not require full replay saving.

During evaluation, maintain a rolling ring buffer of the last N step snapshots for each episode. When player damage increases, emit a damage event record containing:

- event identity:
  - episode index;
  - impact frame;
  - event index in episode;
  - damage delta;
  - health before / after, if available;
  - termination reason, if the event caused death;
- runtime config:
  - training profile;
  - control mode;
  - reward profile;
  - pressure profile;
  - model choice;
  - experiment path;
  - max episode steps;
- hero state at impact:
  - x, y;
  - vx, vy;
  - grounded / airborne;
  - ducking, if available;
  - jumping / jump input;
  - boost pressed;
  - boost ready;
  - boost active, if available;
  - boost cooldown or frames until ready, if available;
  - frames since last boost activation;
  - frames since last landing;
  - frames since last grounded state change, if available;
  - frames since last damage;
- input / motion:
  - policy action;
  - full simulator action;
  - horizontal input;
  - jump input;
  - duck input;
  - boost input;
  - actual dx during recent frames;
  - effective/ineffective horizontal movement if available;
  - pressing left at left edge;
  - pressing right at right edge;
  - any existing input-motion mismatch fields;
- edge / terrain hints:
  - distance to world left edge;
  - distance to world right edge;
  - frames at left/right edge recently;
  - max consecutive frames at edge recently;
  - any available obstacle/blockage diagnostics;
  - if terrain blockage is not currently measurable, write null and note this limitation;
- bullets:
  - visible enemy bullet count at impact;
  - top visible enemy bullets with relative x/y and velocity if available;
  - nearest bullet by distance;
  - best candidate hitting bullet, if inferable;
  - approximate time-to-impact / closest-approach estimate for nearest bullets;
  - whether the hitting/candidate bullet was in the observation top-K, if inferable;
  - max visible bullet count in the pre-impact window;
- pre-impact window:
  - last N compact snapshots before the impact;
  - each snapshot should be compact and not duplicate huge action frequency maps;
  - include frame, hero x/y/vx/vy, key state flags, action, actual dx, visible bullet count, nearest bullet relative position/velocity, edge/blockage hints.

## Avoidability hints

Add a non-authoritative section per damage event:

    avoidability_hints

It may include booleans / small fields such as:

- boost_ready_within_15_frames_before_impact;
- boost_pressed_when_not_ready_before_impact;
- boost_available_but_not_pressed_near_impact;
- grounded_with_jump_available_before_impact;
- duck_available_before_impact;
- horizontal_escape_room_left;
- horizontal_escape_room_right;
- pressing_into_edge_near_impact;
- low_visible_bullet_count_but_hit_anyway;
- high_visible_bullet_count_at_impact;
- candidate_bullet_in_observation;
- candidate_bullet_missing_from_observation;
- impact_while_boost_active_or_recent;
- impact_shortly_after_landing;
- impact_during_long_airborne_streak.

Do not label these as definitive “avoidable=true/false”. Use wording like:

    "heuristic_only": true

## Aggregate summary

Generate aggregate metrics in the JSON and Markdown:

- total damage events;
- damage events per episode;
- damage-free episode count/rate;
- damage events by pressure profile;
- damage events by hero state:
  - grounded;
  - airborne;
  - ducking;
  - boost active/recent;
  - boost ready but not used;
  - near edge;
  - pressing into edge;
- average visible bullets at impact;
- average nearest bullet distance / approximate time-to-impact;
- fraction of impacts where candidate bullet was in observation, if inferable;
- impacts occurring within X frames after boost activation;
- impacts occurring while boost was not ready;
- impacts occurring shortly after landing;
- impacts during high bullet density;
- impacts during low bullet density;
- top suspected categories with counts, using simple heuristic tags.

Heuristic tags may include:

- high_bullet_density
- boost_misuse_or_cooldown
- possible_missed_boost
- possible_missed_jump_or_duck
- edge_or_blockage
- low_density_reading_failure
- observation_candidate_missing
- unclear

These tags must be explicitly documented as heuristics.

## Integration with existing reports

Do not bloat the main eval report with every pre-impact frame if this would make reports huge.

Prefer:

- main eval report contains paths and high-level forensics summary;
- full forensics details live in separate damage_forensics JSON/MD.

The matrix CSV/Markdown should include only compact aggregate forensics fields, for example:

- damage_events
- high_bullet_density_hits
- boost_related_hits
- edge_or_blockage_hits
- low_density_reading_failure_hits
- candidate_missing_from_obs_hits
- unclear_hits

## Files to inspect first

- `scripts/evaluate_model.py`
- `scripts/evaluate_matrix.py`
- `ha2_env.py`
- `ha2_replay.py`
- `scripts/runtime_config.py`
- `scripts/invocation_metadata.py`, if present
- tests for eval reports and matrix reports
- docs under `docs/ai/`

## Tests

Add tests using fake step snapshots and fake damage events where possible.

Required tests:

- damage forensics is off by default.
- enabling `--damage-forensics` writes JSON and Markdown files.
- `--damage-forensics-window N` limits the pre-impact window.
- a fake damage delta creates one damage event record.
- multiple damage deltas in one episode create multiple event records.
- no damage creates an empty event list and valid aggregate summary.
- aggregate summary counts grounded/airborne/boost/edge categories correctly from fake data.
- avoidability hints are marked as heuristic, not definitive.
- `evaluate_matrix --damage-forensics` forwards the flag to child eval commands.
- matrix job directories include copied forensics files.
- matrix bundle includes forensics files.
- existing evaluate_model/evaluate_matrix behavior without the flag remains unchanged.

Avoid expensive PPO evals in normal tests. Use mocks/fakes where possible.

## Validation

Run:

    .venv\Scripts\python.exe -m py_compile scripts/evaluate_model.py scripts/evaluate_matrix.py ha2_env.py ha2_replay.py

Run:

    .venv\Scripts\python.exe -m pytest -q

Run a tiny smoke eval if a local experiment exists:

    .venv\Scripts\python.exe -m scripts.evaluate_matrix --matrix-name damage_forensics_smoke --entry "label=M1;experiment=experiments\20260518_163253_combat_bullets_v1_movement_scripted_attack_direct_defense_v1_normal_500000_b;model=latest" --pressure-profiles normal --episodes 1 --max-episode-steps 600 --max-parallel 1 --threads-per-job 1 --no-save-replays --damage-forensics --damage-forensics-window 60

Verify the produced bundle contains:

- matrix_summary.md
- jobs/<eval_id>/eval_report.json
- jobs/<eval_id>/damage_forensics.json
- jobs/<eval_id>/damage_forensics.md
- jobs/<eval_id>/metadata.json
- command/argv/resolved config metadata if present in current codebase.

Then run a slightly more useful targeted eval if time allows:

    .venv\Scripts\python.exe -m scripts.evaluate_matrix --matrix-name M1_champion_damage_forensics_normal_3600 --entry "label=M1_champion;experiment=experiments\20260518_163253_combat_bullets_v1_movement_scripted_attack_direct_defense_v1_normal_500000_b;model=latest" --pressure-profiles normal --episodes 20 --max-episode-steps 3600 --max-parallel 3 --threads-per-job 3 --no-save-replays --damage-forensics --damage-forensics-window 90

## Acceptance criteria

Complete only if:

- damage forensics can be enabled from `evaluate_model`;
- damage forensics can be enabled from `evaluate_matrix`;
- forensics output is event-based and does not require full replay saving;
- every damage event has a compact pre-impact context window;
- aggregate summaries are generated in JSON and Markdown;
- matrix bundles include all forensics outputs;
- heuristic avoidability/cause tags are clearly marked as heuristic;
- no training/simulator behavior changes;
- tests pass;
- smoke validation passes.

## Stop conditions

Stop and report if:

- current eval info does not expose enough per-step state to produce meaningful forensics;
- detecting damage events reliably would require simulator behavior changes;
- bullet identity cannot be inferred reliably;
- adding this to evaluate_model requires a broad refactor;
- forensics output becomes too large for normal use;
- the task starts turning into terrain/topology observation work or curriculum work.

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
- what per-impact fields are available;
- what fields are null because the simulator does not expose them yet;
- limitations of the heuristic tags;
- suggested next step.