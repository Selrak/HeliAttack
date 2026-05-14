# Codex Session Log

Append every non-trivial Codex implementation/testing session here. Keep entries factual and include validation status.

## 2026-05-03 23:23 Europe/Paris - Phase 0 AI Handoff Bootstrap

### Task Attempted
Created a lightweight AI handoff system for repeated ChatGPT webchat planning and Codex CLI implementation/testing loops.

### Files Created or Updated
- Updated `AGENTS.md`.
- Created `docs/ai/PROJECT_CONTEXT.md`.
- Created `docs/ai/CURRENT_STATE.md`.
- Created `docs/ai/ARCHITECTURE_DECISIONS.md`.
- Created `docs/ai/CODEX_SESSION_LOG.md`.
- Created `docs/ai/NEXT_CODEX_TASK.md`.
- Created `docs/ai/VALIDATION.md`.

### Repository Facts Discovered
- This is a Python 3.11 project.
- Current runtime is centered on `ha2_env.py`, a Gymnasium/Pygame HA2 environment.
- `extract_ha2_data.py` regenerates map/constants data from decompiled HA2 ActionScript.
- `ha2_constants.py` is generated and contains `FULL_MAP_DATA`.
- `heliattack2_scripts/` contains decompiled HA2 AS reference files.
- `heliattack_repo/ha2/assets/` contains original HA2 assets.
- No formal test suite, dependency manifest, or training script was found during bootstrap.
- Prior summaries mention intended SB3/W&B/training architecture, but those components were not verified as current implementation.

### Commands Run
- `Get-ChildItem -Force`
- `if (Test-Path AGENTS.md) { Get-Content -Raw AGENTS.md }`
- `if (Get-Command rg -ErrorAction SilentlyContinue) { rg --files } else { Get-ChildItem -Recurse -File | Select-Object -ExpandProperty FullName }`
- `git status --short`
- `Get-Content -Path ha2_env.py -TotalCount 260`
- `Get-Content -Path extract_ha2_data.py -TotalCount 220`
- `Get-Content -Path ha2_constants.py -TotalCount 220`
- `if (Test-Path docs\ai) { Get-ChildItem -Force docs\ai } else { Write-Output 'docs/ai does not exist' }`
- `$lines = Get-Content ha2_env.py; for ($i=261; $i -le $lines.Length; $i++) { '{0,4}: {1}' -f $i, $lines[$i-1] }`
- `if (Get-Command rg -ErrorAction SilentlyContinue) { rg -n "pytest|unittest|ruff|mypy|gymnasium|pygame|stable_baselines|requirements|pyproject|setup|if __name__|argparse|--record" -S . } else { Select-String -Path * -Pattern "pytest|unittest|ruff|mypy|gymnasium|pygame|stable_baselines|requirements|pyproject|setup|if __name__|argparse|--record" -CaseSensitive:$false }`
- `Get-ChildItem -Force heliattack_repo; Get-ChildItem -Force heliattack_repo\ha2`
- `Get-Date -Format o`
- `Get-Content -Raw Summary_1.md`
- `Get-Content -Raw Summary_2.md`
- `Get-Content -Raw OLD_chatGPT_project_instructions.txt`
- `python --version`
- `python -m py_compile ha2_env.py extract_ha2_data.py ha2_constants.py`
- `python -c "from ha2_env import HeliAttack2Env; env=HeliAttack2Env(render_mode=None); obs,_=env.reset(); print(obs.tolist()); print(env.step([1,0,0,0])[:4]); env.close()"`
- `Get-ChildItem -Force -Name pyproject.toml,requirements.txt,setup.py,setup.cfg,tox.ini,pytest.ini,.pre-commit-config.yaml 2>$null`
- `git rev-parse --show-toplevel`
- `Get-ChildItem -Force docs\ai`
- `git diff -- AGENTS.md docs/ai/PROJECT_CONTEXT.md docs/ai/CURRENT_STATE.md docs/ai/ARCHITECTURE_DECISIONS.md docs/ai/CODEX_SESSION_LOG.md docs/ai/NEXT_CODEX_TASK.md docs/ai/VALIDATION.md`
- `git status --short AGENTS.md docs/ai`

### Validation Result
- Passed: Python version command returned `Python 3.11.9`.
- Passed: `python -m py_compile ha2_env.py extract_ha2_data.py ha2_constants.py`.
- Passed: headless environment import/reset/step smoke test returned initial observation `[25.0, -50.0, 0.0, 0.0]` and first-step observation `[25.0, -49.0, 0.0, 1.0]` with reward `0.1`.
- Passed: post-write file existence check showed all requested `docs/ai` files.
- Note: `git diff -- ...` showed no content because the handoff files are untracked; `git status --short AGENTS.md docs/ai` showed `?? AGENTS.md` and `?? docs/ai/`.
- Not run: GUI play loop and GIF recording.

### Bugs or Blockers Encountered
- None during documentation bootstrap.

### Fixes or Workarounds Applied
- None; no simulator code was changed.

### Architectural Discrepancies Discovered
- Existing summaries describe SB3/W&B/training/checkpointing/threaded recording components that were not found in current repository files.
- Existing code uses absolute Windows paths, which conflicts with future cross-platform goals.

### Remaining Risks
- No automated parity tests exist.
- No dependency manifest exists.
- GUI and GIF workflows still need manual verification.
- Worktree contains pre-existing modified/untracked files, so future sessions must avoid reverting unrelated changes.

### Recommended Next Action
Have ChatGPT webchat produce a concrete implementation phase and paste it into `docs/ai/NEXT_CODEX_TASK.md`, then ask Codex CLI to implement only that task.

## 2026-05-03 23:34 Europe/Paris - Handoff Behavior Update

- Updated `AGENTS.md`, `docs/ai/VALIDATION.md`, and `docs/ai/CURRENT_STATE.md`.
- Added rule: ask clarification questions instead of making hypotheses when requirements are unclear.
- Added rule: keep `docs/ai` updates and session reports concise.
- Validation: documentation-only change; no simulator validation run.

## 2026-05-03 23:46 Europe/Paris - Simulator Run/Test/Replay Foundation

- Task: add project hygiene, repo-relative paths, playable GUI script, deterministic replay scripts, pytest tests, parity notes, and minimal SB3 entry points.
- Changed: `ha2_env.py`, `extract_ha2_data.py`, `ha2_replay.py`, `scripts/`, `tests/`, `.gitignore`, `requirements.txt`, `docs/parity_notes.md`, `models/.gitkeep`, `reports/.gitkeep`, and handoff docs.
- Passed: py_compile; headless reset/step; rgb_array smoke; random replay record/verify; manual equivalent of pytest assertions; speed smoke about 44,982 steps/sec.
- Blocked: `python -m pytest` missing `pytest`; SB3 train/evaluate missing `stable-baselines3`.
- Not run: GUI `play_human`, GUI `play_replay`, `watch_model`.
- Risks: tile mapping approximate; AS case-sensitive variable names still need parity verification.
- Next: install requirements, run pytest, manually test `python -m scripts.play_human`, then decide first golden traces.

## 2026-05-04 00:03 Europe/Paris - Screenshot Hotkey

- Added `F12` in `scripts/play_human.py` to save incrementing PNG screenshots under `recordings/` by default.
- Added `--screenshot-dir` to override the target directory.
- Validation: docs-only update here; screenshot path not manually clicked in the GUI yet.

## 2026-05-04 00:25 Europe/Paris - FFDEC Asset Rendering

- Switched renderer to `assets_ffdec`.
- Fixed tile frame selection to AS mapping `graphic_idx + 1` and tile draw offset `-1`.
- Cleared spawn marker `32` at runtime to match AS map setup.
- Changed default screenshot directory to `screenshots/`.
- Passed: py_compile, pytest, rgb_array smoke PNG generation, replay record/verify.
- Remaining risk: player sprite registration still needs visual comparison against Flash.

## 2026-05-04 00:34 Europe/Paris - Player Bitmap Render Fix

- Switched player rendering from black FFDEC composite sprite PNGs to colored `assets_ffdec/images` player bitmap exports.
- Hid collision boxes by default; `F3` toggles hitbox/logical-box overlay in `play_human`.
- Remaining risk: exact player bitmap registration against Flash still needs visual comparison.

## 2026-05-04 00:44 Europe/Paris - Player Direction And Walk Frames

- Removed Python-side horizontal mirroring for the player body; inspected AS did not show a hero body `_xscale` flip.
- Added walking animation alternating `assets_ffdec/images/126.png` and `128.png`.
- Remaining risk: exact Flash nested-walk-frame cadence still needs verification.

## 2026-05-04 10:30 Europe/Paris - Faster Play Human Startup

- Task: reduce `scripts.play_human` startup time.
- Changed: `ha2_env.py`, `scripts/play_human.py`, `docs/ai/CURRENT_STATE.md`, `docs/ai/CODEX_SESSION_LOG.md`.
- Fix: replaced broad `pygame.init()` with targeted display/font init; deferred `numpy` import in `play_human` until GIF recording is used.
- Result: startup profile to first render improved from about 9.29s to about 0.78s locally.
- Passed: `py_compile`, `pytest -q`, replay record/verify.
- Not run: manual GUI gameplay.

## 2026-05-04 10:57 Europe/Paris - Scripted Player Traces

- Task: add first HA2 player-parity validation layer; no combat/weapons.
- Changed: `.gitignore`, `scripts/record_scripted_trace.py`, `tests/test_scripted_trace.py`, `docs/parity_notes.md`, and handoff docs.
- Added deterministic traces for idle, walk right, jump hold, double jump, duck/stand, and hyperjump under `reports/parity_traces/`.
- Passed: `py_compile`, `pytest -q`, random replay record/verify, scripted trace generation, scripted `walk_right_120` verify.
- Not run: manual GUI play/replay checks.

## 2026-05-04 13:52 Europe/Paris - AS Player/Camera Parity Audit

- Task: audit Python player/camera/rendering behavior against HA2 AS; no combat/training scope.
- Inspected: `ha2_env.py`, replay/trace scripts, docs, and `frame_19_DoAction_2.as` blocks `drawMap`, `assignents`, `getWorldPos`, `scrollMap`, `heroSetup`, `heroStart`, `heroAction`, `hitCheck`, `startGame`, and main scroll/parallax update.
- Changed: `docs/parity_notes.md`, `docs/ai/CURRENT_STATE.md`, `docs/ai/CODEX_SESSION_LOG.md`, `docs/ai/VALIDATION.md`, `docs/ai/PROJECT_CONTEXT.md`.
- Python behavior changed: no.
- Validation passed: `py_compile`; `pytest -q`; random replay record/verify; scripted trace generation; scripted `walk_right_120` verify.
- Bugs/blockers: none.
- Discrepancy found: Python camera/parallax is stateless/centered, unlike AS threshold-driven `world._x/_y` plus `bglayer1` parallax.
- Remaining risks: AS casing quirk, player registration/nested walk cadence, edge `hitCheck` behavior, and camera parity need Flash/bytecode or focused implementation.
- Next: decide whether to implement AS-style stateful camera/parallax or proceed to basic gun task.

## 2026-05-04 14:30 Europe/Paris - Default MachineGun Slice

- Task: implement only the first HA2 default MachineGun/projectile slice.
- AS inspected: `frame_19_DoAction_2.as` blocks `bulletFrame`, `machineGun`, `addBullet`, `heroSetup`, mouse handlers, gun reload/fire logic, and `guns[0]`.
- Confirmed constants: MachineGun reload `5`, speed `8`, damage `10`, bullet frame `1`, spread `rot - 2 + random(4)`.
- Changed: `ha2_env.py`, `ha2_replay.py`, `scripts/play_human.py`, `scripts/record_scripted_trace.py`, `tests/`, `docs/parity_notes.md`, and handoff docs.
- Added: 6-field action support `[move,jump,duck,boost,aim_bin,fire]` with legacy 4-field compatibility, default gun state, env-local deterministic spread RNG, bullet state/hash/debug, bullet rendering from `assets_ffdec/images/35.png`, and `fire_right_60`.
- Validation passed with `.venv` Python: `py_compile`; `pytest` (`13 passed`); random replay record/verify; scripted trace all; `walk_right_120` verify; `fire_right_60` record/verify.
- Not run: manual GUI `play_human` and GUI `play_replay`.
- Approximations: gun/barrel registration uses a fixed player-relative offset; bullet active-region removal uses map bounds plus solid-tile collision instead of exact AS `worldpos/stw/sth`.
- Remaining risks: visual gun/bullet registration and AS camera-dependent removal need later Flash comparison or AS-style camera work.
- Next: Charles should manually test firing in `python -m scripts.play_human` and watch `reports/parity_traces/fire_right_60.jsonl`.

## 2026-05-04 14:44 Europe/Paris - Visible MachineGun Rendering

- Task: fix missing held-gun rendering in play/replay.
- Changed: `ha2_env.py`, `docs/parity_notes.md`, `docs/ai/CURRENT_STATE.md`, `docs/ai/CODEX_SESSION_LOG.md`.
- Fix: render `assets_ffdec/sprites/DefineSprite_107/1.png` around the player gun pivot, rotate from recorded/live `gun_rotation`, and flip local y-scale when aiming left like AS.
- Validation passed: `py_compile`; `pytest` (`13 passed`); random replay record/verify; scripted trace all; `walk_right_120` verify; `fire_right_60` record/verify.
- Manual GUI not run by Codex. RGB trace screenshot showed the gun visible during `fire_right_60`.
- Remaining risk: exact Flash gun/barrel registration still needs comparison.

## 2026-05-04 15:19 Europe/Paris - FFDEC MachineGun Placement

- Task: replace approximate held-gun/barrel placement with Charles-provided FFDEC metadata.
- Changed: `ha2_env.py`, `tests/test_env_basic.py`, `docs/parity_notes.md`, `docs/ai/CURRENT_STATE.md`, `docs/ai/CODEX_SESSION_LOG.md`.
- Fix: added explicit hero gun `(24.0, 29.0)` and MachineGun barrel `(22.7, -7.4)` placement constants for visual gun rendering; bullet spawn logic was left unchanged per visual-only scope.
- Validation passed: `py_compile`; `pytest` (`14 passed`); `fire_right_60` record/verify; random replay record/verify.
- Manual GUI not run by Codex. RGB trace screenshot showed the gun using FFDEC placement; overlay shows visual barrel and unchanged spawn point.
- Remaining risk: visual parity still needs Charles/Flash comparison.

## 2026-05-04 16:01 Europe/Paris - FFDEC Reference Export Script

- Task: make `scripts/export_ffdec_reference.ps1` work with the local FFDEC install.
- Changed: `scripts/export_ffdec_reference.ps1`, `.gitignore`, `docs/ai/CURRENT_STATE.md`, `docs/ai/CODEX_SESSION_LOG.md`.
- Fix: auto-detect `C:\Program Files (x86)\FFDec\ffdec-cli.exe`, support explicit `-Ffdec`/`FFDEC_CLI`, and capture FFDEC stdout/stderr to logs without PowerShell treating Java stderr as failure.
- Validation passed: exported `D:\cthin\Downloads\heli-attack-2.swf` to `reference_exports/ffdec_ha2`.
- Output summary: SWF XML 1, scripts AS/pcode/hex 74 each, sprites PNG/SVG 614 each, shapes SVG 137, frames PNG 29, images 85, symbol class 1.
- Remaining risk: `reference_exports/` is ignored and should be regenerated locally when needed.

## 2026-05-04 16:10 Europe/Paris - Default Heli Target Slice

- Task: implement only the first AS-backed default Heli target slice from `NEXT_CODEX_TASK.md`.
- AS inspected: `frame_19_DoAction_2.as` blocks `bulletFrame`, `heroStart`, `heliFrame`, `addEnemy`, and `startGame`; FFDEC XML for `DefineSprite_111_Heli` and nested `hit`.
- Changed: `ha2_env.py`, `scripts/record_scripted_trace.py`, `tests/test_env_basic.py`, `tests/test_scripted_trace.py`, `docs/parity_notes.md`, `docs/ai/NEXT_CODEX_TASK.md`, and handoff docs.
- Added: reset-time deterministic Heli spawn, Heli health/movement/rendering, player MachineGun hit detection, score/hit/kill counters, enemy state/hash/debug fields, and `fire_at_heli_180`.
- Validation passed with `.venv` Python: `py_compile`; `pytest` (`19 passed`); random replay record/verify; scripted trace all; `walk_right_120`, `fire_right_60`, and `fire_at_heli_180` replay verify.
- Manual GUI not run by Codex.
- Deliberately omitted: enemy bullets, player damage, powerups, drops, pickups, weapon switching, explosions/shards/blood/sounds, and camera rewrite.
- Remaining risks: Heli spawn timing is reset-time instead of AS `heroStart`; Heli movement and hitbox are approximations until AS camera/start lifecycle and Flash `hitTest` parity are implemented.
- Next: Charles should manually check `python -m scripts.play_human` and `python -m scripts.play_replay reports/parity_traces/fire_at_heli_180.jsonl`.

## 2026-05-04 17:22 Europe/Paris - Heli Green Polygon Render Fix

- Task: fix visual-only Heli rendering issue where FFDEC Heli sprite export showed the hidden green `hit` child.
- Inspected: `ha2_env.py`, `DefineSprite_111_Heli` XML, `DefineSprite_109`/shape `108` hit metadata, and FFDEC bitmaps `77.png`/`78.png`.
- Changed: `ha2_env.py`, `tests/test_env_basic.py`, `docs/parity_notes.md`, and handoff docs.
- Fix: render Heli from visible body bitmap `images/78.png` plus pilot `images/77.png`; keep `Heli.hit` metadata for collision/debug only.
- Validation passed with `.venv` Python: `py_compile`; `pytest` (`20 passed`); random replay record/verify; `fire_at_heli_180` record/verify; scripted trace all; `walk_right_120` and `fire_right_60` verify.
- Manual GUI not run by Codex. RGB trace screenshot showed visible helicopter body instead of the green polygon.
- Remaining risk: nested Heli gun is not composed yet; exact Heli visual registration still needs Flash comparison.

## 2026-05-05 - First Heli Combat Loop

- Task: execute `NEXT_CODEX_TASK.md` for AS-backed Heli movement, nested gun, enemy bullets, player damage, and replay validation.
- AS/FFDEC inspected: `heliFrame`, `addEnemy`, `addEnemyBullet`, `enemyBulletFrame`, `bulletFrame`, `heroSetup`, `heroStart`, P-code `timeSetp`, `DefineSprite_111_Heli`, `DefineSprite_107`, and `DefineSprite_68_enemyBullet`.
- Changed: `ha2_env.py`, `scripts/record_scripted_trace.py`, `tests/test_env_basic.py`, `tests/test_scripted_trace.py`, `docs/parity_notes.md`, and handoff docs.
- Added: stateful `world_x/world_y/worldpos`, AS-style Heli movement/gun aiming/shoot cadence, nested Heli gun rendering, deterministic enemy bullets, player health damage, enemy-bullet replay state/hash, and `heli_shoots_hero_240`.
- Validation passed with `.venv` Python: `py_compile`; `pytest` (`26 passed`); random replay record/verify; scripted trace all; `walk_right_120`, `fire_right_60`, `fire_at_heli_180`, and `heli_shoots_hero_240` replay verify.
- Manual GUI not run by Codex. Charles previously reported the green-polygon visual fix looked OK.
- Approximations retained: reset-time Heli spawn instead of AS `heroStart`, rectangle player/Heli hit tests, no death drops/pickups/explosions/blood/sounds, and Python uses functional `timeStep`/lowercase `onscreen` despite AS decompile quirks.
- Remaining risk: exact Heli parity still needs Flash comparison for `heroStart`, `onScreen`/`onscreen`, and `timeSetp`.
- Next: Charles should manually run `play_human` and replay `reports/parity_traces/heli_shoots_hero_240.jsonl`.

## 2026-05-05 10:49 Europe/Paris - Heli Startup/Damage Fix

- Task: fix first Heli startup dart and make enemy bullet damage visible/reliable.
- Inspected: `ha2_env.py`, `scripts/record_scripted_trace.py`, tests, `docs/parity_notes.md`, AS `heroStart`, `addEnemy`, `heliFrame`, and `enemyBulletFrame`.
- Changed: `ha2_env.py`, `ha2_replay.py`, `scripts/record_scripted_trace.py`, `tests/`, `docs/parity_notes.md`, and handoff docs.
- Cause: reset-time Heli spawn let early targeting use the falling player's negative Y; damage existed mechanically but lacked clear trace/overlay reporting.
- Fix: default Heli now queues on reset and spawns after first ground contact using AS-style `addEnemy`; enemy damage frame/id/health are reported in debug, replay debug, and trace summaries.
- Validation passed: `py_compile`; `pytest` (`29 passed`); random replay record/verify; scripted trace all; `walk_right_120`, `fire_right_60`, `fire_at_heli_180`, and `heli_shoots_hero_240` verify.
- Manual GUI not run by Codex.
- Remaining risks: first-ground spawn is still a proxy for full AS `heroStart`; hit tests remain rectangles; death drops/effects remain omitted.
- Next: Charles should manually run `python -m scripts.play_human` and `python -m scripts.play_replay reports/parity_traces/heli_shoots_hero_240.jsonl`.

## 2026-05-05 11:08 Europe/Paris - Debug Side Panel

- Task: move GUI debug text out of the game area.
- Changed: `ha2_env.py`, `scripts/play_human.py`, `tests/test_env_basic.py`, and handoff docs.
- Fix: debug-enabled renders now create a right-side panel; the 450x320 game area remains unchanged. Mouse aim clamps to the playfield when the panel is visible.
- Validation passed: `py_compile`; `pytest` (`30 passed`).
- Manual GUI not run by Codex.
- Next: Charles should run `python -m scripts.play_human` and toggle `F1`.

## 2026-05-05 11:29 Europe/Paris - Continuous Heli Respawn

- Task: implement continuous default-Heli combat after Heli death.
- AS inspected: `heliFrame`, `addEnemy`, `bulletFrame`, `enemyBulletFrame`, HUD updates, and FFDEC HUD exports.
- Changed: `ha2_env.py`, `scripts/record_scripted_trace.py`, `tests/`, `docs/parity_notes.md`, and handoff docs.
- Implemented: dead Helis are removed, `helis/rthelis` increment once, replacements spawn with AS-style `addEnemy(300)`, env version `0.6`, and `kill_heli_respawn_600`.
- Omitted AS side effects: random weapon popup/reward, powerups/drops, shards, burned pilot, destroyed Heli, boom, bullet-time refill, blood, and sounds.
- HUD: no normal HUD added; original HUD asset/text/mask data were found but need a separate faithful composition pass. Debug panel now shows health, Heli health, score, hits, kills, and enemy events.
- Validation passed: `py_compile`; `pytest` (`34 passed`); random replay record/verify; scripted trace all; `walk_right_120`, `fire_right_60`, `fire_at_heli_180`, `heli_shoots_hero_240`, and `kill_heli_respawn_600` verify.
- Manual GUI not run by Codex.
- Remaining risks: exact HUD composition, Flash shape `hitTest`, AS `helis==3` powerup cycle, and full gameover remain unimplemented.
- Next: manually watch `kill_heli_respawn_600` and decide whether to implement faithful original HUD composition.

## 2026-05-05 11:48 +02:00 - Original Healthbar HUD

- Task: add the player healthbar HUD now, without broad HUD composition.
- Inspected: AS `HUD.health.mask._yscale`, FFDEC `HUD.health` placement, `DefineSprite_176`, and bitmaps `170.png`/`174.png`.
- Changed: `ha2_env.py`, `tests/test_env_basic.py`, `docs/parity_notes.md`, and handoff docs.
- Implemented: original healthbar asset rendering at `(431,0)` with bottom-anchored fill from `player.health / 100`.
- Validation passed: `py_compile`; `pytest -q` (`35 passed`); random replay record/verify.
- Manual GUI not run by Codex.
- Remaining risk: full original HUD composition for score/time/ammo/reload/hyperjump is still unimplemented.

## 2026-05-05 11:59 +02:00 - Healthbar Margin and ZQSD Input

- Task: nudge the healthbar off the border and add French-layout movement keys.
- Changed: `ha2_env.py`, `scripts/play_human.py`, `tests/test_env_basic.py`, `docs/parity_notes.md`, and handoff docs.
- Implemented: small leftward healthbar offset; `ZQSD` now maps to left/jump/duck/right alongside existing controls; mouse input in `play_human` falls back cleanly when no video system is active.
- Validation passed: `py_compile`; `pytest -q` (`36 passed`).
- Remaining risk: healthbar margin is still a visual approximation.

## 2026-05-05 15:31 +02:00 - combat_v1 RL Interface

- Task: add the first training-ready RL interface slice without changing legacy defaults.
- Changed: `ha2_env.py`, `ha2_replay.py`, `scripts/train_parkour.py`, `scripts/evaluate_model.py`, `scripts/watch_model.py`, `scripts/play_replay.py`, `tests/test_rl_interface.py`, `.gitignore`, and handoff docs.
- Observation: `combat_v1` uses 37 float32 fields: player state, gun state, primary Heli state, nearest enemy-bullet threat, world/camera, kills, and score.
- Reward: `0.01 + 0.05*score_delta + 5*killed_helis - 0.10*player_damage - 25 if terminated`.
- Episode rules: legacy unchanged; `combat_v1` terminates on fall/player death and truncates at `max_episode_steps` with `termination_reason`.
- Validation passed: `py_compile`; `pytest -q` (`46 passed`); random replay record/verify; scripted trace all; key replay verifies; SB3 `check_env`; `train_parkour --total-timesteps 1000 --n-envs 1 --wandb off`; `evaluate_model --episodes 1`.
- Manual GUI not run by Codex.
- Bugs/workarounds: replay headers now store optional training profile/max steps so combat-profile replays verify while old replays remain legacy.
- Remaining risks: reward is a first-pass training signal, PPO quality is not evaluated, and AS parity is unaffected/unproven by this RL interface.
- Next: review short SB3 smoke behavior and decide whether to tune reward/observations or add curriculum tasks.

## 2026-05-05 17:30 +02:00 - Experiment Directory System

### Task Attempted
Implemented the local experiment-directory system for HA2 RL runs.

### Files Changed or Created
- Added `scripts/experiment_utils.py`.
- Updated `scripts/train_parkour.py`, `scripts/evaluate_model.py`, `scripts/watch_model.py`, `.gitignore`, `docs/ai/CURRENT_STATE.md`, `docs/ai/ARCHITECTURE_DECISIONS.md`, `docs/ai/VALIDATION.md`, and `docs/ai/CODEX_SESSION_LOG.md`.
- Added `tests/test_experiment_outputs.py`.

### Repository Facts Discovered
- `train_parkour` now creates unique experiment folders under `experiments/` by default.
- The experiment layout is self-contained: `config.json`, `git_info.txt`, `summary.md`, `models/`, `reports/`, `replays/`, and `tensorboard/`.
- `evaluate_model` resolves `best`/`latest` from an experiment and writes reports/replays inside that experiment by default.
- `watch_model` can resolve experiment-scoped `best`/`latest` models and can auto-name replay/GIF outputs.
- `scripts.run_experiment.py` was deferred.

### Command Examples
- `python -m scripts.train_parkour --total-timesteps 1000 --n-envs 1 --wandb off`
- `python -m scripts.evaluate_model --experiment experiments/<created_experiment> --model-choice latest --episodes 1 --save-replays`
- `python -m scripts.evaluate_model --experiment experiments/<created_experiment> --model-choice best --episodes 1 --save-replays`
- `python -m scripts.watch_model --experiment experiments/<created_experiment> --model-choice latest`

### Validation Result
- Passed: `py_compile` for `scripts/experiment_utils.py`, `scripts/train_parkour.py`, `scripts/evaluate_model.py`, `scripts/watch_model.py`.
- Passed: `pytest -q` (`50 passed`).
- Passed: `record_random_replay --steps 300`, `verify_replay replays/smoke.jsonl`.
- Passed: `record_scripted_trace --scenario all` and all key replay verifications.
- Passed: `train_parkour --total-timesteps 1000 --n-envs 1 --wandb off`.
- Passed: `evaluate_model --experiment experiments/ha2_000001_20260505_1729_combat-v1_1k --model-choice latest --episodes 1 --save-replays`.
- Passed: `evaluate_model --experiment experiments/ha2_000001_20260505_1729_combat-v1_1k --model-choice best --episodes 1 --save-replays`.
- Passed: `verify_replay` on `experiments/ha2_000001_20260505_1729_combat-v1_1k/replays/latest_eval_ep0.jsonl` and `best_eval_ep0.jsonl`.
- Manual GUI watch was not run.

### Bugs or Blockers Encountered
- None in the implementation path.

### Fixes or Workarounds Applied
- Evaluation and replay outputs fail clearly if the target file already exists instead of overwriting silently.
- `best_model.zip` is still copied to `best.zip` inside the experiment for compatibility.

### Architectural Discrepancies
- Root-level `models/` and `reports/` remain only as legacy/ad hoc compatibility, but the preferred path is now experiment-scoped outputs.

### Remaining Risks
- `watch_model` still needs manual GUI validation.
- `run_experiment.py` was deferred, so train/eval remains a two-step smoke path.

### Suggested Next Step
- Manually run `python -m scripts.watch_model --experiment experiments/<created_experiment> --model-choice latest`, then decide whether to add `run_experiment.py`.

## 2026-05-05 17:45 +02:00 - Fast-Forward GUI Toggle

### Task Attempted
Added a GUI fast-forward toggle for replay and model-watch viewers.

### Files Changed or Created
- Updated `scripts/play_replay.py`, `scripts/watch_model.py`, `docs/ai/CURRENT_STATE.md`, and `docs/ai/CODEX_SESSION_LOG.md`.

### Behavior
- `F` toggles fast-forward in both `play_replay` and `watch_model`.
- Fast-forward multiplies the target FPS by the configured multiplier instead of changing replay/model semantics.

### Validation Result
- Pending compile/pytest at the time of this log entry; no manual GUI validation yet.

### Remaining Risks
- Fast-forward feel and exact frame pacing still need manual GUI testing.

### Suggested Next Step
- Manually test `F` in `python -m scripts.play_replay ...` and `python -m scripts.watch_model ...`.

## 2026-05-14 Europe/Paris - Visual Startup Speed Pass

- Task: profile visual startup again and apply only clean low-risk improvements.
- Changed: `ha2_env.py`, `scripts/play_human.py`, `scripts/play_replay.py`, `scripts/watch_model.py`, `docs/ai/CURRENT_STATE.md`, and `docs/ai/CODEX_SESSION_LOG.md`.
- Findings: normal env first render is import-bound at about `0.68-0.72s`; replay loading for a 1545-step replay adds about `0.04s`; `watch_model` with the latest 1m experiment model measured about `5.8s`, dominated by SB3 import (`~3.85s`) and model load (`~1.57s`).
- Implemented: suppress Pygame support prompt before Pygame import, avoid the first-render debug-panel display resize, defer `watch_model` Pygame/env/replay imports until after model path resolution and SB3 model load, and keep NumPy lazy for GIF recording.
- Validation passed: `py_compile ha2_env.py scripts/play_human.py scripts/play_replay.py scripts/watch_model.py`; `pytest -q tests/test_env_basic.py tests/test_experiment_outputs.py` (`31 passed`).
- Manual GUI not run.
- Remaining risk: larger startup gains would require a broader lazy-Pygame/env import split or persistent process strategy; current clean low-risk headroom is small.

## 2026-05-14 Europe/Paris - VecEnv Benchmark Pass

- Task: add safe optional `DummyVecEnv`/`SubprocVecEnv` selection and a small PPO benchmark matrix.
- Changed: `scripts/train_parkour.py`, `scripts/run_experiment.py`, `scripts/benchmark_vec_envs.py`, `tests/test_vec_env_benchmark.py`, `.gitignore`, `docs/ai/CURRENT_STATE.md`, `docs/ai/VALIDATION.md`, and `docs/ai/CODEX_SESSION_LOG.md`.
- Also retained prior same-session visual startup cleanup in `ha2_env.py`, `scripts/play_human.py`, `scripts/play_replay.py`, and `scripts/watch_model.py`.
- Behavior: `--vec-env dummy|subproc` is available in `train_parkour` and `run_experiment`; default remains `dummy`.
- Benchmark reports: `reports/vec_env_benchmarks/20260514_163024_vec_env_benchmark.json` and `.md`.
- Benchmark summary: dummy/1 env `29.20s`, `70.1` computed steps/s, SB3 fps `88`; dummy/2 env `31.40s`, `65.2`, fps `147`; subproc/1 env `29.51s`, `69.4`, fps `86`; subproc/2 env `32.11s`, `63.8`, fps `169`.
- Result: SubprocVecEnv worked on Windows at `n_envs=2`, but it was slightly slower wall-clock than DummyVecEnv in this tiny laptop smoke benchmark.
- Validation passed: full `py_compile`; `pytest -q` (`54 passed`); dummy train smoke; subproc train smoke; benchmark smoke; random replay record/verify; scripted trace all; key replay verifies.
- Warning observed: SB3 warns that SubprocVecEnv training env and eval env wrapper types differ; training still completed and saved models.
- Manual GUI not run.
- Remaining risk: tiny 2048-step smoke runs are not enough to pick a default for 500k+ runs; run a larger local benchmark before changing defaults.
- Suggested next step: `python -m scripts.benchmark_vec_envs --total-timesteps 8192 --repeats 2 --vec-envs dummy subproc --n-envs 1 2 4 8 --wandb off --device cpu`.

## 2026-05-13 23:55 Europe/Paris - WandB Experiment Sync System

### Task Attempted
Implemented a robust experiment synchronization system using WandB Artifacts to support dual-computer contribution.

### Files Changed or Created
- Created `scripts/sync_experiment.py`.
- Updated `scripts/train_parkour.py`.
- Updated `.gitignore`.
- Updated `docs/ai/ARCHITECTURE_DECISIONS.md`, `docs/ai/CURRENT_STATE.md`, and `docs/ai/CODEX_SESSION_LOG.md`.

### Repository Facts Discovered
- The `wandb` library (v0.26.1) is strict about the 40-character length of "Classic" API keys when using `wandb login` or environment variables.
- New-style Personal Access Tokens (`wandb_v1_...`) are supported but required manual `wandb login --relogin` to be accepted in this environment.
- Local configuration can be managed via `.env` using `python-dotenv`, allowing per-folder WandB identities (entity/project).

### Commands Run
- `pip install python-dotenv`
- `python -m scripts.train_parkour --total-timesteps 100 --n-envs 1 --wandb on --experiment-name "sync_final_test"`
- `python -m scripts.sync_experiment "sync_final_test" --experiments-root "experiments_sync_test"`
- `wandb login --relogin`

### Validation Result
- Passed: `py_compile` for `scripts/train_parkour.py` and `scripts/sync_experiment.py`.
- Passed: Full training run with `--wandb on` successfully uploaded experiment artifacts (models, replays, reports, config) to WandB.
- Passed: `scripts.sync_experiment` successfully downloaded the experiment artifact, recreating the identical directory structure locally.

### Bugs or Blockers Encountered
- `wandb.errors.errors.AuthenticationError`: API key length validation (40+ characters) blocked `.env`-based login for new-style tokens initially.

### Fixes or Workarounds Applied
- Added `python-dotenv` support to scripts to load local `.env` configuration.
- Simplified `wandb.init` to allow global/environment defaults while still supporting `.env` overrides.
- Recommended manual `wandb login --relogin` for tokens that don't satisfy the library's strict environment variable length checks.

### Architectural Discrepancies
- None; the system aligns with the "Experiment Directory" decision from 2026-05-05.

### Remaining Risks
- Users must remember to run `sync_experiment.py` on the second machine; there is no "auto-pull" on startup.
- `.env` files must be manually synchronized or recreated (they are git-ignored).

### Suggested Next Step
- Start a real training run with `--wandb on` and verify the dashboard and artifacts are accessible on both machines.

## 2026-05-14 00:30 Europe/Paris - RL Training Workflow and Diagnostics

### Task Attempted
Set up a robust first real HA2 RL training workflow around the existing `combat_v1` environment by implementing a bounded training orchestration and diagnostics layer.

### Files Changed or Created
- Created `scripts/run_experiment.py`.
- Updated `ha2_env.py` to add new combat metrics counters (`total_player_damage`, `heli_kills`, etc.) to the `info` dict.
- Updated `scripts/train_parkour.py` to accept `args_list`, return `ExperimentLayout`, and support `--no-wandb-finish`.
- Updated `scripts/evaluate_model.py` to accept `args_list` and output aggregate combat diagnostics (min, max, mean, sum) to the JSON report.
- Updated `scripts/watch_model.py` to accept `args_list`.
- Updated `docs/ai/CURRENT_STATE.md`, `docs/ai/VALIDATION.md`, and `docs/ai/CODEX_SESSION_LOG.md`.

### Repository Facts Discovered
- `train_parkour.py`, `evaluate_model.py`, and `watch_model.py` were previously heavily reliant on direct `sys.argv` parsing, requiring minor refactoring to accept `args_list` for clean orchestration.

### Commands Run
- `python -m scripts.run_experiment --total-timesteps 100 --n-envs 1 --eval-episodes 1` (Smoke tests)
- `python -m scripts.run_experiment --total-timesteps 1000 --n-envs 1 --wandb off --eval-episodes 1 --save-replays` (Validation test)

### Validation Result
- Passed: `run_experiment.py` orchestrates training and evaluation seamlessly in one process.
- Passed: `ha2_env.py` successfully returns new combat metrics in the `info` dict.
- Passed: Evaluation reports now include detailed min/max/mean/sum aggregates and termination reason counts.
- Passed: Full validation run created a complete experiment directory with models, config, summaries, reports, and replays.

### Bugs or Blockers Encountered
- `train_parkour.py` had redundant `parser.parse_args()` calls which caused parsing errors when arguments were passed via `args_list`.
- WandB artifact upload had to be moved/delayed to `run_experiment.py` (via `--no-wandb-finish`) so that the evaluation artifacts (reports and replays) would be included in the upload.

### Fixes or Workarounds Applied
- Removed redundant arg parsing in `train_parkour.py`.
- Added the `--no-wandb-finish` flag to `train_parkour.py` and moved the artifact upload logic to the end of `run_experiment.py`.

### Architectural Discrepancies
- None; the system aligns with the established "Experiment Directory" strategy and enhances it with orchestration.

### Remaining Risks
- The 1000-step smoke run does not guarantee the model will learn; a longer real training run is still needed.

### Suggested Next Step
- Start a real training run on a more powerful machine (e.g., Ubuntu workstation) using `scripts.run_experiment` and monitor the WandB dashboard to evaluate the learning behavior.

## 2026-05-14 01:05 Europe/Paris - RL Diagnostics and Firing Metrics

### Task Attempted
Improve RL experiment diagnostics by evaluating both best and latest models, generating detailed statistical reports, and clarifying firing metrics.

### Files Changed or Created
- Updated `ha2_env.py` to differentiate between `player_shot_attempts`, `player_bullets_spawned`, and `player_shots_spawn_blocked` instead of a generic `gun_shots` counter.
- Updated `scripts/evaluate_model.py` to calculate structured metrics (mean, std, min, max, sum), derived rates (hit, death, fall, timeout), and marginal action distributions.
- Updated `scripts/run_experiment.py` to evaluate both `best` and `latest` models and append a structured evaluation summary to the experiment's `summary.md`.
- Updated `docs/ai/CURRENT_STATE.md` and `docs/ai/CODEX_SESSION_LOG.md`.

### Repository Facts Discovered
- `evaluate_model.py` used simple averages for episode rewards and lengths, lacking the statistical depth needed to analyze variance in model behavior.
- Firing metrics were conflating a button press with an actual bullet spawn, making hit rate calculations inaccurate when bullets were blocked by walls.

### Commands Run
- `python -m scripts.run_experiment --total-timesteps 1000 --n-envs 1 --wandb off --eval-episodes 1 --save-replays` (Validation test)

### Validation Result
- Passed: `ha2_env.py` successfully tracks detailed firing metrics.
- Passed: `evaluate_model.py` generates detailed structured JSON reports including action distributions.
- Passed: `run_experiment.py` evaluates both models and correctly updates `summary.md`.

### Bugs or Blockers Encountered
- None.

### Fixes or Workarounds Applied
- None.

### Architectural Discrepancies
- None.

### Remaining Risks
- The marginal action distribution only counts executed actions; SB3's exploratory actions during training are logged to WandB but are not part of the final evaluation report.

### Recommended Next Action
- Conduct the 500k RL training run on the Ubuntu workstation using `run_experiment.py`.

## 2026-05-14 17:50 Europe/Paris - VecEnv Eval Controls and Benchmark Modes

### Task Attempted
Add explicit training-time eval controls and split VecEnv benchmarks into train-only and workflow modes.

### Files Changed
- `scripts/train_parkour.py`
- `scripts/run_experiment.py`
- `scripts/benchmark_vec_envs.py`
- `tests/test_vec_env_benchmark.py`
- `docs/ai/CURRENT_STATE.md`
- `docs/ai/VALIDATION.md`
- `docs/ai/CODEX_SESSION_LOG.md`

### Validation
- Passed: py_compile for core files and touched scripts.
- Passed: `python -m pytest -q` using `.venv` (`58 passed`).
- Passed: dummy train-only smoke and SubprocVecEnv `--eval-vec-env same` workflow smoke.
- Passed: train-only benchmark report `reports/vec_env_benchmarks/20260514_174712_vec_env_benchmark.json`.
- Passed: workflow benchmark report `reports/vec_env_benchmarks/20260514_174755_vec_env_benchmark.json`.
- Passed: random replay and required scripted trace verification.

### Benchmark Summary
- Train-only 2048-step smoke: best wall-clock was `dummy n_envs=2` at `6.44s` / `318.0 requested steps/s`.
- Workflow 2048-step smoke: best wall-clock was `dummy n_envs=1` at `12.29s` / `166.7 requested steps/s`.
- `--eval-vec-env same` removed the SB3 wrapper mismatch warning in the SubprocVecEnv smoke and benchmark.

### Remaining Risks
- Tiny 2048-step benchmark results are smoke data only; Charles should run the larger `8192`/multi-repeat benchmark before choosing local defaults.
- Default remains `dummy`; do not switch to SubprocVecEnv based on current measurements.

### Suggested Next Step
- Run `python -m scripts.benchmark_vec_envs --mode both --total-timesteps 8192 --repeats 2 --vec-envs dummy subproc --n-envs 1 2 4 8 --eval-vec-env same --wandb off --device cpu`.
