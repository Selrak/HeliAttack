# NEXT_CODEX_TASK.md

## Goal

Implement and test the first defensive curriculum reward profile:

- `M0_defense`: no boost, scripted direct attack, defensive reward.
- `M1_defense`: boost allowed, scripted direct attack, defensive reward.

The goal is to make bullet avoidance matter much more than merely surviving long enough to kill Helis.

## Non-goals

Do not change HA2 mechanics, physics, bullets, Heli logic, observations, action spaces, replay determinism, or existing default rewards.

Do not remove boost.

Do not add new observation fields yet.

Do not run 500k yet.

## Context

Current M0/M1 curriculum works mechanically:

- M0 uses `movement_no_boost_scripted_attack_direct`.
- M1 uses `movement_scripted_attack_direct`.
- Both use `combat_bullets_v1`, which already exposes visible enemy bullet relative positions and bullet velocity fields.

Current problem:

- M0 tends to camp/stall and die.
- M1 performs much better, but mainly through boost-heavy survival.
- We need a reward profile that strongly rewards not taking damage while still requiring offensive progress, without rewarding passive hiding/camping.

## Implementation

Add a new opt-in reward profile:

- `combat_default`: current reward, default, unchanged.
- `defense_v1`: new curriculum reward.

Add `reward_profile` to `HeliAttack2Env`, config, summaries, eval reports, replays if practical, and CLIs:

- `scripts.train_parkour`
- `scripts.run_experiment`
- `scripts.run_experiment_pair`
- `scripts.evaluate_model`
- `scripts.watch_model`

Evaluation/watch should infer `reward_profile` from `config.json` when given an experiment.

## Suggested `defense_v1` reward

Keep exact constants easy to find in code.

Initial proposal:

- living: `0.0`
- enemy damage: `0.03 * score_delta`
- Heli kill: `3.0 * killed_helis`
- player damage: `-1.0 * player_damage`
  - so one 10-damage bullet costs `-10`
- terminal death/fall: `-50.0`
- mild edge/input inefficiency penalty:
  - small penalty when pressing into a physical edge/wall without actual horizontal movement;
  - small penalty for prolonged edge camping;
  - do not over-penalize brief tactical edge contact.

Expose all terms in `reward_breakdown`.

Do not penalize boost, jump, or duck directly.

## Anti-camping scope

Use existing/new diagnostics only.

For now, penalize:

- prolonged left/right edge camping;
- repeated horizontal input with no actual horizontal movement.

Do not attempt full line-of-sight or “hiding behind scenery” detection yet unless it is trivial and robust.

The reward must still require offensive progress through enemy damage/kills, so passive hiding with no hits should not be attractive.

## Pair runner support

Add:

- `--reward-profile`
- `--reward-profile-a`
- `--reward-profile-b`

to `scripts.run_experiment_pair.py`.

Common `--reward-profile` should apply to both jobs unless overridden.

## Tests

Add tests for:

- default reward unchanged for `combat_default`;
- `defense_v1` applies much stronger player-damage penalty;
- `reward_profile` is stored in `config.json`;
- `evaluate_model` reports `reward_profile`;
- `run_experiment_pair` forwards A/B reward profiles correctly;
- M0 still produces no boost with `defense_v1`;
- M1 still allows boost with `defense_v1`;
- reward breakdown contains all `defense_v1` terms.

Keep tests short.

## Validation

Run:

- `.venv\Scripts\python.exe -m py_compile ha2_env.py scripts/train_parkour.py scripts/evaluate_model.py scripts/run_experiment.py scripts/run_experiment_pair.py scripts/watch_model.py`
- `.venv\Scripts\python.exe -m pytest`

Run quick smokes:

- `.venv\Scripts\python.exe -m scripts.run_experiment --training-profile combat_bullets_v1 --control-mode movement_no_boost_scripted_attack_direct --reward-profile defense_v1 --total-timesteps 1000 --n-envs 1 --vec-env dummy --wandb off --train-eval off --eval-episodes 1 --save-replays --timing-profile on --torch-num-threads 2 --net-arch 128,128`

- `.venv\Scripts\python.exe -m scripts.run_experiment --training-profile combat_bullets_v1 --control-mode movement_scripted_attack_direct --reward-profile defense_v1 --total-timesteps 1000 --n-envs 1 --vec-env dummy --wandb off --train-eval off --eval-episodes 1 --save-replays --timing-profile on --torch-num-threads 2 --net-arch 128,128`

Then run the first real comparison:

- `.venv\Scripts\python.exe -m scripts.run_experiment_pair --mode parallel --profile-a combat_bullets_v1 --profile-b combat_bullets_v1 --control-mode-a movement_no_boost_scripted_attack_direct --control-mode-b movement_scripted_attack_direct --reward-profile-a defense_v1 --reward-profile-b defense_v1 --label-a M0_defense --label-b M1_defense --total-timesteps 100000 --n-envs 4 --vec-env dummy --wandb off --train-eval on --eval-freq-timesteps 50000 --train-eval-episodes 2 --eval-episodes 5 --save-replays --net-arch 128,128 --threads-per-job 6 --timing-profile on --seed 0 --seed-b 0`

## Inspect after 100k

Report for M0_defense and M1_defense:

- reward;
- Heli kills;
- player damage;
- death rate;
- visible bullet hit rate;
- time to first damage;
- longest damage-free streak;
- damage-free episode rate;
- player x range;
- left/right edge fractions;
- max consecutive edge frames;
- actual horizontal movement fractions;
- input-motion mismatch rate;
- boost pressed / ready / activations;
- replay commands.

## Acceptance criteria

Complete only if:

- `combat_default` reward is unchanged;
- `defense_v1` is opt-in and recorded everywhere;
- M0_defense and M1_defense train/evaluate successfully;
- M0_defense still has no boost in replay actions;
- M1_defense still allows boost;
- reports expose `reward_breakdown` and `reward_profile`;
- 100k comparison completes;
- diagnostic bundles include reports/replays/timing;
- no simulator mechanics or observations are changed.

## Stop conditions

Stop and report if:

- reward-profile plumbing would require changing core mechanics;
- old experiments cannot be evaluated because of missing `reward_profile`;
- M0 produces any boost action;
- defense reward creates obvious passive no-attack behavior in smoke replays;
- replay verification breaks;
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
- smoke experiment paths;
- 100k pair path;
- key M0_defense/M1_defense metrics;
- replay commands;
- remaining risks;
- suggested next step.