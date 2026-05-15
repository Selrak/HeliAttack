# Validation

Run from repo root after installing `requirements.txt`:

```powershell
python -m py_compile ha2_env.py ha2_replay.py extract_ha2_data.py ha2_constants.py
python -m py_compile scripts/experiment_utils.py scripts/train_parkour.py scripts/evaluate_model.py scripts/watch_model.py scripts/run_experiment.py scripts/benchmark_vec_envs.py
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
python -m scripts.run_experiment --training-profile combat_bullets_v1 --total-timesteps 1000 --n-envs 1 --vec-env dummy --wandb off --train-eval off --eval-episodes 1 --save-replays --timing-profile on --torch-num-threads 2 --net-arch 128,128
python -m scripts.run_experiment_pair --mode parallel --profile-a combat_v1 --profile-b combat_bullets_v1 --total-timesteps 1000 --n-envs 1 --vec-env dummy --wandb off --train-eval off --eval-episodes 1 --save-replays --timing-profile on --threads-per-job 2 --net-arch 128,128 --stagger-seconds 0
python -m scripts.train_parkour --total-timesteps 1024 --n-envs 1 --vec-env dummy --train-eval off --wandb off
python -m scripts.train_parkour --total-timesteps 1024 --n-envs 2 --vec-env subproc --eval-vec-env same --train-eval on --train-eval-episodes 1 --wandb off
python -m scripts.benchmark_vec_envs --mode train-only --total-timesteps 2048 --repeats 1 --vec-envs dummy subproc --n-envs 1 2 --wandb off --device cpu
python -m scripts.benchmark_vec_envs --mode workflow --total-timesteps 2048 --repeats 1 --vec-envs dummy subproc --n-envs 1 2 --eval-vec-env same --wandb off --device cpu
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
- `experiments/<created_experiment>/reports/timing/train_timing.json` and `.md`
- `experiments/<created_experiment>/reports/timing/orchestration_timing.json` and `.md`
- `experiments/<created_experiment>/replays/latest_eval_ep0.jsonl`
- `experiments/<created_experiment>/replays/best_eval_ep0.jsonl`
- `experiments/<created_experiment>/tensorboard/`
- `experiments/<created_experiment>/<created_experiment>_diagnostic_bundle.zip`

Manual GUI checks:

```powershell
python -m scripts.play_human
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
