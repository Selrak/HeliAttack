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
