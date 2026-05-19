# Validation

Run from repo root after installing `requirements.txt`. Use the project venv (`.venv`) if the system Python does not have pytest/SB3:

```powershell
python -m py_compile ha2_env.py ha2_replay.py extract_ha2_data.py ha2_constants.py
python -m py_compile scripts/runtime_config.py scripts/experiment_utils.py scripts/invocation_metadata.py scripts/train_parkour.py scripts/evaluate_model.py scripts/evaluate_matrix.py scripts/watch_model.py scripts/play_human.py scripts/play_replay.py scripts/run_experiment.py scripts/run_experiment_pair.py scripts/benchmark_vec_envs.py
python -m pytest
python -m scripts.record_random_replay --steps 300 --out replays/smoke.jsonl
python -m scripts.verify_replay replays/smoke.jsonl
python -m scripts.record_scripted_trace --scenario all
python -m scripts.verify_replay reports/parity_traces/walk_right_120.jsonl
python -m scripts.record_scripted_trace --scenario fire_right_60
python -m scripts.verify_replay reports/parity_traces/fire_right_60.jsonl
python -m scripts.record_scripted_trace --scenario fire_at_heli_180
python -m scripts.verify_replay reports/parity_traces/fire_at_heli_180.jsonl
python -m scripts.record_scripted_trace --scenario heli_shoots_hero_240
python -m scripts.verify_replay reports/parity_traces/heli_shoots_hero_240.jsonl
python -m scripts.record_scripted_trace --scenario kill_heli_respawn_600
python -m scripts.verify_replay reports/parity_traces/kill_heli_respawn_600.jsonl
python -c "from stable_baselines3.common.env_checker import check_env; from ha2_env import HeliAttack2Env; env=HeliAttack2Env(render_mode=None, training_profile='combat_v1', max_episode_steps=300); check_env(env, warn=True); env.close(); print('check_env passed')"
python -m scripts.run_experiment --training-profile combat_bullets_v1 --total-timesteps 1000 --n-envs 1 --vec-env dummy --wandb off --train-eval off --eval-episodes 1 --save-replays --timing-profile on --torch-num-threads 2 --net-arch 128,128 --eval-freq-timesteps 500
python -m scripts.run_experiment_pair --mode parallel --profile-a combat_v1 --profile-b combat_bullets_v1 --total-timesteps 1000 --n-envs 1 --vec-env dummy --wandb off --train-eval off --eval-episodes 1 --save-replays --timing-profile on --threads-per-job 2 --net-arch 128,128 --stagger-seconds 0 --seed 0 --seed-b 0 --eval-freq-timesteps 500
python -m scripts.run_experiment_pair --mode parallel --profile-a combat_bullets_v1 --profile-b combat_bullets_v1 --control-mode-a movement_no_boost_scripted_attack_direct --control-mode-b movement_scripted_attack_direct --label-a M0_no_boost --label-b M1_boost --total-timesteps 100000 --n-envs 4 --vec-env dummy --wandb off --train-eval on --eval-freq-timesteps 50000 --train-eval-episodes 2 --eval-episodes 5 --save-replays --net-arch 128,128 --threads-per-job 6 --timing-profile on --seed 0 --seed-b 0
python -m scripts.run_experiment --training-profile combat_bullets_v1 --control-mode movement_scripted_attack_direct --reward-profile defense_v1 --pressure-profile enemy_fire_slow_4x --total-timesteps 1000 --n-envs 1 --vec-env dummy --wandb off --train-eval off --eval-episodes 1 --save-replays --timing-profile on --torch-num-threads 2 --net-arch 128,128
python -m scripts.run_experiment_pair --mode parallel --profile-a combat_bullets_v1 --profile-b combat_bullets_v1 --control-mode-a movement_no_boost_scripted_attack_direct --control-mode-b movement_scripted_attack_direct --reward-profile-a defense_v1 --reward-profile-b defense_v1 --pressure-profile-a enemy_fire_slow_4x --pressure-profile-b enemy_fire_slow_4x --label-a M0_defense_slow4 --label-b M1_defense_slow4 --total-timesteps 100000 --n-envs 4 --vec-env dummy --wandb off --train-eval on --eval-freq-timesteps 50000 --train-eval-episodes 2 --eval-episodes 5 --save-replays --net-arch 128,128 --threads-per-job 6 --timing-profile on --seed 0 --seed-b 0
python -m scripts.run_experiment --training-profile combat_bullets_v1 --control-mode movement_no_boost_scripted_attack_direct --reward-profile defense_v1 --pressure-profile enemy_fire_slow_2x --resume-from experiments/<parent_experiment>/models/latest.zip --total-timesteps 1024 --n-envs 1 --vec-env dummy --wandb off --train-eval off --eval-episodes 1 --timing-profile on
python -m scripts.train_parkour --total-timesteps 1024 --n-envs 1 --vec-env dummy --train-eval off --wandb off
python -m scripts.train_parkour --total-timesteps 1024 --n-envs 2 --vec-env subproc --eval-vec-env same --train-eval on --train-eval-episodes 1 --wandb off
python -m scripts.benchmark_vec_envs --mode train-only --total-timesteps 2048 --repeats 1 --vec-envs dummy subproc --n-envs 1 2 --wandb off --device cpu
python -m scripts.benchmark_vec_envs --mode workflow --total-timesteps 2048 --repeats 1 --vec-envs dummy subproc --n-envs 1 2 --eval-vec-env same --wandb off --device cpu
python -m scripts.evaluate_matrix --matrix-name smoke_matrix --entry "label=M0;experiment=experiments/<m0_experiment>;model=latest" --entry "label=M1;experiment=experiments/<m1_experiment>;model=best" --pressure-profiles enemy_fire_slow_4x,enemy_fire_slow_2x,normal --episodes 1 --max-episode-steps 200 --max-parallel 2 --threads-per-job 1 --dry-run
python -m scripts.evaluate_matrix --matrix-name damage_forensics_smoke --entry "label=M1;experiment=experiments/<m1_experiment>;model=latest" --pressure-profiles normal --episodes 1 --max-episode-steps 600 --max-parallel 1 --threads-per-job 1 --no-save-replays --damage-forensics --damage-forensics-window 60
python -m scripts.run_experiment --training-profile combat_bullets_v1 --control-mode movement_scripted_attack_direct --reward-profile defense_v1 --pressure-profile normal --total-timesteps 1024 --n-envs 1 --vec-env dummy --wandb off --train-eval off --eval-episodes 1 --max-episode-steps 200 --timing-profile on --label invocation_smoke_label_alias
```

Current Heli damage check: `reports/parity_traces/heli_shoots_hero_240_summary.txt` should show `initial_player_health=100`, `final_player_health=90`, `enemy_bullet_hits=1`, and `first_enemy_damage_frame=240`.
Current Heli respawn check: `reports/parity_traces/kill_heli_respawn_600_summary.txt` should show non-empty `killed_enemy_ids`, a non-`None` `replacement_heli_spawn_frame`, and `active_enemies=1`.
Manual healthbar check: in `heli_shoots_hero_240`, the original red healthbar at the top-right should shrink after player damage.

Experiment smoke output:
- `experiments/<created_experiment>/config.json`
- `experiments/<created_experiment>/git_info.txt`
- `experiments/<created_experiment>/summary.md`
- `experiments/<created_experiment>/models/latest.zip`
- `experiments/<created_experiment>/models/best.zip` if SB3 produced one
- `experiments/<created_experiment>/models/checkpoints/`
- `experiments/<created_experiment>/reports/eval_latest.json`
- `experiments/<created_experiment>/reports/eval_best.json`
- Evaluation reports should include visible enemy-bullet metrics, damage timing metrics, and defensive rates.
- Evaluation reports should include top-level `reward_profile`, `pressure_profile`, and aggregated `reward_breakdown`; replay headers should include `reward_profile` and `pressure_profile`, and replay step debug should include `reward_breakdown`.
- Optional damage forensics evals should write `damage_forensics_*.json` and `.md`; matrix jobs should copy them to `jobs/<eval_id>/damage_forensics.json` and `.md`.
- Resumed experiment configs should include `resume_from`, `parent_experiment_dir`, parent runtime profiles, `reset_num_timesteps`, and `fine_tune_timesteps`. By default, resumed runs should not reset SB3 timestep numbering.
- Curriculum reports should include `policy_action_space_nvec`, `sim_action_space_nvec`, `policy_action_distributions`, and `full_action_distributions`.
- M0 (`movement_no_boost_scripted_attack_direct`) replay `action` values should be full 6D simulator actions with `action[3] == 0` for every step.
- `experiments/<created_experiment>/reports/timing/train_timing.json` and `.md`
- `experiments/<created_experiment>/reports/timing/orchestration_timing.json` and `.md`
- `experiments/<created_experiment>/replays/latest_eval_ep0.jsonl`
- `experiments/<created_experiment>/replays/best_eval_ep0.jsonl`
- `experiments/<created_experiment>/tensorboard/`
- `experiments/<created_experiment>/<created_experiment>_diagnostic_bundle.zip`
- `experiments/<created_experiment>/argv.json`
- `experiments/<created_experiment>/command.txt`
- `experiments/<created_experiment>/resolved_config.json`
- `experiments/<created_experiment>/invocation_metadata.json`
- Orchestrated runs also include child metadata such as `train_argv.json`, `train_command.txt`, and `eval_latest_command.txt`.

Manual GUI checks:

```powershell
python -m scripts.play_human
python -m scripts.play_human --pressure-profile enemy_fire_slow_4x
python -m scripts.play_replay replays/smoke.jsonl
python -m scripts.play_replay reports/parity_traces/walk_right_120.jsonl
python -m scripts.play_replay reports/parity_traces/fire_right_60.jsonl
python -m scripts.play_replay reports/parity_traces/fire_at_heli_180.jsonl
python -m scripts.play_replay reports/parity_traces/heli_shoots_hero_240.jsonl
python -m scripts.play_replay reports/parity_traces/kill_heli_respawn_600.jsonl
```

Optional GUI/model watch after SB3 smoke creates a model:

```powershell
python -m scripts.watch_model --experiment experiments/<created_experiment> --model-choice latest
```

Local environment:
- `.venv` exists and has pytest/SB3 installed as of 2026-05-04.
- Use `.\.venv\Scripts\Activate.ps1` before running commands interactively.

`scripts.run_experiment.py` is the canonical local training entry point.
Vector-env benchmark reports are written to ignored files under `reports/vec_env_benchmarks/`.

Final reports should stay concise: files changed, validation run, pass/fail, manual checks, blockers, risks, next step.

Current fast-path note: the full pytest suite runs in about 36 seconds locally after trimming a few duplicate/expensive smoke checks.

Watch/evaluate note: `scripts.watch_model` and `scripts.evaluate_model` can now infer experiment config from `experiments/.../models/*.zip` when `--experiment` is omitted, so direct model-path runs should not need extra runtime flags if the model stays inside its experiment folder.

Watch-model note: wrapper-based control modes render through `env.unwrapped`, so custom GUI render kwargs should now work for experiment models that use scripted control wrappers.

Count-format note: step/timestep CLI arguments now accept `500_000`, `500k`, `1_000_000`, and `1M` where those arguments are wired through the shared human-count parser.

Evaluation matrix note: `scripts.evaluate_matrix` writes self-contained matrix outputs and bundles under `experiments/eval_matrices/`.
