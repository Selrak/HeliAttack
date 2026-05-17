# NEXT_CODEX_TASK.md

## Goal

Implement an opt-in `pressure_profile` curriculum layer to reduce enemy Heli fire frequency during training/evaluation/manual play.

This is meant to make movement ↔ bullet-avoidance causality easier to learn without changing bullet speed, bullet damage, player physics, observations, action spaces, or the default game behavior.

## Non-goals

Do not change default HA2 mechanics.

Do not change bullet speed, bullet damage, Heli movement, player movement, rewards, observations, action spaces, or replay semantics for default runs.

Do not add trajectory-distance shaping or near-miss reward.

Do not run 500k yet.

## Context

`defense_v1` is now technically active: 10 player damage gives about `-10`, not the old `-0.99`.

However, M0_defense still tends to fail/camp, and M1_defense improves mostly through boost/mobility rather than clean bullet avoidance.

Next curriculum idea: keep the same bullets, same damage, same physics, but reduce enemy fire frequency temporarily so PPO can more clearly learn the causal link between movement and avoided impacts.

## Implement `pressure_profile`

Add supported values:

- `normal`
- `enemy_fire_slow_2x`
- `enemy_fire_slow_4x`

Default must be `normal`.

Semantics:

- `normal`: current behavior, unchanged.
- `enemy_fire_slow_2x`: enemy Helis fire half as often.
- `enemy_fire_slow_4x`: enemy Helis fire one quarter as often.

Prefer implementing this by scaling the enemy Heli fire interval / reload threshold, not by changing bullet speed, bullet damage, bullet collision, or bullet lifetime.

Keep constants easy to find in code.

## CLI support

Add `--pressure-profile` to:

- `scripts.train_parkour`
- `scripts.run_experiment`
- `scripts.run_experiment_pair`
- `scripts.evaluate_model`
- `scripts.watch_model`
- `scripts.play_human`

Add pair-runner overrides:

- `--pressure-profile`
- `--pressure-profile-a`
- `--pressure-profile-b`

Common `--pressure-profile` applies to both jobs unless overridden.

## Manual play support

`play_human` must accept `--pressure-profile`.

This is important: manual human play should be able to test the same reduced-fire regimes used by RL.

Examples should work:

- `.venv\Scripts\python.exe -m scripts.play_human --pressure-profile normal`
- `.venv\Scripts\python.exe -m scripts.play_human --pressure-profile enemy_fire_slow_2x`
- `.venv\Scripts\python.exe -m scripts.play_human --pressure-profile enemy_fire_slow_4x`

The debug panel should show the active pressure profile and enough enemy-fire counters to verify the cadence difference.

## Replay / watch / verification support

Record `pressure_profile` in replay headers.

Replay verification must instantiate/replay with the recorded `pressure_profile`.

`play_replay` must display or at least preserve the pressure profile from the replay header. It should not require a manual `--pressure-profile` for existing replay files unless overriding is explicitly requested.

`watch_model` must infer `pressure_profile` from the experiment `config.json`, like `control_mode` and `reward_profile`.

If `watch_model --pressure-profile ...` is passed explicitly, it may override config, but this must be clearly logged.

## Reports, summaries, graphs

Record `pressure_profile` in:

- `config.json`
- `summary.md`
- `eval_best.json`
- `eval_latest.json`
- replay header
- pair summary JSON/Markdown
- timing/orchestration metadata if practical

Update all summary tables/graphs/plots produced by the experiment pipeline so comparisons label:

- training profile
- control mode
- reward profile
- pressure profile

Any generated comparison graph must not silently compare runs with different pressure profiles without showing the difference.

Also finish the small reporting gap from the previous reward-profile work:

- include `reward_profile` in replay headers;
- include `reward_profile` in eval reports;
- expose `reward_breakdown` in eval reports and replay debug if practical.

## Tests

Add tests for:

- default `pressure_profile="normal"` preserves current enemy fire cadence;
- `enemy_fire_slow_2x` fires less often than normal over a deterministic fixed horizon;
- `enemy_fire_slow_4x` fires less often than `enemy_fire_slow_2x`;
- bullet speed/damage are unchanged under pressure profiles;
- `pressure_profile` is recorded in config/eval/replay header;
- replay verification uses the recorded `pressure_profile`;
- `play_human` accepts all pressure-profile values;
- `watch_model` infers pressure profile from config;
- `run_experiment_pair` forwards common and A/B pressure profiles;
- default old commands still work without specifying pressure profile.

Keep tests short and deterministic.

## Validation

Run:

- `.venv\Scripts\python.exe -m py_compile ha2_env.py ha2_replay.py scripts/train_parkour.py scripts/evaluate_model.py scripts/watch_model.py scripts/play_human.py scripts/play_replay.py scripts/run_experiment.py scripts/run_experiment_pair.py`
- `.venv\Scripts\python.exe -m pytest`

Run manual-play smoke only far enough to confirm startup/argument parsing if GUI automation is impractical:

- `.venv\Scripts\python.exe -m scripts.play_human --pressure-profile enemy_fire_slow_4x`

Run small training smokes:

- `.venv\Scripts\python.exe -m scripts.run_experiment --training-profile combat_bullets_v1 --control-mode movement_scripted_attack_direct --reward-profile defense_v1 --pressure-profile enemy_fire_slow_4x --total-timesteps 1000 --n-envs 1 --vec-env dummy --wandb off --train-eval off --eval-episodes 1 --save-replays --timing-profile on --torch-num-threads 2 --net-arch 128,128`

- `.venv\Scripts\python.exe -m scripts.run_experiment --training-profile combat_bullets_v1 --control-mode movement_scripted_attack_direct --reward-profile defense_v1 --pressure-profile normal --total-timesteps 1000 --n-envs 1 --vec-env dummy --wandb off --train-eval off --eval-episodes 1 --save-replays --timing-profile on --torch-num-threads 2 --net-arch 128,128`

Verify that slow-fire produces fewer enemy bullets spawned over comparable episodes, while bullet speed/damage remain unchanged.

Then run first curriculum comparison, not 500k:

- `.venv\Scripts\python.exe -m scripts.run_experiment_pair --mode parallel --profile-a combat_bullets_v1 --profile-b combat_bullets_v1 --control-mode-a movement_no_boost_scripted_attack_direct --control-mode-b movement_scripted_attack_direct --reward-profile-a defense_v1 --reward-profile-b defense_v1 --pressure-profile-a enemy_fire_slow_4x --pressure-profile-b enemy_fire_slow_4x --label-a M0_defense_slow4 --label-b M1_defense_slow4 --total-timesteps 100000 --n-envs 4 --vec-env dummy --wandb off --train-eval on --eval-freq-timesteps 50000 --train-eval-episodes 2 --eval-episodes 5 --save-replays --net-arch 128,128 --threads-per-job 6 --timing-profile on --seed 0 --seed-b 0`

## Inspect after 100k

Report for M0 and M1:

- reward;
- Heli kills;
- player damage;
- death rate;
- visible bullet hit rate;
- enemy bullets spawned;
- enemy visible bullet pressure;
- time to first damage;
- longest damage-free streak;
- damage-free episode rate;
- player x range;
- left/right edge fractions;
- max consecutive edge frames;
- actual horizontal movement fractions;
- input-motion mismatch rate;
- boost pressed / ready / activations;
- pressure profile;
- replay commands.

## Acceptance criteria

Complete only if:

- `normal` preserves current behavior.
- Slow-fire profiles reduce enemy firing frequency only.
- Bullet speed/damage/collision remain unchanged.
- `play_human` can run with pressure profiles.
- `watch_model` and `play_replay` handle pressure profile correctly.
- Replay verification remains deterministic.
- Reports and comparison graphs label pressure profile clearly.
- Reward profile reporting gap is fixed.
- 100k M0/M1 slow4 comparison completes.
- No default simulator/reward/observation/action-space behavior changes.

## Stop conditions

Stop and report if:

- enemy fire cadence cannot be changed without touching unrelated Heli behavior;
- replay verification becomes ambiguous;
- pressure profile is not recoverable from old replays/configs;
- play_human/watch_model/play_replay need a broader refactor;
- slow-fire changes bullet speed, damage, or collision behavior;
- tests become slow or flaky.

## Required log update

Update:

- `docs/ai/CURRENT_STATE.md`
- `docs/ai/VALIDATION.md`
- `docs/ai/CODEX_SESSION_LOG.md`

Include:

- files changed;
- commands run;
- pass/fail result;
- proof of enemy fire-rate reduction;
- proof bullet speed/damage unchanged;
- smoke experiment paths;
- 100k pair path;
- key metrics table;
- replay/watch/play_human commands;
- remaining risks;
- suggested next step.