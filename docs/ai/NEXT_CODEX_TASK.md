# NEXT_CODEX_TASK.md

## Goal

Harmonize HA2 GUI/viewer behavior across `scripts/play_human.py`, `scripts/watch_model.py`, and `scripts/play_replay.py`.

## Requirements

- Introduce required shared GUI helper code in `ha2_gui.py`.
- Use shared code for common GUI keys, speed factors, pause/single-step state, terminal hold/restart policy, post-player-death visual slow-motion, and GUI sound setup/update/shutdown.
- Keep mode-specific code limited to manual input, model action selection, or replay action playback.
- Common keys: `Esc` quit, `Enter`/`R` restart from terminal state, `F` speed up, `Shift+F` speed down, `1` reset speed, `P`/`Space` pause, `N` single-step, `F1` debug, `F3` collision overlay where applicable.
- Common speed factors: `0.25x`, `0.5x`, `1x`, `2x`, `4x`, `8x`.
- Compose user GUI speed and gameover slowdown multiplicatively during player-death terminal presentation.
- Do not call normal `env.step()` after terminal `player_death`; advance only render-only visual effects.
- Keep HUD drawing centralized in `ha2_env.render()`.
- Keep sound GUI-only. Do not move mixer/channel/loop state into `ha2_env.py`, `evaluate_model.py`, training, or headless paths.
- Diagnose/repair `sheli` through GUI loop code and tests.
- Do not modify `ha2_env_legacy.py`.
- Do not run training.

## Validation

```powershell
python -m py_compile ha2_gui.py ha2_env.py ha2_replay.py ha2_sound.py scripts/play_human.py scripts/play_replay.py scripts/watch_model.py scripts/evaluate_model.py
python -m pytest tests/test_env_basic.py
python -m pytest tests/test_replay_metadata.py
python -m pytest
```

Use the project virtual environment if system Python lacks test dependencies.
