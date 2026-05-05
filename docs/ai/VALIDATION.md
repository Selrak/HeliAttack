# Validation

Run from repo root after installing `requirements.txt`:

```powershell
python -m py_compile ha2_env.py ha2_replay.py extract_ha2_data.py ha2_constants.py
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
python -m scripts.train_parkour --total-timesteps 1000 --n-envs 1 --wandb off
python -m scripts.evaluate_model --episodes 1
```

Current Heli damage check: `reports/parity_traces/heli_shoots_hero_240_summary.txt` should show `initial_player_health=100`, `final_player_health=90`, `enemy_bullet_hits=1`, and `first_enemy_damage_frame=240`.
Current Heli respawn check: `reports/parity_traces/kill_heli_respawn_600_summary.txt` should show non-empty `killed_enemy_ids`, a non-`None` `replacement_heli_spawn_frame`, and `active_enemies=1`.
Manual healthbar check: in `heli_shoots_hero_240`, the original red healthbar at the top-right should shrink after player damage.

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
python -m scripts.watch_model
```

Local environment:
- `.venv` exists and has pytest/SB3 installed as of 2026-05-04.
- Use `.\.venv\Scripts\Activate.ps1` before running commands interactively.

Final reports should stay concise: files changed, validation run, pass/fail, manual checks, blockers, risks, next step.
