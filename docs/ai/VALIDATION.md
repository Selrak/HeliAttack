# Validation

Run from repo root after installing `requirements.txt`:

```powershell
python -m py_compile ha2_env.py ha2_replay.py extract_ha2_data.py ha2_constants.py
python -m pytest
python -m scripts.record_random_replay --steps 300 --out replays/smoke.jsonl
python -m scripts.verify_replay replays/smoke.jsonl
python -m scripts.record_scripted_trace --scenario all
python -m scripts.verify_replay reports/parity_traces/walk_right_120.jsonl
```

Manual GUI checks:

```powershell
python -m scripts.play_human
python -m scripts.play_replay replays/smoke.jsonl
python -m scripts.play_replay reports/parity_traces/walk_right_120.jsonl
```

Optional SB3 smoke after installing training dependencies:

```powershell
python -m scripts.train_parkour --total-timesteps 1000 --n-envs 1 --wandb off
python -m scripts.evaluate_model --episodes 3
python -m scripts.watch_model
```

Local environment:
- `.venv` exists and has pytest/SB3 installed as of 2026-05-04.
- Use `.\.venv\Scripts\Activate.ps1` before running commands interactively.

Final reports should stay concise: files changed, validation run, pass/fail, manual checks, blockers, risks, next step.
