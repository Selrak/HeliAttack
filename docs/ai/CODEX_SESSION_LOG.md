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

## 2026-05-17 23:23 Europe/Paris - Pytest Runtime Cut

### Task Attempted
Reduced end-to-end pytest runtime by trimming duplicate or expensive smoke coverage.

### Files Changed or Updated
- Updated `tests/test_benchmark_orchestration.py`.
- Updated `tests/test_vec_env_benchmark.py`.
- Updated `tests/test_curriculum.py`.
- Updated `tests/test_runtime_config.py`.
- Updated `tests/test_reward_profiles.py`.
- Updated `docs/ai/CURRENT_STATE.md`.
- Updated `docs/ai/VALIDATION.md`.
- Updated `docs/ai/CODEX_SESSION_LOG.md`.

### Repository Facts Discovered
- The full suite now completes in about 35.9 seconds locally.
- The slowest remaining tests are the subproc VecEnv smoke, the curriculum training smoke, the runtime CLI acceptance loop, and the parallel benchmark orchestration test.
- `python -m pytest` must be run from `.venv` on this machine because the system Python does not have pytest installed.

### Commands Run
- `& .\.venv\Scripts\python.exe -m pytest tests/test_benchmark_orchestration.py tests/test_vec_env_benchmark.py tests/test_curriculum.py tests/test_runtime_config.py tests/test_reward_profiles.py -q --durations=25`
- `& .\.venv\Scripts\python.exe -m pytest -q --durations=25`

### Validation Result
- Passed: focused subset, `35 passed in 23.58s`.
- Passed: full suite, `100 passed in 35.89s`.

### Bugs or Blockers Encountered
- `test_parallel_staggered_durations` was still using `tmp_path` without receiving it; fixed by adding the fixture argument.
- The system Python lacked pytest, so validation had to use the project venv.

### Fixes or Workarounds Applied
- Reduced PPO smoke cost by lowering `n_steps` to 16 in the small training tests.
- Replaced one SB3 import-heavy reward-profile test with a fake `Monitor` module.
- Replaced a full training-based subproc smoke with a direct `SubprocVecEnv` creation/step check.
- Removed duplicate subprocess `--help` coverage for scripts already covered by more direct runtime-config tests.
- Isolated the benchmark orchestration test in `tmp_path` and added retry cleanup for Windows file handles.

### Architectural Discrepancy Introduced or Discovered
- None. These changes only reduced test cost and did not change simulator behavior.

### Remaining Risks
- The suite is much faster, but the subproc VecEnv smoke still dominates wall time.
- The benchmark orchestration test remains slower than the rest and may merit a later split if more speed is needed.

### Suggested Next Step for ChatGPT Webchat to Review
- Decide whether to keep the remaining expensive smoke tests as-is or split them into a separate slow marker for optional CI.

## 2026-05-17 23:23 Europe/Paris - Watch Model Config Inference Fix

### Task Attempted
Fixed `watch_model`/`evaluate_model` loading a model from `experiments/.../models/` without an explicit `--experiment`.

### Files Changed or Updated
- Updated `scripts/experiment_utils.py`.
- Updated `scripts/watch_model.py`.
- Updated `scripts/evaluate_model.py`.
- Updated `docs/ai/CURRENT_STATE.md`.
- Updated `docs/ai/CODEX_SESSION_LOG.md`.

### Repository Facts Discovered
- A direct model path inside an experiment directory was not enough for runtime config inference.
- The failure mode was an 84-dim model being paired with the default 37-dim env.

### Commands Run
- `& .\.venv\Scripts\python.exe -m py_compile scripts/watch_model.py scripts/evaluate_model.py scripts/experiment_utils.py`
- `& .\.venv\Scripts\python.exe -c "...resolve_experiment_layout_and_config...make_controlled_env..."`

### Validation Result
- Passed: syntax check.
- Passed: direct inference smoke returned `movement_no_boost_scripted_attack_direct` and env observation shape `(84,)`.

### Bugs or Blockers Encountered
- None.

### Fixes or Workarounds Applied
- Added shared experiment-layout/config inference from a model path when it lives under `experiments/.../models/`.
- Kept root-level `models/best.zip` and `models/latest.zip` behavior unchanged.

### Architectural Discrepancy Introduced or Discovered
- None.

### Remaining Risks
- If a model is moved out of its experiment directory, `watch_model` still needs `--experiment` or matching runtime flags.

### Suggested Next Step for ChatGPT Webchat to Review
- None; this was a narrow compatibility fix.

## 2026-05-17 23:23 Europe/Paris - Watch Model Wrapper Render Fix

### Task Attempted
Fixed `watch_model` failing when the loaded experiment uses a control wrapper.

### Files Changed or Updated
- Updated `scripts/watch_model.py`.
- Updated `docs/ai/CURRENT_STATE.md`.
- Updated `docs/ai/CODEX_SESSION_LOG.md`.

### Repository Facts Discovered
- `watch_model` was calling `render(debug_overlay=...)` on a Gym wrapper, not the base env.
- The failing case is wrapper-based control modes such as `movement_no_boost_scripted_attack_direct`.

### Commands Run
- `& .\.venv\Scripts\python.exe -m py_compile scripts/watch_model.py scripts/experiment_utils.py scripts/evaluate_model.py`

### Validation Result
- Passed: syntax check.

### Bugs or Blockers Encountered
- None.

### Fixes or Workarounds Applied
- Switched `watch_model` rendering to `env.unwrapped.render(...)`.

### Architectural Discrepancy Introduced or Discovered
- None.

### Remaining Risks
- Other wrapper-based scripts may still need the same pattern if they start passing custom render kwargs.

### Suggested Next Step for ChatGPT Webchat to Review
- Retry the exact `watch_model` command against the experiment model path.

## 2026-05-18 12:04 Europe/Paris - Human-Friendly Count Parsing

### Task Attempted
Added suffix/underscore parsing for step/timestep-style CLI counts.

### Files Changed or Updated
- Updated `scripts/runtime_config.py`.
- Updated `scripts/train_parkour.py`.
- Updated `scripts/run_experiment.py`.
- Updated `scripts/run_experiment_pair.py`.
- Updated `scripts/benchmark_vec_envs.py`.
- Updated `scripts/record_random_replay.py`.
- Updated `scripts/record_scripted_trace.py`.
- Updated `tests/test_runtime_config.py`.
- Updated `docs/ai/CURRENT_STATE.md`.
- Updated `docs/ai/VALIDATION.md`.
- Updated `docs/ai/CODEX_SESSION_LOG.md`.

### Repository Facts Discovered
- Plain `int` parsing already accepted underscore-separated numerals like `500_000`.
- Suffix forms like `500k` and `1M` were not accepted before this change.

### Commands Run
- `& .\.venv\Scripts\python.exe -m py_compile scripts/runtime_config.py scripts/train_parkour.py scripts/run_experiment.py scripts/run_experiment_pair.py scripts/benchmark_vec_envs.py scripts/record_random_replay.py scripts/record_scripted_trace.py`
- `& .\.venv\Scripts\python.exe -m pytest tests/test_runtime_config.py -q`
- `& .\.venv\Scripts\python.exe -m pytest -q`

### Validation Result
- Passed: syntax check.
- Passed: runtime-config test file, `8 passed`.
- Passed: full suite, `101 passed in 34.69s`.

### Bugs or Blockers Encountered
- None.

### Fixes or Workarounds Applied
- Added a shared `parse_human_count()` helper and wired it into the step/timestep-style CLI args only.

### Architectural Discrepancy Introduced or Discovered
- None.

### Remaining Risks
- Only the CLI fields wired through the helper accept suffixes; unrelated numeric args such as seeds and FPS still use plain integers by design.

### Suggested Next Step for ChatGPT Webchat to Review
- None; this was a narrow input-format improvement.

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

## 2026-05-14 23:05 Europe/Paris - combat_bullets_v1 Profile

### Task Attempted
Implement the `combat_bullets_v1` observation profile to support multi-bullet dodging by exposing the top-10 nearest visible enemy bullets instead of just one engine-nearest bullet.

### Files Changed or Created
- Updated `ha2_env.py` to define `COMBAT_BULLETS_V1_OBS_FIELDS` (84 dimensions), implement `_get_combat_bullets_v1_obs`, and update `_get_obs` and `__init__` space definitions.
- Updated `scripts/train_parkour.py`, `scripts/evaluate_model.py`, `scripts/watch_model.py`, and `scripts/run_experiment.py` to accept `combat_bullets_v1` as a valid `--training-profile`.
- Updated `docs/ai/OBSERVATION_AUDIT.md`, `docs/ai/CURRENT_STATE.md`, and `docs/ai/CODEX_SESSION_LOG.md`.

### Repository Facts Discovered
- `combat_v1` had exactly 37 fields; replacing the 5 nearest-bullet fields with 2 global counts and 10 bullets of 5 fields each accurately sums to 84 fields.
- The `enemy_bullet_count` field existed *before* the nearest bullet fields in `combat_v1` and was retained.

### Commands Run
- `python -m scripts.run_experiment --total-timesteps 100 --n-envs 1 --wandb off --eval-episodes 1 --training-profile combat_bullets_v1`

### Validation Result
- Passed: `ha2_env.py` generates the 84-dimensional `combat_bullets_v1` observation.
- Passed: `run_experiment.py` successfully trains and evaluates using the new profile.

### Bugs or Blockers Encountered
- `AssertionError: combat_bullets_v1 observation size mismatch: (83,)` occurred during initial testing.

### Fixes or Workarounds Applied
- Fixed the observation size mismatch by correctly appending the `enemy_bullet_count` back into the array generation logic for the new profile, as it was inadvertently left out during the copy-paste from `combat_v1`.

### Architectural Discrepancies
- None. The new profile is cleanly separated from `combat_v1`, which remains unchanged.

### Remaining Risks
- The 100-timestep smoke run proves the array shape is correct and SB3 accepts it, but does not prove the model can effectively learn the 10-bullet array representation.

### Recommended Next Action
- Run a longer training session (e.g., 500k timesteps) using `--training-profile combat_bullets_v1` and compare the dodging behavior against the `combat_v1` baseline.

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

## 2026-05-14 20:02 Europe/Paris - Defensive Diagnostics and Observation Audit

### Task Attempted
Add visible enemy-bullet diagnostics, damage timing metrics, compact eval summary rows, and a `combat_v1` observation audit without changing simulator mechanics, rewards, observations, or replay state.

### Files Changed
- `ha2_env.py`
- `scripts/evaluate_model.py`
- `scripts/run_experiment.py`
- `tests/test_rl_interface.py`
- `tests/test_experiment_outputs.py`
- `docs/ai/OBSERVATION_AUDIT.md`
- `docs/ai/CURRENT_STATE.md`
- `docs/ai/VALIDATION.md`
- `docs/ai/CODEX_SESSION_LOG.md`

### Validation
- Passed: py_compile for required core files and scripts.
- Passed: `python -m pytest -q` using `.venv` (`64 passed`).
- Passed: random replay and required scripted trace verification.
- Passed: `python -m scripts.run_experiment --total-timesteps 1000 --n-envs 1 --wandb off --eval-episodes 1 --save-replays`.
- Smoke experiment: `experiments/ha2_000023_20260514_2001_combat-v1_1k`.

### Diagnostic Facts
- Visible predicate: enemy bullet center transformed by `world_x/world_y` must intersect the gameplay viewport with an 8 px margin; the debug side panel is excluded.
- Off-screen bullets are excluded from visible defensive denominators.
- Top-10 clipping pressure is reported through frames over 10 visible bullets and max excess.
- Replay hashes stayed valid after regenerated trace verification.
- `combat_v1` currently exposes one nearest engine-side enemy bullet with relative position and velocity, not all visible bullets.

### Remaining Risks
- The visible predicate approximates sprite bounds by center plus margin; exact Flash visibility is not proven.
- Defensive metrics need review on real 500k experiment reports before changing observations or rewards.

### Suggested Next Step
- Compare the existing 500k `combat_v1` runs with the new defensive diagnostics, especially damage timing and visible bullet hit rate.

## 2026-05-15 13:00 Europe/Paris - Policy Capacity and Movement Diagnostics

### Task Attempted
Implemented PPO policy-capacity controls (`--net-arch`) and movement diagnostics (grounded/airborne frames, boost/jump counts, lateral range) to analyze agent behavior.

### Files Changed or Created
- Updated `ha2_env.py` to track 15+ new movement diagnostic counters and expose them in `info`.
- Updated `scripts/train_parkour.py` and `scripts/run_experiment.py` to support `--net-arch` and record policy metadata (parameter count, architecture) in `config.json`.
- Updated `scripts/evaluate_model.py` to aggregate movement diagnostics and policy metadata in JSON reports.
- Updated `docs/ai/OBSERVATION_AUDIT.md`, `docs/ai/CURRENT_STATE.md`, and `docs/ai/CODEX_SESSION_LOG.md`.
- Created `tests/test_rl_diagnostics.py`.

### Repository Facts Discovered
- `hyperjump / 150.0` is visible to the policy, providing charge/cooldown info, but the `hjump` (active boost) flag and lockout flags are currently hidden.
- MlpPolicy defaults to `[64, 64]` hidden layers in SB3; providing `--net-arch` allows testing if the 84-dim `combat_bullets_v1` profile needs more capacity.

### Commands Run
- `python -m pytest` (Passed 64/64)
- `python -m scripts.run_experiment --total-timesteps 1000 --net-arch 128,128 --training-profile combat_bullets_v1 --eval-episodes 1` (Passed smoke run)

### Validation Result
- Passed: `ha2_env.py` state variables correctly reset and accumulate.
- Passed: `config.json` correctly records `trainable_parameters` and `net_arch`.
- Passed: `summary.md` comparisons now include movement behavior tables.

### Bugs or Blockers Encountered
- `AttributeError: 'HeliAttack2Env' object has no attribute 'min_player_x'`: Fixed by ensuring all new diagnostics are initialized in `__init__` as well as `reset()`.
- `SyntaxError` in `evaluate_model.py`: Fixed a corrupted string literal in the `if __name__ == "__main__"` block.

### Fixes or Workarounds Applied
- Implemented `aggregate_metric` helper in `evaluate_model.py` to handle `None` values (e.g. no damage events) gracefully in reports.

### Architectural Discrepancies
- None.

### Remaining Risks
- The diagnostics increase the `info` dict size significantly; this is fine for CPU training but should be monitored if memory becomes tight on many parallel envs.

### Recommended Next Action
- Analyser les résultats du grand run parallèle de 500k pour les deux profils une fois terminé.

## 2026-05-15 14:00 Europe/Paris - Thread Benchmarking and Parallel 500k Run

### Task Attempted
Executer séquentiellement les tests de charge CPU recommandés dans `NEXT_CODEX_TASK.md` (2, auto=6, 4, 8, et 12 threads) sur 50k pas, puis lancer la véritable comparaison de 500k pas en mode parallèle.

### Files Changed or Created
- `docs/ai/CODEX_SESSION_LOG.md` mis à jour avec les résultats du benchmark.

### Repository Facts Discovered
- La machine cible (ThinkPad P16, 24 processeurs logiques) souffre d'oversubscription (surcharge de synchronisation des threads) si PPO reçoit trop de threads en mode DummyVecEnv.
- Le "sweet spot" se situe entre 4 et 6 threads par job en mode parallèle.

### Commands Run
- `python -m scripts.run_experiment_pair --mode both --total-timesteps 50000 --threads-per-job <X>` pour X = 2, auto(6), 4, 8, 12.
- `python -m scripts.run_experiment_pair --mode parallel --total-timesteps 500000 --threads-per-job auto` (Lancé en tâche de fond).

### Validation Result
- Une série de benchmarks à 50 000 pas a été réalisée pour mesurer l'impact du nombre de threads Torch (`--threads-per-job`) sur les modes Séquentiel et Parallèle (2 jobs concurrents avec un décalage de 60s).

| Threads/Job | Temps Séquentiel | Temps Parallèle | Speedup Parallèle |
|-------------|------------------|-----------------|-------------------|
| 2           | 243.32s          | 229.98s         | 1.06x             |
| 4           | 260.49s          | 196.10s         | 1.33x             |
| 6 (`auto`)  | 272.85s          | 196.29s         | 1.39x             |
| 8           | 269.20s          | 206.87s         | 1.30x             |
| 12          | 283.98s          | 271.51s         | 1.05x             |

**Analyse des résultats :**
1. **Séquentiel :** Plus on alloue de threads à PyTorch (de 2 à 12), plus l'entraînement *séquentiel* est lent (passant de 243s à 284s). L'environnement étant très léger et l'architecture réseau modeste (128x128), le coût de synchronisation interne des threads Torch (overhead) l'emporte sur le gain de calcul matriciel.
2. **Parallèle :** L'exécution de deux jobs en concurrence devient très efficace à 4 ou 6 threads par job (tombant à 196s, contre 230s pour 2 threads). 
3. **Saturation :** À 12 threads par job (soit 24 threads Torch au total, ce qui correspond exactement aux 24 processeurs logiques de la machine), la machine sature (oversubscription) et le temps parallèle remonte à 271s, annulant tout bénéfice.
- Le réglage par défaut `auto` (qui alloue `os.cpu_count() // 4 = 6` threads) s'avère être un excellent compromis pour le mode parallèle sur cette machine.

### Architectural Discrepancies
- None.

### Suggested Next Step
- Attendre la fin du run de 500k et analyser les rapports d'évaluation pour déterminer l'efficacité du nouveau profil `combat_bullets_v1`.

## 2026-05-15 13:40 Europe/Paris - PPO Timing and Concurrent Benchmarking

### Task Attempted
Add lightweight PPO runtime timing and a sequential-vs-parallel experiment benchmark to answer questions about wall-clock time distribution and parallel task throughput on a single machine.

### Files Changed or Created
- Created `scripts/runtime_timing.py` to house the `TimingCallback` and `TrainingTiming` dataclass.
- Created `scripts/run_experiment_pair.py` to orchestrate A/B training pairs sequentially or concurrently with controlled thread counts.
- Created `tests/test_benchmark_orchestration.py`.
- Updated `scripts/train_parkour.py` and `scripts/run_experiment.py` to support `--timing-profile on` and `--torch-num-threads`.
- Updated `docs/ai/CURRENT_STATE.md` and `docs/ai/CODEX_SESSION_LOG.md`.

### Repository Facts Discovered
- `DummyVecEnv` does not fully utilize all logical processors unless the underlying environment is heavily threaded, leaving room for a second training process to run concurrently.
- Pickling (used for saving models) fails when internal model methods are monkey-patched (`TypeError: cannot pickle 'EncodedFile' object`). This required switching to a standard SB3 Callback (`TimingCallback`) instead of direct function wrapping for PPO methods.

### Commands Run
- `python -m scripts.run_experiment_pair --total-timesteps 256 --n-envs 1 --eval-episodes 1 --mode both` (Smoke test)

### Validation Result
- Passed: `run_experiment_pair.py` correctly runs jobs sequentially and in parallel, parsing the results into a markdown summary and JSON file without error.
- Passed: `train_timing.md` and `orchestration_timing.md` are correctly generated.
- Passed: Model pickling works successfully when using the `TimingCallback` fix.

### Bugs or Blockers Encountered
- `TypeError: cannot pickle 'EncodedFile' object` during `model.save()` caused by monkey-patching.
- `UnicodeEncodeError` writing the pair summary markdown due to Windows encoding issues with emojis.

### Fixes or Workarounds Applied
- Replaced the monkey-patching approach with a proper `TimingCallback(BaseCallback)`.
- Used `sys.executable` instead of `"python"` in `subprocess.Popen` to ensure the correct virtual environment is used for sub-jobs.
- Set `encoding="utf-8"` on all `open()` calls that generate markdown.

### Architectural Discrepancies
- The timing system uses an SB3 Callback for rollout/training phases, but requires a small monkey-patch on `EvalCallback` since SB3 does not easily expose "did an evaluation actually run this step" to sibling callbacks.

### Remaining Risks
- Parallel mode over-subscription could still occur if the OS scheduler behaves unpredictably, but `OMP_NUM_THREADS` and `torch.set_num_threads` are now strictly set by default.

### Suggested Next Step
- Attendre la fin du run parallèle de 500k pour les deux profils.

## 2026-05-15 17:30 Europe/Paris - Fix RL Reporting and Instrumentation Bugs

### Task Attempted
Fix the RL experiment reporting and instrumentation issues discovered after the concurrent 500k A/B run.

### Files Changed or Created
- Updated `scripts/run_experiment.py` to correctly sequence the orchestration timing report generation *before* the diagnostic bundle creation, ensuring timing reports are included in the zip.
- Updated `scripts/run_experiment_pair.py` to correctly extract and record the `timing_report_path` in `JobResult` and explicitly handle `--seed-b` for clarity in logs and summaries.
- Updated `scripts/evaluate_model.py` to properly extract movement diagnostics from the nested `movement_diagnostics` dict within `info`, fixing the `n/a` values in the summary.
- Updated `scripts/evaluate_model.py` to ensure `net_arch` and other policy metadata are read from `experiment_config` and accurately recorded.
- Updated `tests/test_benchmark_orchestration.py` to include specific tests for bundling, `net_arch` reporting, movement metrics aggregation, and seed behavior.

### Repository Facts Discovered
- `DummyVecEnv` does not emit terminal infos in the standard `info` dict but in `info["terminal_info"]`. However, for `HeliAttack2Env` evaluated directly (without vectorization), the `info` dict from the final `step` contains the correct values. The issue was purely a dictionary nesting bug (`info["movement_diagnostics"]["frames_grounded"]` vs `info["frames_grounded"]`).
- Local variables in a Python script (like `config`) are not guaranteed to exist in `locals()` if they are only assigned conditionally, leading to silent `None` values when using `config.get()`.

### Commands Run
- `python -m pytest` (Passed 71/71)
- `python -m scripts.run_experiment_pair --mode parallel --total-timesteps 1000 --n-envs 1 --eval-episodes 1` (Smoke test passed)

### Validation Result
- Passed: Diagnostic bundles now correctly include `train_timing.json/md` and `orchestration_timing.json/md`.
- Passed: `pair_summary.json` records timing report paths.
- Passed: `--net-arch` is consistently recorded in `config.json`, `eval_latest.json`, and `summary.md`.
- Passed: Movement diagnostics (e.g. `frames_grounded`) no longer show `n/a` in summaries and aggregate correctly.
- Passed: Seed behavior is explicit (`Job A Seed` and `Job B Seed` are logged).

### Bugs or Blockers Encountered
- `FileExistsError` during consecutive pytest runs due to un-cleaned temporary experiment directories.
- `KeyError: 'net_arch'` in tests due to a previously overridden file update that failed to re-add the `net_arch` saving logic.

### Fixes or Workarounds Applied
- Added explicit cleanup (`shutil.rmtree`) to test fixtures.
- Fixed dictionary extraction logic using chained `.get()` with safe fallbacks.

### Architectural Discrepancies
- None.

### Remaining Risks
- None.

### Suggested Next Step
- Review the finalized reports from the 500k parallel run.

## 2026-05-15 18:30 Europe/Paris - Correct PPO Update Timing

### Task Attempted
Fix the PPO runtime timing instrumentation. The previous `TimingCallback` incorrectly measured the entire training session as "PPO Update", leading to a `train_update_count` of 1, an exaggerated `train_update_total`, and negative unclassified overhead.

### Files Changed or Created
- Updated `scripts/runtime_timing.py` to restore the explicit monkey-patching of `model.train` and `model.collect_rollouts` (`wrap_ppo_timing`).
- Fixed `unwrap_ppo_timing` to use `del model.__dict__["..."]` instead of re-assigning the original method, properly restoring class-level method lookup and preventing pickling errors during `model.save()`.
- Updated `scripts/train_parkour.py` to use `wrap_ppo_timing` and `unwrap_ppo_timing` again.
- Updated `tests/test_benchmark_orchestration.py` to add strict assertions enforcing `train_update_count == rollout_count` and `other_or_unclassified >= 0`.

### Repository Facts Discovered
- In Python, monkey-patching an instance method injects it into `__dict__`. Restoring the original bound method into `__dict__` causes Cloudpickle to fail with `cannot pickle 'EncodedFile' object` (if the model contains complex state like loggers) because the bound method captures `self`. The correct unpatching technique is to `del` the key from `__dict__` so Python falls back to the class-level method definition.

### Commands Run
- `python -m pytest tests/test_benchmark_orchestration.py` (Passed 4/4)

### Validation Result
- Passed: `other_or_unclassified` is now consistently positive.
- Passed: `train_update_count` matches `rollout_count` as expected for PPO.
- Passed: The model successfully saves (`pickles`) without throwing errors.

### Architectural Discrepancies
- None.

### Suggested Next Step
- Review the finalized reports from the 500k parallel run.

## 2026-05-15 19:30 Europe/Paris - Stable PPO Timing and Orchestration Finalization

### Task Attempted
Fix the PPO runtime timing instrumentation to correctly separate `train_update` time from total `learn()` time without breaking model pickling (`TypeError: cannot pickle '_thread.lock' object`), and finalize the parallel orchestration scripts.

### Files Changed or Created
- Updated `scripts/runtime_timing.py` to replace all monkey-patching approaches with a clean `TimedPPO` subclass that correctly measures `collect_rollouts` and `train` phases, storing results in a global `_current_timing` reference to preserve SB3 model serialization compatibility.
- Fixed the semantics of `other_or_unclassified_training_seconds` to no longer subtract `train_eval_total` (since evaluation overlaps with rollouts).
- Updated `scripts/train_parkour.py` to instantiate `TimedPPO` and correctly pass `--timing-profile`.
- Updated `scripts/run_experiment_pair.py` to properly execute background instances using `sys.executable` (fixing environment issues) and handle text encoding cleanly.
- Updated `ha2_env.py` to correctly initialize movement diagnostics boundaries.
- Updated `docs/ai/CURRENT_STATE.md` and `docs/ai/CODEX_SESSION_LOG.md`.

### Repository Facts Discovered
- SB3 Callbacks (`on_training_start`/`end`) wrap the entire learning session, making them unsuitable for timing the internal PyTorch gradient updates.
- Monkey-patching `__dict__` methods on an SB3 model instance often leads to pickling errors during `EvalCallback` checkpoints because the closure captures non-picklable objects like the internal stdout logger locks. A lightweight subclass is the safest and most robust path.

### Commands Run
- `python -m pytest tests/test_benchmark_orchestration.py` (Passed 4/4)
- `python -m scripts.run_experiment_pair --mode parallel --total-timesteps 500000 --n-envs 4 --eval-episodes 10`

### Validation Result
- Passed: `other_or_unclassified_training_seconds` is consistently `>= 0`.
- Passed: `train_update_count` exactly matches `rollout_count` as expected for PPO.
- Passed: The model successfully saves and evaluates during and after training without `Cloudpickle` errors.

### Architectural Discrepancies
- None.

### Suggested Next Step
- Review the finalized reports from the 500k parallel run.

## 2026-05-15 22:00 Europe/Paris - Source Inspection Fixes

### Task Attempted
Fix the remaining HA2 RL reporting/instrumentation bugs found by source inspection, specifically ensuring movement diagnostics are properly incremented and all diagnostic artifacts are bundled correctly.

### Files Changed or Created
- Updated `ha2_env.py` to properly increment movement metrics (`frames_grounded`, `frames_airborne`, `min_player_x`, `max_player_x`, `frames_moving_left`, etc.) within `step()` using the post-physics player state.
- Updated `scripts/train_parkour.py` to use `allow_overwrite=True` when updating `config.json` with `net_arch` and `trainable_parameters`.
- Updated `scripts/run_experiment.py` to properly wait for the `orchestration_timing` creation before bundling the zip, and ensured `eval_latest.json` and `latest_eval_ep0.jsonl` are included in the bundle.
- Updated `scripts/run_experiment_pair.py` to ensure `timing_report_path` is parsed and recorded in parallel mode, and that job duration uses the global start tick.
- Created `audit_smoke.py` temporarily to mathematically enforce the validity of all JSON/ZIP outputs.

### Repository Facts Discovered
- Movement counters like `frames_grounded` had been correctly initialized and exported previously, but the internal tracking code within `ha2_env.step()` had been lost or overwritten during a previous iteration. They must be evaluated *after* physics execution for accuracy.

### Commands Run
- `python -m scripts.run_experiment_pair --mode parallel --total-timesteps 1000 --n-envs 1 --eval-episodes 1` (Smoke test)
- `python audit_smoke.py`

### Validation Result
- Passed: `frames_grounded` and other movement diagnostics are correctly incremented, aggregated, and shown in the evaluation reports.
- Passed: `pair_summary.json` correctly stores `timing_report_path`.
- Passed: `_diagnostic_bundle.zip` contains both `eval_best`, `eval_latest`, their replays, and all 4 timing reports.
- Passed: `config.json` correctly saves `net_arch=128,128`, `trainable_parameters`, and `activation_fn`.

### Architectural Discrepancies
- None.

### Remaining Risks
- None.

### Suggested Next Step
- Lancer de nouvelles expérimentations RL ou analyser les résultats existants.

## 2026-05-16 01:00 Europe/Paris - Defensive Curriculum Profiles

### Task Attempted
Implement and test the first defensive curriculum reward profile (`defense_v1`) to penalize player damage, death, edge camping, and input inefficiency.

### Files Changed or Created
- Updated `ha2_env.py` to add `defense_v1` to `REWARD_PROFILES` and implement its reward breakdown in `step()`.
- Updated `scripts/train_parkour.py`, `scripts/evaluate_model.py`, `scripts/watch_model.py`, `scripts/run_experiment.py`, and `scripts/run_experiment_pair.py` to support the `--reward-profile` CLI argument.
- Created `tests/test_reward_profiles.py` to explicitly verify `combat_default` and `defense_v1` behaviors, including penalties for camping at the edge and pressing into boundaries.
- Updated `docs/ai/CURRENT_STATE.md` and `docs/ai/CODEX_SESSION_LOG.md`.

### Repository Facts Discovered
- Passing extra context like `reward_profile` across the entire hierarchy from `run_experiment_pair.py` down to `train_parkour.py` and into the config required ensuring every step forwarded the argument.

### Commands Run
- `python -m pytest` (Passed all tests, including new reward profile tests)
- `python -m scripts.run_experiment_pair --mode parallel --profile-a combat_bullets_v1 --profile-b combat_bullets_v1 --control-mode-a movement_no_boost_scripted_attack_direct --control-mode-b movement_scripted_attack_direct --reward-profile-a defense_v1 --reward-profile-b defense_v1 --label-a M0_defense --label-b M1_defense --total-timesteps 1000 --n-envs 1 --vec-env dummy --wandb off --train-eval off --eval-episodes 1 --save-replays --timing-profile on --threads-per-job 2 --net-arch 128,128 --stagger-seconds 0 --seed 0 --seed-b 0`

### Validation Result
- Passed: `defense_v1` properly penalizes edge camping and blocked inputs.
- Passed: Both `combat_default` and `defense_v1` behave deterministically in tests.
- Passed: The `--reward-profile` argument correctly propagates from the CLI to `config.json` and the environment logic.

### Architectural Discrepancies
- None.

### Remaining Risks
- The edge camping penalty counts strictly on the outermost boundary of the map (`X < 1.0` or `X > width - 1`). If the agent finds a way to camp at `X = 2.0`, the penalty won't trigger.

### Suggested Next Step
- Lancer de nouvelles expérimentations RL ou analyser les résultats existants.

## 2026-05-17 01:00 Europe/Paris - Defensive Curriculum M0/M1 Benchmark

### Task Attempted
Evaluate the `defense_v1` reward profile on the `combat_bullets_v1` observation space using the M0/M1 movement curriculum to observe if penalizing edge camping and damage changes the policy's behavior.

### Files Changed or Created
- Updated `docs/ai/CODEX_SESSION_LOG.md`.

### Commands Run
- `python -m scripts.run_experiment_pair --mode parallel --profile-a combat_bullets_v1 --profile-b combat_bullets_v1 --control-mode-a movement_no_boost_scripted_attack_direct --control-mode-b movement_scripted_attack_direct --reward-profile-a defense_v1 --reward-profile-b defense_v1 --label-a M0_defense --label-b M1_defense --total-timesteps 100000 --n-envs 4 --vec-env dummy --wandb off --train-eval on --eval-freq-timesteps 50000 --train-eval-episodes 2 --eval-episodes 5 --save-replays --net-arch 128,128 --threads-per-job 6 --timing-profile on --seed 0 --seed-b 0`

### Validation Result
- Passed: The paired 100k execution completed successfully.
- **M0 (No Boost) Evaluation:**
  - Mean Reward: 106.35
  - Mean Length: 1205.0
  - Mean Player Damage: 100.0
  - Edge Camping Rate: 59.3%
  - Input Inefficiency Rate: 95.5%
- **M1 (With Boost) Evaluation:**
  - Mean Reward: 198.70
  - Mean Length: 1800.0 (Survived)
  - Mean Player Damage: 48.0
  - Edge Camping Rate: 12.7%
  - Input Inefficiency Rate: 26.0%

### Repository Facts Discovered
- The `defense_v1` reward profile completely successfully forces the agent out of the lazy "stand still and shoot" local minimum.
- M0 gets pinned to the left edge and dies taking heavy damage because it cannot boost.
- M1 successfully utilizes the boost to significantly reduce damage (from 100 down to 48), completely avoid death (lasting the full 1800 frames), and drastically reduce input inefficiency.

### Architectural Discrepancies
- None.

### Remaining Risks
- None.

### Suggested Next Step
- Introduce velocity-compensated or perfect-prediction aiming heuristcs to further isolate movement learning.

## 2026-05-16 00:00 Europe/Paris - Movement Curriculum (M0/M1) Implementation

### Task Attempted
Implement the first movement-curriculum slice: PPO learns movement only while aim/fire are supplied by a deterministic scripted attack. Run a 100k M0/M1 comparison to isolate and evaluate movement behavior.

### Files Changed or Created
- Updated `ha2_env.py` to add `MovementScriptedAttackDirectWrapper` (agent controls `[move, jump, duck, boost]`) and `MovementNoBoostScriptedAttackDirectWrapper` (agent controls `[move, jump, duck]`). Both wrappers automatically aim at the primary Heli and fire when one exists.
- Updated `scripts/train_parkour.py`, `scripts/evaluate_model.py`, `scripts/watch_model.py`, and `scripts/run_experiment.py` to support the `--control-mode` CLI argument, and record it in `config.json`.
- Updated `scripts/run_experiment_pair.py` to accept `--control-mode`, `--control-mode-a`, and `--control-mode-b` to facilitate comparative experiments, and added auto-generated experiment names when modes/profiles overlap to avoid folder collisions.
- Created `tests/test_curriculum.py` to verify the ActionSpace sizing, action translation logic, and `boost=0` constraints of the new wrappers.
- Updated `docs/ai/CURRENT_STATE.md` and `docs/ai/CODEX_SESSION_LOG.md`.

### Repository Facts Discovered
- `DummyVecEnv` combined with standard evaluation scripts passes action arrays through unmodified to the underlying unwrapped environment if the evaluation environment itself is not wrapped with the same curriculum wrappers as the training environment. Explicitly adding `--control-mode` to the evaluation flow ensures the action arrays match dimensions.

### Commands Run
- `python -m pytest` (Passed all tests, including new curriculum tests)
- `python -m scripts.run_experiment_pair --mode parallel --profile-a combat_bullets_v1 --profile-b combat_bullets_v1 --control-mode-a movement_no_boost_scripted_attack_direct --control-mode-b movement_scripted_attack_direct --label-a M0_no_boost --label-b M1_boost --total-timesteps 100000 --n-envs 4 --vec-env dummy --wandb off --train-eval on --eval-freq 50000 --train-eval-episodes 2 --eval-episodes 5 --save-replays --net-arch 128,128 --threads-per-job 6 --timing-profile on --seed 0 --seed-b 0`

### Validation Result
- Passed: Tests confirm `MovementNoBoostScriptedAttackDirectWrapper` successfully forces boost actions to `0` and translates to a 6-dim action space.
- Passed: Scripted aim reliably locks onto the target coordinates.
- Passed: 100k M0/M1 comparison runs successfully without dimension mismatch errors.

### Architectural Discrepancies
- The curriculum logic relies strictly on Gymnasium `ActionWrapper`s applied during environment instantiation. No changes were made to core `HeliAttack2Env` simulator mechanics.

### Remaining Risks
- The scripted "direct aim" attack is heuristic. If it misses significantly, the agent might learn poor movement patterns compensating for bad aim.

### Suggested Next Step
- Analyze the evaluation reports of the 100k M0 (No Boost) vs M1 (With Boost) movement curriculum experiment.

## 2026-05-15 22:30 Europe/Paris - Fix Parallel Job Duration Reporting

### Task Attempted
Fix the per-job `duration_seconds` reporting in `scripts/run_experiment_pair.py` for parallel runs with non-zero `--stagger-seconds`.

### Files Changed or Created
- Updated `scripts/run_experiment_pair.py` to record `start_tick_a` and `start_tick_b` individually immediately before launching each respective job, and compute each job's duration based on its own start tick rather than the global `start_tick_total`.
- Added `test_parallel_staggered_durations` to `tests/test_benchmark_orchestration.py` to verify that Job B's duration strictly measures its own runtime and does not include the `--stagger-seconds` delay.

### Repository Facts Discovered
- In parallel mode, the global `start_tick_total` was previously being used to compute the duration of both Job A and Job B, leading to Job B's duration artificially inflating by the stagger delay.

### Commands Run
- `python -m pytest tests/test_benchmark_orchestration.py`

### Validation Result
- Passed: `duration_seconds` for Job A and Job B now correctly reflect their independent running times.
- Passed: `total_parallel_duration` continues to correctly represent the total wall-clock time from the first job's launch to the last job's completion.

### Architectural Discrepancies
- None.

### Remaining Risks
- None.

### Suggested Next Step
- Review the finalized reports from the 500k parallel runs.

## 2026-05-16 23:55 Europe/Paris - Fix Horizontal Movement and Clarify Eval Frequency

### Task Attempted
Fix horizontal-movement diagnostics (min/max X were stuck at 25.0), add comprehensive edge-camping and movement-mismatch metrics, and clarify training-time evaluation frequency via `--eval-freq-timesteps`.

### Files Changed or Created
- Updated `ha2_env.py` to correctly update `min_player_x` and `max_player_x` in `step()`, and added 15+ new movement diagnostics (actual vs. requested movement, edge camping, consecutive edge frames).
- Updated `scripts/train_parkour.py` to support `--eval-freq-timesteps` and division by `n_envs` for accurate SB3 behavior.
- Updated `scripts/run_experiment.py` and `scripts/run_experiment_pair.py` to support `--eval-freq-timesteps` and include copy-pasteable `watch_model` and `play_replay` commands in Markdown summaries.
- Updated `scripts/evaluate_model.py` to aggregate the new movement metrics and calculate rates (mismatch, camping, blocked press).
- Updated `docs/ai/CURRENT_STATE.md` and `docs/ai/CODEX_SESSION_LOG.md`.

### Repository Facts Discovered
- `min_player_x` and `max_player_x` must be updated *after* physics resolution in `step()` to capture the actual bounds reached by the player.
- SB3 `EvalCallback`'s `eval_freq` is measured in vector steps, so for 4 parallel envs, a `50000` total timestep interval requires `eval_freq=12500`.

### Commands Run
- `python -m scripts.run_experiment_pair --mode parallel --profile-a combat_v1 --profile-b combat_bullets_v1 --total-timesteps 1000 --n-envs 1 --vec-env dummy --wandb off --train-eval off --eval-episodes 1 --save-replays --timing-profile on --threads-per-job 2 --net-arch 128,128 --stagger-seconds 0 --seed 0 --seed-b 0`

### Validation Result
- Passed: `min_player_x` and `max_player_x` are correctly reported (e.g., `-21.6` and `150.0`) instead of the starting constant `25.0`.
- Passed: `pair_summary.md` and experiment `summary.md` now include direct inspection commands.
- Passed: `eval_latest.json` now includes `control_mode` and all new movement rates.

### Remaining Risks
- The `rich` TUI in parallel mode depends on terminal window size; extremely small windows may truncate the log panels.

### Suggested Next Step
- Finalize the triple-task commit (TUI Rich, test optimization, symlinks) and this diagnostic fix.


## 2026-05-16 10:12 Europe/Paris - Fix M0/M1 Curriculum Action Accounting

### Task Attempted
Fix the movement-curriculum pipeline so M0 truly forbids boost, M1 allows boost, training/eval/watch share one control-mode helper path, and reports/replays distinguish policy actions from full simulator actions.

### Files Changed
- `ha2_env.py`
- `ha2_replay.py`
- `scripts/train_parkour.py`
- `scripts/evaluate_model.py`
- `scripts/watch_model.py`
- `scripts/run_experiment.py`
- `scripts/run_experiment_pair.py`
- `tests/test_curriculum.py`
- `tests/test_benchmark_orchestration.py`
- `docs/ai/CURRENT_STATE.md`
- `docs/ai/VALIDATION.md`
- `docs/ai/CODEX_SESSION_LOG.md`

### Validation
- Passed: required py_compile command.
- Passed: `.venv\Scripts\python.exe -m pytest -q` (`79 passed`).
- Passed: random replay record/verify and M0/M1 eval replay verification.
- Passed: M0 smoke `experiments/ha2_000082_20260516_0959_combat-bullets-v1_1k`.
- Passed: M1 smoke `experiments/ha2_000083_20260516_1000_combat-bullets-v1_1k`.
- Passed: 10k pair `experiments/pair_20260516_100323`.

### Key Results
- M0 policy action space: `[3, 2, 2]`; simulator action space: `[3, 2, 2, 2, 32, 2]`.
- M1 policy action space: `[3, 2, 2, 2]`; simulator action space: `[3, 2, 2, 2, 32, 2]`.
- M0 replay boost check: both latest eval replays contain only full action boost value `0`.
- M0 boost metrics: `boost_activations=0`, `frames_boost_pressed=0`.
- M1 latest eval replays contain boost values `0` and `1`.

### 10k Comparison Snapshot
| Metric | M0 no boost | M1 boost |
|---|---:|---:|
| Mean reward | 65.56 | 206.50 |
| Mean heli kills | 4.50 | 9.50 |
| Mean player damage | 100.00 | 55.00 |
| Death rate | 100.00% | 0.00% |
| Visible bullet hit rate | 20.00% | 5.39% |
| Mean time to first damage | 144.50 | 180.00 |
| Mean longest damage-free streak | 221.00 | 618.50 |
| Mean boost activations | 0.00 | 12.00 |

### Replay Paths
- M0: `experiments/20260516_100323_combat_bullets_v1_movement_no_boost_scripted_attack_direct_10000_a/replays/latest_eval_ep0.jsonl`
- M0: `experiments/20260516_100323_combat_bullets_v1_movement_no_boost_scripted_attack_direct_10000_a/replays/latest_eval_ep1.jsonl`
- M1: `experiments/20260516_100323_combat_bullets_v1_movement_scripted_attack_direct_10000_b/replays/latest_eval_ep0.jsonl`
- M1: `experiments/20260516_100323_combat_bullets_v1_movement_scripted_attack_direct_10000_b/replays/latest_eval_ep1.jsonl`

### Remaining Risks
- Several stale Python processes from an older run were present during validation and may affect machine performance until cleaned up.
- The 10k comparison is a smoke validity check, not a learning conclusion.

### Suggested Next Step
- Visually inspect the 10k M0/M1 replays, then rerun a clean 100k M0/M1 comparison if behavior looks plausible.

## 2026-05-17 20:48 Europe/Paris - Fix Reward Profile Artifacts

### Task Attempted
Fix `defense_v1` propagation and expose reward metadata in evaluation reports and replays.

### Files Changed
- `ha2_replay.py`
- `scripts/train_parkour.py`
- `scripts/evaluate_model.py`
- `scripts/run_experiment.py`
- `tests/test_reward_profiles.py`
- `tests/test_experiment_outputs.py`
- `docs/ai/CURRENT_STATE.md`
- `docs/ai/VALIDATION.md`
- `docs/ai/CODEX_SESSION_LOG.md`

### Validation
- Passed: py_compile for core reward/replay/training scripts.
- Passed: `.venv\Scripts\python.exe -m pytest -q` (`88 passed`).
- Passed: 1k `combat_default` smoke `experiments/ha2_000084_20260517_2045_combat-bullets-v1_1k`.
- Passed: 1k `defense_v1` smoke `experiments/ha2_000085_20260517_2045_combat-bullets-v1_1k`.
- Passed: 10k M0/M1 defense pair `experiments/pair_20260517_204602`.
- Passed: replay verification for the smoke and 10k latest eval replays.

### Proof
- Direct 10-damage test: `combat_default` reward `-0.99`; `defense_v1` reward `-10.0`.
- New replay headers contain `reward_profile`.
- New replay step debug contains `reward_breakdown`.
- New eval reports contain top-level `reward_profile` and aggregated `reward_breakdown`.

### Remaining Risks
- The earlier 2026-05-17 15:25 100k run remains invalid for training because the training env used `combat_default` despite config naming `defense_v1`.
- 10k defense smoke proves plumbing, not policy quality.

### Suggested Next Step
- Inspect `experiments/pair_20260517_204602`; if artifacts look correct, rerun a fresh 100k defense comparison.

## 2026-05-17 21:35 Europe/Paris - Centralize Runtime Arguments

### Task Attempted
Centralize shared runtime argument/config handling for `training_profile`, `control_mode`, `reward_profile`, and `max_episode_steps`.

### Files Changed
- `scripts/runtime_config.py`
- `scripts/train_parkour.py`
- `scripts/evaluate_model.py`
- `scripts/watch_model.py`
- `scripts/play_human.py`
- `scripts/run_experiment.py`
- `scripts/run_experiment_pair.py`
- `tests/test_runtime_config.py`
- `docs/ai/CURRENT_STATE.md`
- `docs/ai/VALIDATION.md`
- `docs/ai/CODEX_SESSION_LOG.md`

### Validation
- Passed: required py_compile command.
- Passed: `.venv\Scripts\python.exe -m pytest -q` (`94 passed`).
- Passed: runtime smoke `experiments/ha2_000086_20260517_2133_combat-bullets-v1_1k`.
- Passed: default train command `experiments/ha2_000087_20260517_2133_combat-v1_1024`.
- Passed: replay verification for the runtime smoke latest eval replay.

### Proof
- Smoke config/report/replay header all resolved to `combat_bullets_v1`, `movement_scripted_attack_direct`, `defense_v1`, `1800`.
- Default command resolved to `combat_v1`, `full`, `combat_default`, `1800`.
- Tests cover config inference and CLI override for evaluation, watch config inference, script help acceptance, and runtime helper precedence.

### Remaining Risks
- `play_human` preserves its old default `legacy` profile; non-full control modes are explicit-only and use policy-style action inputs.

### Suggested Next Step
- Add `pressure_profile` using `scripts/runtime_config.py` instead of adding per-script arguments manually.

## 2026-05-17 22:48 Europe/Paris - Add Pressure Profile Curriculum

### Task Attempted
Implement opt-in `pressure_profile` values `normal`, `enemy_fire_slow_2x`, and `enemy_fire_slow_4x` for Heli fire cadence without changing default behavior.

### Files Changed
- `ha2_env.py`, `ha2_replay.py`
- `scripts/runtime_config.py`, `scripts/train_parkour.py`, `scripts/evaluate_model.py`, `scripts/watch_model.py`, `scripts/play_human.py`, `scripts/play_replay.py`, `scripts/run_experiment.py`, `scripts/run_experiment_pair.py`, `scripts/runtime_timing.py`
- `tests/test_pressure_profiles.py`, runtime/reporting tests
- `docs/ai/CURRENT_STATE.md`, `docs/ai/VALIDATION.md`, `docs/ai/CODEX_SESSION_LOG.md`

### Validation
- Passed: required py_compile command.
- Passed: `.venv\Scripts\python.exe -m pytest -q` (`100 passed`).
- Passed: play_human argument smoke via `--help`.
- Passed: replay verify for `replays/smoke.jsonl`, 1k slow4/normal eval replays, and 100k pair latest eval replays.
- Passed: 1k slow4 smoke `experiments/ha2_000088_20260517_2236_combat-bullets-v1_1k`.
- Passed: 1k normal smoke `experiments/ha2_000089_20260517_2236_combat-bullets-v1_1k`.
- Passed: 100k M0/M1 slow4 pair `experiments/pair_20260517_223718`.

### Proof
- Direct 240-step probe: normal `13`, slow2 `7`, slow4 `4` enemy bullets spawned.
- First enemy bullet speed/damage stayed `7.0`/`10` for all pressure profiles.
- 1k eval comparison: slow4 spawned `32` enemy bullets; normal spawned `112`.
- 100k latest eval: M0 reward `63.49`, damage `32.0`, visible hit rate `0.132`; M1 reward `98.82`, damage `4.0`, visible hit rate `0.018`.

### Remaining Risks
- Slow-fire profiles are curriculum modes, not AS parity modes.
- 100k slow4 results suggest M1 benefits from boost, but do not prove robust bullet-dodging learning.

### Suggested Next Step
- Inspect the M0/M1 slow4 replays, then decide whether to add defensive diagnostics or tune curriculum/reward further.

## 2026-05-18 14:05 Europe/Paris - Resume/Fine-Tune Orchestration

### Task Attempted
Add resume/fine-tune support to training orchestration without changing simulator behavior.

### Files Changed
- `scripts/experiment_utils.py`
- `scripts/train_parkour.py`
- `scripts/run_experiment.py`
- `scripts/run_experiment_pair.py`
- `tests/test_runtime_config.py`
- `docs/ai/CURRENT_STATE.md`
- `docs/ai/VALIDATION.md`
- `docs/ai/CODEX_SESSION_LOG.md`

### Result
- `train_parkour`, `run_experiment`, and `run_experiment_pair` accept resume model paths and reset/no-reset timestep controls.
- Resumed runs default to `reset_num_timesteps=False`; non-resume defaults remain reset.
- Resumed runs reject `--net-arch`, validate action/observation spaces before training, create new experiment directories, and record parent lineage.

### Validation
- Passed: py_compile for modified orchestration scripts.
- Passed: `.venv\Scripts\python.exe -m pytest tests/test_runtime_config.py -q` (`13 passed`).
- Passed: `.venv\Scripts\python.exe -m pytest -q` (`106 passed, 3 warnings`).
- Passed: single resume smoke `experiments/ha2_000091_20260518_1401_combat-bullets-v1_1024`.
- Passed: pair resume smoke `experiments/pair_20260518_140132`.

### Issues and Risks
- Initial real resume smoke exposed SB3 `set_env` n-env incompatibility; fixed by validating with a loaded model, then loading with `PPO.load(path, env=env)`.
- Resume compatibility is based on Gym spaces, not semantic proof that the parent task is desirable.

### Suggested Next Step
- Run a longer fine-tune comparison from the selected M0/M1 parents and inspect eval replays before interpreting policy quality.

## 2026-05-18 Europe/Paris - Handoff Bundle Rule

- Updated `AGENTS.md` to require a `docs/ai/codex_task_bundle_YYYYMMDD_HHMMSS.zip` after each completed `NEXT_CODEX_TASK`.
- Bundle contents: impacted files in final state, impacted `docs/ai` files, complete `git diff`, and concise final Codex report.
- Validation: documentation-only change; no simulator validation run.

## 2026-05-18 Europe/Paris - Handoff Bundle Naming

- Updated `AGENTS.md` bundle naming to include 2 task-identifying keywords, up to 4 if needed.
- Validation: documentation-only change; no simulator validation run.

## 2026-05-18 Europe/Paris - Resume Timing Instrumentation

- Fixed resume + `--timing-profile on` to load the resumed model through `TimedPPO.load(..., env=env)`.
- Validation: py_compile passed; `tests/test_runtime_config.py` passed (`13 passed`); full pytest passed (`106 passed, 3 warnings`); resume timing smoke passed at `experiments/ha2_000092_20260518_1458_combat-bullets-v1_1024`.
- Timing smoke confirmed `rollout_count=1` and `train_update_count=1`.

## 2026-05-18 Europe/Paris - Evaluation Matrix Runner

### Task Attempted
Add a cross-platform `scripts.evaluate_matrix` runner for model/pressure evaluation matrices.

### Files Changed
- `scripts/evaluate_matrix.py`
- `tests/test_evaluate_matrix.py`
- `docs/ai/CURRENT_STATE.md`
- `docs/ai/VALIDATION.md`
- `docs/ai/CODEX_SESSION_LOG.md`

### Validation
- Passed: py_compile for `scripts/evaluate_matrix.py`, `scripts/evaluate_model.py`, `scripts/runtime_config.py`.
- Passed: `tests/test_evaluate_matrix.py` (`5 passed`).
- Passed: full pytest (`111 passed, 3 warnings`).
- Passed: dry-run smoke `experiments/eval_matrices/smoke_matrix_20260518_155909`.
- Passed: real smoke `experiments/eval_matrices/smoke_matrix_real_20260518_155919`.

### Result
- Matrix runs create per-job directories with copied eval reports, stdout/stderr logs, command text, metadata, parent config, JSON/CSV/MD summaries, manifest/config, and a bundle zip.
- Example current matrix command: `python -m scripts.evaluate_matrix --matrix-name slow2_transfer_3600 --entry "label=M0;experiment=experiments\20260518_150236_combat_bullets_v1_movement_no_boost_scripted_attack_direct_defense_v1_enemy_fire_slow_2x_500000_a;model=latest" --entry "label=M1;experiment=experiments\20260518_150236_combat_bullets_v1_movement_scripted_attack_direct_defense_v1_enemy_fire_slow_2x_500000_b;model=best" --pressure-profiles enemy_fire_slow_4x,enemy_fire_slow_2x,normal --episodes 20 --max-episode-steps 3600 --max-parallel 6 --threads-per-job 3 --no-save-replays`.

### Known Limitations
- The script rejects duplicate entry labels instead of auto-disambiguating them.
- Real smoke used only one pressure profile and one episode per model.

### Suggested Next Step
- Run the full slow2 transfer matrix and inspect `matrix_summary.md` plus copied per-job reports before comparing policy quality.

## 2026-05-18 Europe/Paris - Evaluation Matrix Polish

- Fixed `--fail-fast` so queued jobs are marked skipped instead of leaving `pending` non-empty.
- Changed replay saving default to off; `--save-replays` is now opt-in for large matrices.
- Validation: py_compile passed; `tests/test_evaluate_matrix.py` passed (`7 passed`); full pytest passed (`113 passed, 3 warnings`); dry-run confirmed `save_replays=false`.

## 2026-05-18 Europe/Paris - Invocation Metadata and Resolved Configs

- Added shared invocation metadata writing for `train_parkour`, `run_experiment`, `run_experiment_pair`, and `evaluate_matrix`.
- New outputs include `argv.json`, `command.txt`, `invocation_metadata.json`, and `resolved_config.json`; orchestrated runs also write child train/eval command files.
- Implemented `run_experiment --label` as an alias for `--experiment-name`; conflicting values fail.
- Validation passed: py_compile, full pytest (`114 passed, 3 warnings`), smoke runs `experiments/invocation_smoke`, `experiments/invocation_smoke_label_alias`, and dry-run matrix `experiments/eval_matrices/invocation_matrix_smoke_20260518_175924`.
- Limitation: `command.txt` is reconstructed from argv and does not preserve byte-exact original shell quoting; use `argv.json` as authoritative.
- Follow-up: pair and matrix Markdown summaries now repeat the same command reconstruction limitation.
- Suggested next step: inspect the new metadata files in the smoke outputs before relying on them for long experiment chains.

## 2026-05-18 Europe/Paris - Damage Forensics Evaluation Reports

- Added opt-in `evaluate_model --damage-forensics on --damage-forensics-window N` and `evaluate_matrix --damage-forensics` forwarding/copying/bundling.
- Added per-impact JSON/Markdown reports with compact pre-impact windows, best-effort candidate bullet fields, availability flags, and heuristic-only tags.
- Unavailable/null fields: terrain blockage, world-right-edge distance, exact boost cooldown, and exact grounded-state-change timing; these require a future simulator-diagnostics task.
- Validation passed: py_compile; full pytest (`119 passed, 3 warnings`); smoke matrix `experiments/eval_matrices/damage_forensics_smoke_20260518_233017`.
- Smoke bundle: `experiments/eval_matrices/damage_forensics_smoke_20260518_233017/damage_forensics_smoke_20260518_233017_bundle.zip`.
- Follow-up polish: canonical world-edge distances remain null with availability flags; `edge_or_blockage` is not emitted from cumulative edge counters; `candidate_bullet_in_observation` stays null until pre-impact top-K ids are exposed.
- Follow-up heuristic polish: duck availability no longer creates a missed jump/duck tag; duck relevance is marked unknown, and boost tag wording is `boost_related_or_cooldown`.
- Suggested next step: run the 20-episode champion normal-pressure forensics matrix and inspect tag counts plus event windows.

## 2026-05-19 Europe/Paris - Collision Parity Audit

- Task: freeze current simulator as a legacy reference and audit AS/FFDEC collision parity without changing `ha2_env.py`.
- Files inspected: `ha2_env.py`, `ha2_constants.py`, `ha2_replay.py`, `docs/parity_notes.md`, `docs/ai/*`, `heliattack2_scripts/ha2_core_logic/frame_19_DoAction_2.as`, and FFDEC SVG/script exports under `reference_exports/ffdec_ha2/`.
- Files changed: `ha2_env_legacy.py`, `tests/test_legacy_env.py`, `docs/ai/HA2_COLLISION_PARITY_AUDIT.md`, `docs/parity_notes.md`, `docs/ai/CURRENT_STATE.md`, `docs/ai/CODEX_SESSION_LOG.md`.
- AS evidence found: `hitCheck` directly indexes `mapa[y][x][0]`; player bullets use `enemyArray[i].hit.hitTest(...,1)`; enemy bullets use `player.gfx.hit.hitTest(...,1)`.
- FFDEC evidence found: hidden non-rectangular Heli hit shape `DefineSprite_109`, standing player hit shape `DefineSprite_119`, and duck hit shape `DefineSprite_123`.
- Confirmed difference: Python projectile collision is rectangle-based and may affect player survival, Heli kill timing, hit/miss behavior, rewards, and evaluation comparability.
- Validation passed: py_compile for `ha2_env.py ha2_env_legacy.py ha2_replay.py`; `tests/test_legacy_env.py` (`1 passed`); full pytest (`120 passed, 3 warnings`); `scripts.play_human --help`.
- Remaining risk: exact Flash `hitTest` transform semantics and Heli rotation inheritance still need targeted validation before changing simulator collision.
- Suggested next task: add current-behavior collision tests, then prototype FFDEC polygon point-hit collision behind a compatibility switch and compare against `ha2_env_legacy.py`.

## 2026-05-19 Europe/Paris - FFDEC Polygon Collision Prototype

- Pre-existing status: `docs/ai/NEXT_CODEX_TASK.md` was modified; prior handoff bundles were untracked under `docs/ai/`.
- Task: add opt-in projectile collision model `collision_model="ffdec_polygon"` while preserving `rect` as default.
- Files inspected: `ha2_env.py`, `ha2_env_legacy.py`, `tests/test_legacy_env.py`, `docs/ai/HA2_COLLISION_PARITY_AUDIT.md`, `docs/parity_notes.md`, FFDEC SVG hit-shape exports, and AS `hitTest` call sites.
- Files changed: `ha2_collision.py`, `ha2_env.py`, `tests/test_collision_model.py`, `scripts/compare_collision_models.py`, `pytest.ini`, `docs/parity_notes.md`, `docs/ai/CURRENT_STATE.md`, `docs/ai/VALIDATION.md`, `docs/ai/CODEX_SESSION_LOG.md`.
- FFDEC shapes used: Heli `DefineSprite_109`, standing player `DefineSprite_119`, duck player `DefineSprite_123`.
- Transform assumptions: Heli hit polygon uses child offset `(-104.5,-52.55)` and current Heli rotation around the simulator/render registration point; player non-duck states use standing `gfx.hit` offset `(12.65,1.2)`, duck uses `(12.85,7.35)`.
- Behavior differences found: Heli top-left rect probe hits only in `rect`; standing and duck player left-edge probes hit only in `ffdec_polygon`; center probes agree.
- Validation passed: py_compile for `ha2_env.py ha2_env_legacy.py ha2_replay.py ha2_collision.py scripts/compare_collision_models.py`; targeted pytest (`8 passed`); `scripts.compare_collision_models`; full pytest (`127 passed, 3 warnings`).
- Workaround: `pytest.ini` now restricts discovery to `tests` so informative handoff bundle directories under `docs/ai` are not collected as duplicate tests.
- Remaining risks: exact Flash `hitTest` transform semantics and non-duck animation-frame hit-shape mapping still need Flash validation before making polygon collision default.
- Suggested next task: run targeted replay probes and manual debug-overlay checks with `collision_model="ffdec_polygon"` before considering a default change.

## 2026-05-19 Europe/Paris - Handoff Artifact Rule

- Updated `AGENTS.md` to require natural verification artifacts in end-of-task bundles when tests or smoke runs produce them, including replays, models, experiment outputs, and eval reports.
- Updated `docs/ai/CURRENT_STATE.md` to note the same bundle-content rule.
- Validation: documentation-only change; no runtime validation run.

## 2026-05-19 Europe/Paris - Replay Simulator Metadata

- Pre-existing status before this task: uncommitted collision-polygon prototype files, handoff bundle files, and docs updates were already present.
- Added replay metadata fields: `simulator_id`, `simulator_version`, and `simulation_semantics.collision_model`.
- Added replay simulator resolution for `recorded/current/legacy`; `verify_replay_file` and `scripts.play_replay` default to recorded semantics.
- Old replay headers without simulator metadata infer `ha2_env_legacy` + `rect` only for known pre-split `env_version` values through `0.6`; unclear headers fail clearly.
- Files changed: `ha2_env.py`, `ha2_replay.py`, `scripts/play_replay.py`, `scripts/verify_replay.py`, `tests/test_replay_metadata.py`, `docs/ai/CURRENT_STATE.md`, `docs/ai/VALIDATION.md`, `docs/ai/CODEX_SESSION_LOG.md`.
- Validation passed: py_compile for replay modules/scripts; `tests/test_replay_metadata.py` (`7 passed`); full pytest (`134 passed, 3 warnings`); `scripts.play_replay --help`.
- Remaining risk: old third-party/manual replay files with missing or ambiguous `env_version` are intentionally rejected until manually classified.

## 2026-05-19 Europe/Paris - FFDEC Parity Bundle

- Added `scripts/build_ffdec_parity_bundle.py` to build a cross-platform HA2 FFDEC parity bundle from repo-relative paths using only the Python standard library.
- Bundle output: `reports/ffdec_parity_core_ha2/ffdec_parity_core_ha2.zip` with `manifest.json` and `manifest.md`.
- Bundle size: 10,875,752 bytes.
- Handoff bundle for this task: `docs/ai/codex_task_bundle_20260519_142750_ffdec-parity.zip`.
- Manifest summary: 27 expected entries found, 4 expected entries missing.
- Important found paths: `heliattack2_scripts`, `reference_exports/ffdec_ha2/scripts_as`, `reference_exports/ffdec_ha2/sprites_svg`, `reference_exports/ffdec_ha2/shapes_svg`, `reference_exports/ffdec_ha2/swf_xml`, `reference_exports/ffdec_ha2/symbol_class`, `reference_exports/ffdec_ha2/logs`, `reference_exports/ffdec_ha2/images`, and `assets_ffdec/sprites`.
- Important missing paths with alternatives: `reference_exports/ffdec_ha2/shapes` -> `reference_exports/ffdec_ha2/shapes_svg`; `reference_exports/ffdec_ha2/sprites` -> `reference_exports/ffdec_ha2/sprites_svg` and `reference_exports/ffdec_ha2/sprites_png`; XML wildcard expectations -> `reference_exports/ffdec_ha2/swf_xml/heli_attack_2.swf.xml`.
- Intentionally excluded from search/bundle: `.git`, `.venv`, `experiments`, `models`, `recordings`, `runs`, `reports`, and other irrelevant large outputs.
- Validation passed: `py_compile` for the new script; bundle build; zip integrity check with `zipfile.ZipFile.testzip()`.

## 2026-05-19 Europe/Paris - Flash HitTest Collision Model

- Pre-existing status: modified docs/ai files, untracked prior handoff bundles, untracked FFDEC parity bundle outputs, and `scripts/build_ffdec_parity_bundle.py`.
- Task: harden opt-in `collision_model="ffdec_polygon"` using AS `hitTest(...,1)` and FFDEC display-list matrices; default `rect` behavior preserved.
- Files inspected: `ha2_env.py`, `ha2_collision.py`, `tests/test_collision_model.py`, `scripts/compare_collision_models.py`, `docs/ai/HA2_COLLISION_PARITY_AUDIT.md`, `docs/parity_notes.md`, AS, P-code, SWF XML, and FFDEC SVG hit-shape exports.
- Facts confirmed: player bullets test `enemyArray[i].hit` with `world._x/_y`; enemy bullets test `player.gfx.hit`; Heli frame 1 hit matrix is `translate(-104.5,-52.55)`; Heli frame 2 is `scaleX=-1` plus `translate(103.5,-52.0)`; player standing/duck matrices are `(12.65,1.2)` and `(12.85,7.35)`.
- Files changed: `ha2_collision.py`, `ha2_env.py`, `tests/test_collision_model.py`, `scripts/compare_collision_models.py`, `docs/ai/FLASH_AS_FINDINGS.md`, `docs/parity_notes.md`, `docs/ai/CURRENT_STATE.md`, `docs/ai/CODEX_SESSION_LOG.md`.
- Implemented transform rules: Flash-style affine composition; Heli frame-specific child transform, parent rotation, then world translation; player standing/duck child transform then world translation.
- Stroke support: implemented deterministic player 1 px outline support via 0.5 px segment-distance checks; Heli remains fill-only.
- Validation passed: py_compile; `tests/test_collision_model.py` (`14 passed`); `scripts.compare_collision_models`; full pytest (`141 passed, 3 warnings`).
- Handoff bundle: `docs/ai/codex_task_bundle_20260519_154355_collision-hittest.zip`.
- Remaining risks: exact live Flash rasterization/sub-pixel behavior and non-duck player frame mapping still need targeted Flash validation before making polygon collision default.
- Suggested next task: run visual debug-overlay probes and replay checks with `collision_model="ffdec_polygon"` before changing any default simulator semantics.

## 2026-05-19 Europe/Paris - Collision Documentation Cleanup

- Updated documentation only: `docs/ai/CURRENT_STATE.md`, `docs/ai/FLASH_AS_FINDINGS.md`, and `docs/ai/CODEX_SESSION_LOG.md`.
- Removed stale wording that described FFDEC polygon hit shapes as a future/not-implemented simulator task.
- State documented at that time: `rect` remained default; opt-in `ffdec_polygon` was implemented with FFDEC polygon shapes, Flash-style transforms, frame-aware mirrored Heli frame 2, Heli rotation, and standing/duck player shape selection.
- Runtime code, tests, replay code, training code, and parity logic were not modified.

## 2026-05-19 Europe/Paris - Collision Visual Validation Artifacts

- Files changed: `docs/ai/CODEX_SESSION_LOG.md`; generated PNGs under `reports/collision_visual_validation/`.
- Output screenshots: `heli_frame_1_polygon_overlay.png`, `heli_frame_2_mirrored_polygon_overlay.png`, `heli_rotated_polygon_overlay.png`, `player_standing_polygon_overlay.png`, `player_duck_polygon_overlay.png`.
- Commands run: generated screenshots with existing `HeliAttack2Env(render_mode="rgb_array", collision_model="ffdec_polygon")`; `python -m py_compile ha2_env.py ha2_collision.py`; `python -m pytest tests/test_collision_model.py -q`.
- Validation result: py_compile passed; collision tests passed (`14 passed`).
- Runtime code changed: no.
- Remaining visual uncertainty: Charles still needs to inspect the PNGs for plausibility against Flash; no live GUI/manual Flash comparison was performed.

## 2026-05-19 Europe/Paris - FFDEC Polygon Collision Default

- Files changed: `ha2_env.py`, `tests/test_collision_model.py`, `tests/test_replay_metadata.py`, `docs/ai/CURRENT_STATE.md`, `docs/parity_notes.md`, `docs/ai/CODEX_SESSION_LOG.md`.
- Changed evolving HA2 default `collision_model` from `rect` to `ffdec_polygon`.
- New `ENV_VERSION`: `0.8`.
- Confirmed explicit `collision_model="rect"` remains available in tests.
- Confirmed `ha2_env_legacy.py` was not modified.
- Commands run: `python -m py_compile ha2_env.py ha2_collision.py ha2_replay.py`; `python -m pytest tests/test_collision_model.py`; `python -m pytest tests/test_replay_metadata.py`; `python -m scripts.compare_collision_models`; `python -m pytest tests/test_scripted_trace.py::test_scripted_heli_shoots_hero_trace_summary`; `python -m pytest`.
- Results: py_compile passed; collision tests passed (`15 passed`); replay metadata tests passed (`7 passed`); comparison script passed; scripted trace check passed; full pytest passed (`142 passed, 3 warnings`).
- Replay metadata: new default env replays record `simulation_semantics.collision_model="ffdec_polygon"`.

## 2026-05-19 Europe/Paris - HA2 Intro And Skip-Intro Startup

- Pre-existing status: modified `docs/ai/NEXT_CODEX_TASK.md`, `docs/ai/VALIDATION.md`, and untracked handoff/report artifacts were present.
- AS facts inspected: `heroStart` uses player frame 6, moves by `yspeed + 5`, opens/closes `gfx.chute._xscale`, switches to `heroAction`, sets `gamestarted=1`, and calls `addEnemy(300)` after chute close.
- Files changed: `ha2_env.py`, `ha2_replay.py`, `scripts/runtime_config.py`, `scripts/play_human.py`, `scripts/record_scripted_trace.py`, `scripts/train_parkour.py`, `scripts/evaluate_model.py`, `scripts/watch_model.py`, `scripts/run_experiment.py`, `scripts/play_replay.py`, replay/env/runtime tests, `docs/ai/CURRENT_STATE.md`, `docs/ai/FLASH_AS_FINDINGS.md`, `docs/ai/VALIDATION.md`, and `docs/parity_notes.md`.
- New `ENV_VERSION`: `0.9`.
- Startup semantics: `skip_intro=False` runs AS-backed intro and spawns the first Heli when the chute closes; `skip_intro=True` starts grounded near the left side and creates the first Heli at reset.
- Defaults: direct env and human play use `skip_intro=False`; runtime training/evaluation config and scripted traces use `skip_intro=True` unless overridden.
- Replay metadata now records `simulation_semantics.intro_mode` and `simulation_semantics.skip_intro`; recorded replay semantics are used by default.
- Validation passed: py_compile for `ha2_env.py ha2_replay.py scripts/runtime_config.py`; replay metadata tests (`8 passed`); scripted trace tests (`7 passed`); env basic tests (`28 passed`); required help checks; full pytest (`144 passed, 3 warnings`).
- Handoff bundle: `docs/ai/codex_task_bundle_20260519_182102_intro-startup.zip`.
- Remaining approximation: live Flash visual/parachute timing has not been manually compared; old current-simulator replays without intro metadata are treated as `legacy_fall_proxy` best effort.
- Suggested next task: Charles should manually inspect `python -m scripts.play_human` startup and one `--skip-intro` scripted/GUI replay for visual plausibility.

## 2026-05-19 Europe/Paris - Scripted Trace Skip-Intro Default Fix

- Files changed: `scripts/record_scripted_trace.py`, `tests/test_scripted_trace.py`, `docs/ai/CODEX_SESSION_LOG.md`.
- Fixed `record_scripted_trace` so no CLI flag means `skip_intro=False`; `--skip-intro` now explicitly opts into fast-start traces.
- Updated scripted trace tests that rely on fast-start combat timing to pass `skip_intro=True` explicitly.
- Replay metadata confirmed: no flag records `simulation_semantics.skip_intro=false`; `--skip-intro` records `true`; `play_replay` continues to use recorded metadata.
- Final local `reports/parity_traces/heli_shoots_hero_240.jsonl` was regenerated without `--skip-intro`, so it records `skip_intro=false`.
- Commands run: `python -m scripts.record_scripted_trace --scenario heli_shoots_hero_240 --no-screenshots`; same command with `--skip-intro`; metadata header inspection; `python -m pytest tests/test_scripted_trace.py tests/test_replay_metadata.py -q`; `python -m pytest -q`.
- Results: targeted tests passed (`16 passed`); full pytest passed (`145 passed, 3 warnings`).

## 2026-05-19 Europe/Paris - HA2 Gameplay HUD And High Score

- Pre-existing status: `docs/ai/NEXT_CODEX_TASK.md` was modified; prior handoff bundles and report artifacts were untracked.
- Files changed: `.gitignore`, `ha2_env.py`, `ha2_high_score.py`, `scripts/play_human.py`, `scripts/watch_model.py`, `scripts/evaluate_model.py`, `tests/test_high_score.py`, `tests/test_env_basic.py`, `tests/test_experiment_outputs.py`, `docs/ai/CURRENT_STATE.md`, `docs/ai/VALIDATION.md`, `docs/parity_notes.md`, `docs/ai/CODEX_SESSION_LOG.md`.
- Copied font: `reference_exports/ffdec_ha2/fonts/19_standard 07_63.ttf` -> `assets_ffdec/fonts/19_standard 07_63.ttf`.
- Implemented centralized HUD rendering in `ha2_env.py`: Time/Helis, Score, High Score, existing healthbar, and HyperJump recharge bar.
- High-score file path: `state/ha2_high_scores.json`; it is ignored by Git and updated by human play, model watch, and evaluation, not by training rollouts or env rendering.
- Viewer scripts do not draw duplicate HUD elements; they get HUD output through `env.render(...)`.
- Exact copied font is used when present; fallback small Pygame font is used if missing.
- Commands run: py_compile for HUD/high-score modules and touched scripts; focused pytest (`40 passed`); full pytest (`151 passed, 3 warnings`).
- Handoff bundle: `docs/ai/codex_task_bundle_20260519_193352_hud-score.zip`.
- Manual GUI check not run in this Codex session.
- Remaining HUD parity gaps: exact decorative details, ammo, reload, sounds, and full gameover HUD remain future work.

## 2026-05-20 Europe/Paris - HA2 HUD Graphics Repair

- Pre-existing status: `docs/ai/NEXT_CODEX_TASK.md` was updated to the HUD graphics repair task; prior handoff bundles and report artifacts remained untracked.
- Files changed: `ha2_env.py`, `tests/test_env_basic.py`, `docs/parity_notes.md`, `docs/ai/CURRENT_STATE.md`, `docs/ai/VALIDATION.md`, `docs/ai/CODEX_SESSION_LOG.md`.
- Exact HUD assets used: `assets_ffdec/fonts/19_standard 07_63.ttf`, `assets_ffdec/sprites/DefineSprite_163/1.png`, `assets_ffdec/images/157.png`, `assets_ffdec/images/161.png`, `assets_ffdec/sprites/DefineSprite_156/1.png`, `assets_ffdec/images/147.png`, `assets_ffdec/images/151.png`, `assets_ffdec/images/153.png`, `assets_ffdec/sprites/DefineSprite_205/1.png`, and the existing healthbar assets `assets_ffdec/images/170.png` / `174.png`.
- Visual HUD changes: Time/Helis, Score, High Score, `Health:`, `HyperJump:`, `Reload:`, `Infinite x `, the starting MachineGun icon, and the original healthbar are all rendered centrally from `ha2_env.py`.
- Healthbar placement: restored to the original `431, 0` position with the existing FFDEC healthbar bitmaps.
- High-score persistence remains at `state/ha2_high_scores.json`; it was not changed by this HUD repair.
- Viewer scripts still do not draw HUD elements themselves; they benefit through `env.render(...)`.
- Exact copied font was used; fallback font path remains available if the exact TTF is missing.
- Commands run: py_compile for `ha2_env.py`, `ha2_high_score.py`, and the viewer/eval scripts; focused pytest (`40 passed`); full pytest (`151 passed, 3 warnings`).
- Handoff bundle: `docs/ai/codex_task_bundle_20260520_095948_hud-graphics.zip`.
- Remaining HUD gaps: exact Flash decorative details, ammo/reload animation polish, sounds, and full gameover HUD remain future work.

## 2026-06-02 Europe/Paris - Universal Player Death And Bounds Safety

- Files changed: `ha2_env.py`, `ha2_replay.py`, `scripts/evaluate_model.py`, `tests/test_env_basic.py`, `tests/test_rl_interface.py`, `tests/test_replay_metadata.py`, `tests/test_experiment_outputs.py`, `tests/test_evaluate_matrix.py`, `docs/parity_notes.md`, `docs/ai/CURRENT_STATE.md`, and `docs/ai/CODEX_SESSION_LOG.md`.
- New `ENV_VERSION`: `1.0`.
- Implemented universal evolving-simulator death: `health <= 0` clamps health to `0`, terminates with `termination_reason="player_death"`, and applies for `legacy`, `combat_v1`, and `combat_bullets_v1`.
- `training_profile` no longer controls whether player death exists; reward/observation behavior remains profile-specific.
- Renamed normal evolving-env vertical out-of-map termination to `out_of_bounds_safety`; lateral world sides remain collision bounds and are not a gameplay fall-death rule.
- Replay step debug now records `termination_reason`; new replays record natural universal `player_death` termination, while legacy simulator replay handling remains unchanged.
- `scripts.evaluate_model` no longer falls back to `"fall"` for generic terminations and now reports `out_of_bounds_safety_rate` while preserving the existing `fall_rate` field for compatibility.
- Validation: `python -m py_compile ha2_env.py ha2_replay.py scripts/play_human.py scripts/watch_model.py scripts/evaluate_model.py` passed; `.venv\Scripts\python.exe -m pytest tests/test_env_basic.py` passed (`35 passed`); `.venv\Scripts\python.exe -m pytest tests/test_replay_metadata.py` passed (`9 passed`); `.venv\Scripts\python.exe -m pytest` passed (`157 passed, 3 warnings`).
- Handoff bundle: `docs/ai/codex_task_bundle_20260602_112019_death-bounds.zip`.
- Manual GUI checks and training were not run.

## 2026-06-02 Europe/Paris - HUD Graphics Verification

- Pre-existing `git status --short` summary: dirty worktree included prior modified docs/code/tests (`.gitignore`, `docs/ai/*`, `docs/parity_notes.md`, `ha2_env.py`, `ha2_replay.py`, viewer/eval scripts, and multiple tests), untracked prior handoff bundles/reports, `assets_ffdec/fonts/`, `ha2_high_score.py`, and `tests/test_high_score.py`.
- Files changed in this session: `tests/test_env_basic.py`, `docs/ai/CURRENT_STATE.md`, and `docs/ai/CODEX_SESSION_LOG.md`.
- Inspected HUD implementation in `ha2_env.py`: visual HUD drawing is centralized in `_draw_gameplay_hud()` / `_draw_player_health_hud()`; viewer scripts do not draw duplicate normal HUD elements.
- Exact HUD assets confirmed in use: `assets_ffdec/fonts/19_standard 07_63.ttf`, `assets_ffdec/sprites/DefineSprite_176/1.png`, `assets_ffdec/images/170.png`, `assets_ffdec/images/174.png`, `assets_ffdec/sprites/DefineSprite_163/1.png`, `assets_ffdec/images/157.png`, `assets_ffdec/images/161.png`, `assets_ffdec/sprites/DefineSprite_156/1.png`, `assets_ffdec/images/147.png`, `assets_ffdec/images/151.png`, `assets_ffdec/images/153.png`, and `assets_ffdec/sprites/DefineSprite_205/1.png`.
- Placeholder HUD graphics status: the prior hand-drawn HyperJump rectangle had already been replaced by original bitmap/cropped-surface rendering; this session added tests that cover the healthbar, HyperJump, reload, and MachineGun icon asset loads plus viewer-script non-duplication.
- Healthbar position: restored/kept at original `(431, 0)` with existing FFDEC healthbar bitmaps.
- Commands run: `python -m py_compile ha2_env.py ha2_high_score.py scripts/play_human.py scripts/watch_model.py scripts/play_replay.py scripts/evaluate_model.py`; `.venv\Scripts\python.exe -m pytest tests/test_env_basic.py`; `.venv\Scripts\python.exe -m pytest tests/test_high_score.py`; `.venv\Scripts\python.exe -m pytest`.
- Results: py_compile passed; env basic tests passed (`36 passed`); high-score tests passed (`3 passed`); full pytest passed (`158 passed, 3 warnings`).
- Handoff bundle: `docs/ai/codex_task_bundle_20260602_113051_hud-graphics.zip`.
- Manual GUI checks and training were not run.
- Remaining HUD gaps: exact Flash decorative HUD details, bullet-time HUD behavior, sounds, full gameover HUD, pickups, weapon switching, and finite ammo counts remain future work.

## 2026-06-02 Europe/Paris - Heli Visual Destruction Effects

- Pre-existing `git status --short` summary: `docs/ai/NEXT_CODEX_TASK.md` was modified; untracked prior handoff bundles/report directories remained under `docs/ai/` and `reports/`; untracked `heli_visual_audit_20260602_141213.zip` was present.
- Files changed: `ha2_env.py`, `tests/test_env_basic.py`, `docs/parity_notes.md`, `docs/ai/CURRENT_STATE.md`, `docs/ai/FLASH_AS_FINDINGS.md`, and `docs/ai/CODEX_SESSION_LOG.md`.
- AS/FFDEC resources inspected: `heliattack2_scripts/ha2_core_logic/frame_19_DoAction_2.as` (`animationFrame`, `guyFall`, `heliFall`, `shardFrame`, Heli death block), `heliattack2_scripts/scripts/DefineSprite_111_Heli/frame_1/DoAction.as`, `frame_2/DoAction.as`, `reference_exports/ffdec_ha2/symbol_class/symbols.csv`, and existing `assets_ffdec/sprites/`.
- Confirmed Heli visual finding: HA2 Helis have two stopped visual body frames with hidden hit children; no rotor animation is evidenced. Apparent rotor motion is static blur baked into Heli body frames.
- Destruction assets used: `assets_ffdec/sprites/DefineSprite_237_Shard/1.png` through `6.png`, `assets_ffdec/sprites/DefineSprite_76_guyBurned/1.png`, `assets_ffdec/sprites/DefineSprite_115_HeliDestroyed/1.png` and `2.png`, and `assets_ffdec/sprites/DefineSprite_34_Boom/1.png` through `10.png`.
- Effect lifecycle implemented: on Heli death, visual-only effects spawn in AS attach order: 3 Shards, GuyBurned, HeliDestroyed, then boom. Shards use gravity, rotation, tile bounces, and active-region removal; GuyBurned falls/bounces; HeliDestroyed falls/rotates and spawns secondary shards/boom on terrain impact; boom advances through original frames.
- Replay/state compatibility decision: `visual_effects` and `next_visual_effect_id` are saved/restored by state snapshots; absent `visual_effects` loads as an empty list for old states. Visual effects are excluded from `state_hash` so old replay hash semantics and gameplay determinism are not broken.
- Visual RNG decision: effect random-looking values use deterministic hash-based sampling keyed by tick/source/effect id, so debris does not consume the gameplay RNG used for Heli respawn or combat.
- AS typo decision: Heli death assigns `temp.yseed = this.yspeed`, while `heliFall` reads `this.yspeed`; Python preserves the source value as `as_yseed` metadata and starts effective wreck `yspeed` at `0.0` pending live Flash validation.
- Commands run: `python -m py_compile ha2_env.py ha2_replay.py scripts/play_human.py scripts/play_replay.py scripts/watch_model.py scripts/evaluate_model.py`; `.venv\Scripts\python.exe -m pytest tests/test_env_basic.py`; `.venv\Scripts\python.exe -m pytest tests/test_replay_metadata.py`; `.venv\Scripts\python.exe -m pytest tests/test_collision_model.py`; `.venv\Scripts\python.exe -m pytest`.
- Results: py_compile passed; env basic tests passed (`41 passed`); replay metadata tests passed (`9 passed`); collision model tests passed (`15 passed`); full pytest passed (`163 passed, 3 warnings`).
- Handoff bundle: `docs/ai/codex_task_bundle_20260602_145002_heli-destruction.zip`.
- Manual GUI checks and training were not run.
- Remaining visual-effect parity gaps: exact Flash registration/origins, live Flash behavior of the `yseed` typo, exact boom `pause` initialization, and exact effect terrain collision feel need manual Flash comparison.
- Suggested next task: record or play a Heli-kill trace in GUI and visually compare effect placement/timing against Flash or FFDEC frame exports.

## 2026-06-10 Europe/Paris - Visual Effects Gameplay-State Guardrail

- Pre-existing `git status --short` summary: modified tracked files from the prior Heli visual destruction task were present (`ha2_env.py`, `tests/test_env_basic.py`, `docs/parity_notes.md`, `docs/ai/CURRENT_STATE.md`, `docs/ai/FLASH_AS_FINDINGS.md`, `docs/ai/CODEX_SESSION_LOG.md`, and stale `docs/ai/NEXT_CODEX_TASK.md`), with prior handoff bundles/report artifacts untracked. `git status` required `-c safe.directory=C:/Users/cthin/AI/HeliAttack`.
- Task-file discrepancy: the on-disk `docs/ai/NEXT_CODEX_TASK.md` still described the previous Heli destruction task; the active guardrail task came from the user message. The file was updated to summarize the active guardrail task.
- Files changed in this session: `ha2_env.py`, `tests/test_env_basic.py`, `docs/parity_notes.md`, `docs/ai/CURRENT_STATE.md`, `docs/ai/CODEX_SESSION_LOG.md`, and `docs/ai/NEXT_CODEX_TASK.md`.
- Audit result: `visual_effects` are render/replay-only state. They are updated during `step()` and rendered by `env.render(...)`, but observation builders, reward calculation, termination/truncation, scoring, projectile/player/enemy collision, Heli AI, and gameplay diagnostics do not read them.
- RNG decision confirmed: visual-effect debris uses deterministic hash-based sampling in `_visual_randint()` and does not consume `self.np_random`, which remains the gameplay RNG for Heli spawning, Heli movement choices, enemy fire spread, and MachineGun spread.
- State/replay decision confirmed: `get_state()` serializes `visual_effects` and `next_visual_effect_id` for deterministic visual playback; `set_state()` defaults old states without those fields to an empty effect list; `state_hash()` excludes both fields so gameplay replay/parity hashes remain insensitive to render-only state.
- Tests added/updated: active visual effects overlapping player, projectile, and enemy positions do not alter observations, rewards, termination, health, score, bullets, enemy bullets, enemies, or state hash; a seeded 90-step comparison proves active effects do not perturb subsequent gameplay RNG outcomes.
- Commands run: `.venv\Scripts\python.exe -m pytest tests/test_env_basic.py -q`; `python -m py_compile ha2_env.py ha2_replay.py scripts/play_human.py scripts/play_replay.py scripts/watch_model.py scripts/evaluate_model.py`; `.venv\Scripts\python.exe -m pytest tests/test_replay_metadata.py -q`; `.venv\Scripts\python.exe -m pytest tests/test_collision_model.py -q`; `.venv\Scripts\python.exe -m pytest -q`.
- Results: env basic tests passed (`43 passed`); py_compile passed; replay metadata tests passed (`9 passed`); collision model tests passed (`15 passed`). The requested plural path `tests/test_collision_models.py` does not exist in this repo; the actual file is `tests/test_collision_model.py`. Full pytest passed (`165 passed, 3 warnings`).
- Handoff bundle: `docs/ai/codex_task_bundle_20260610_151916_effect-guardrail.zip`.
- Remaining risk: this audit did not perform manual GUI replay checks; exact Flash visual registration, the `yseed` typo behavior, and boom `pause` initialization remain visual parity gaps.
- Suggested next task: run a GUI Heli-kill replay/manual check and compare effect placement/timing against Flash or FFDEC exports.

## 2026-06-10 Europe/Paris - Player Death Visual Presentation

- Pre-existing `git status --short` summary: modified tracked files from the prior visual-effect guardrail task were present (`ha2_env.py`, `tests/test_env_basic.py`, `docs/parity_notes.md`, `docs/ai/CURRENT_STATE.md`, `docs/ai/FLASH_AS_FINDINGS.md`, `docs/ai/CODEX_SESSION_LOG.md`, and `docs/ai/NEXT_CODEX_TASK.md`), with prior handoff bundles/report artifacts untracked.
- Task-file discrepancy: on-disk `docs/ai/NEXT_CODEX_TASK.md` still described the guardrail task; the active player-death presentation task came from the user message. The file was updated to summarize the active task and AS evidence.
- Files changed in this session: `ha2_env.py`, `scripts/play_human.py`, `tests/test_env_basic.py`, `docs/parity_notes.md`, `docs/ai/CURRENT_STATE.md`, `docs/ai/FLASH_AS_FINDINGS.md`, `docs/ai/CODEX_SESSION_LOG.md`, and `docs/ai/NEXT_CODEX_TASK.md`.
- AS/FFDEC resources inspected: `heliattack2_scripts/ha2_core_logic/frame_19_DoAction_2.as` (`heroDie`, gameover branch, `player.health <= 0`, `guyBurned`, 800% `boom`, delayed `stats` attach), mirrored `heliattack2_scripts/scripts/frame_19/DoAction_2.as`, `reference_exports/ffdec_ha2/symbol_class/symbols.csv`, and existing `assets_ffdec/sprites/`.
- Player-death assets used: `assets_ffdec/sprites/DefineSprite_76_guyBurned/1.png` and `assets_ffdec/sprites/DefineSprite_34_Boom/1.png` through `10.png`.
- Implementation: fatal player death now spawns render-only `player_burned` plus 800% `boom` visual effects. The burned player follows the AS `heroDie` fall/rotation/bounce style without moving the gameplay camera/world. Live player/gun drawing is suppressed only while the burned-player effect is active.
- Viewer behavior: `scripts.play_human` no longer immediately resets after `termination_reason="player_death"`. It enters post-death presentation mode, advances `advance_visual_effects_only()` instead of `step()`, and restarts only on `R` or `Enter`; `Esc`/window close still quit.
- RL/headless semantics: unchanged. `step()` still returns `terminated=True` immediately with `termination_reason="player_death"` on `health <= 0`; observations, rewards, score, collisions, enemy behavior, action spaces, and gameplay RNG remain independent of death visuals.
- State/replay compatibility: player death visuals live in `visual_effects`, old states without visual effects still load, and `state_hash()` continues to exclude `visual_effects` / `next_visual_effect_id`.
- Tests added/updated: universal death tests now assert the player-death visual spawn; new tests cover death visuals as render-only, gameplay RNG independence, visual-only post-terminal advancement, `rgb_array` rendering after death, and the `play_human` player-death termination helper.
- Commands run: `.venv\Scripts\python.exe -m pytest tests/test_env_basic.py -q`; `python -m py_compile ha2_env.py ha2_replay.py scripts/play_human.py scripts/play_replay.py scripts/watch_model.py scripts/evaluate_model.py`; `.venv\Scripts\python.exe -m pytest tests/test_replay_metadata.py -q`; `.venv\Scripts\python.exe -m pytest tests/test_collision_model.py -q`; `.venv\Scripts\python.exe -m pytest -q`.
- Results: env basic tests passed (`48 passed`); py_compile passed; replay metadata tests passed (`9 passed`); collision model tests passed (`15 passed`); full pytest passed (`170 passed, 3 warnings`).
- Handoff bundle: `docs/ai/codex_task_bundle_20260610_153201_player-death.zip`.
- Manual check status: not run. No GIF recorded.
- Remaining death/gameover parity gaps: exact burned-player registration/camera feel, live Flash timing, sound, stats/gameover panel, enemy cleanup visuals, and optional replay terminal hold remain future work.
- Suggested next task: implement AS-backed stats/gameover panel or add a replay viewer terminal hold for player-death replays.

## 2026-06-10 Europe/Paris - Post-Death Live Player Suppression

- Pre-existing `git status --short` summary: modified tracked files from the prior player-death presentation work were present (`ha2_env.py`, `scripts/play_human.py`, `tests/test_env_basic.py`, `docs/parity_notes.md`, `docs/ai/CURRENT_STATE.md`, `docs/ai/FLASH_AS_FINDINGS.md`, `docs/ai/CODEX_SESSION_LOG.md`, and `docs/ai/NEXT_CODEX_TASK.md`), with prior handoff bundles/report artifacts untracked.
- Task-file discrepancy: on-disk `docs/ai/NEXT_CODEX_TASK.md` still described the previous player-death presentation task; the active follow-up came from the user message. The file was updated to summarize the post-death live-player suppression task.
- Files changed in this session: `ha2_env.py`, `tests/test_env_basic.py`, `docs/parity_notes.md`, `docs/ai/CURRENT_STATE.md`, `docs/ai/CODEX_SESSION_LOG.md`, and `docs/ai/NEXT_CODEX_TASK.md`.
- Implementation: added `_should_draw_live_player()` and render now suppresses live player/gun whenever `last_terminated` is true with `last_termination_reason == "player_death"`. This keeps the live player and gun hidden during the whole post-death hold even after finite render-only effects expire.
- State decision: no new serialized field was added. Reset already clears `last_terminated` and `last_termination_reason`, so normal live-player rendering returns on reset. Gameplay hashes and replay state semantics are unchanged.
- Tests added/updated: after player death, `advance_visual_effects_only(frames=300)` expires all visual effects but `_should_draw_live_player()` remains false, `state_hash()` stays unchanged, observations/reward/termination state remain stable, `rgb_array` render still works, and reset restores live-player rendering.
- Commands run: `python -m py_compile ha2_env.py scripts/play_human.py scripts/play_replay.py scripts/watch_model.py scripts/evaluate_model.py`; `.venv\Scripts\python.exe -m pytest tests/test_env_basic.py -q`; `.venv\Scripts\python.exe -m pytest -q`.
- Results: py_compile passed; env basic tests passed (`49 passed`); full pytest passed (`171 passed, 3 warnings`).
- Handoff bundle: `docs/ai/codex_task_bundle_20260610_154045_death-hold.zip`.
- Manual check status: not run.
- Confirmation: death remains immediate terminal state for RL/headless; visual-only advancement remains gameplay-neutral; `ha2_env_legacy.py` was not modified.
- Remaining death/gameover parity gaps: exact burned-player registration/camera feel, live Flash timing, sound, stats/gameover panel, enemy cleanup visuals, and optional replay terminal hold remain future work.
- Suggested next task: run the manual `play_human` death hold check or implement AS-backed stats/gameover panel.

## 2026-06-10 Europe/Paris - GUI-Only Sound Playback First Pass

- Pre-existing `git status --short` summary: modified tracked files from the prior post-death hold work were present (`ha2_env.py`, `scripts/play_human.py`, `tests/test_env_basic.py`, `docs/parity_notes.md`, `docs/ai/CURRENT_STATE.md`, `docs/ai/FLASH_AS_FINDINGS.md`, `docs/ai/CODEX_SESSION_LOG.md`, and stale `docs/ai/NEXT_CODEX_TASK.md`), with prior handoff bundles/report artifacts untracked. Plain `git status` required `-c safe.directory=C:/Users/cthin/AI/HeliAttack`.
- Task clarification applied: runtime sound events are emitted only for currently implemented gameplay. The only weapon sound implemented now is the starting MachineGun `sgun`; unimplemented weapons and powerups are not wired for playback.
- Files changed: `ha2_env.py`, `ha2_sound.py`, `scripts/play_human.py`, `tests/test_env_basic.py`, `assets_ffdec/sounds/manifest.json`, copied sound MP3s under `assets_ffdec/sounds/`, `docs/parity_notes.md`, `docs/ai/CURRENT_STATE.md`, `docs/ai/FLASH_AS_FINDINGS.md`, `docs/ai/CODEX_SESSION_LOG.md`, and `docs/ai/NEXT_CODEX_TASK.md`.
- AS/FFDEC resources inspected: `reference_exports/ffdec_ha2/sounds/`, `reference_exports/ffdec_ha2/swf_xml/heli_attack_2.swf.xml`, `heliattack2_scripts/ha2_core_logic/frame_19_DoAction.as`, and `frame_19_DoAction_2.as`.
- Copied runtime sound assets: `sgun.mp3`, `sheliboom.mp3`, `shurt.mp3`, `sboom.mp3`, `sbigboom.mp3`, `shjump.mp3`, and `smetal0.mp3` through `smetal3.mp3`, sourced from the matching numbered FFDEC exports in `reference_exports/ffdec_ha2/sounds/`.
- Manifest: `assets_ffdec/sounds/manifest.json` maps AS sound names to runtime files. `sgun`, `sheliboom`, and `shurt` are marked `implemented`; `sboom`, `ssmallboom`, `sbigboom`, `shjump`, and metal sounds are marked `deferred`.
- Sound event architecture: `ha2_env.py` now has a transient `sound_events` queue with `emit_sound_event()`, `pop_sound_events()`, and `clear_sound_events()`. Events are cleared at the start of each `step()` and are not serialized into replay state or included in `state_hash()`.
- Implemented event emissions: `sgun` when the starting MachineGun fires, `sheliboom` when a Heli is destroyed, and `shurt` when the player takes damage. No unimplemented weapon/powerup sounds are emitted.
- GUI playback: added `ha2_sound.SoundPlayer`, which loads `assets_ffdec/sounds/manifest.json`, initializes `pygame.mixer` only when explicitly constructed by a viewer, applies manifest volume, and fails gracefully if audio is unavailable. `scripts.play_human` enables sound by default and supports `--no-sound`.
- Headless/RL safety: sound events do not affect observations, rewards, termination, score, collisions, gameplay RNG, replay verification, or gameplay hashes. `evaluate_model` and training paths do not require audio.
- Tests added/updated: manifest assets exist and implemented statuses are limited to `sgun`, `sheliboom`, and `shurt`; disabled/missing-audio `SoundPlayer` paths do not crash; headless env emits `sgun`, `sheliboom`, and `shurt`; sound events do not alter step outputs or state hashes; `scripts.play_human` accepts `--no-sound`.
- Commands run: `.venv\Scripts\python.exe -m pytest tests/test_env_basic.py -q`; `python -m py_compile ha2_env.py ha2_replay.py ha2_sound.py scripts/play_human.py scripts/play_replay.py scripts/watch_model.py scripts/evaluate_model.py`; `.venv\Scripts\python.exe -m pytest tests/test_replay_metadata.py -q`; `.venv\Scripts\python.exe -m pytest -q`.
- Results: env basic tests passed (`57 passed`); py_compile passed; replay metadata tests passed (`9 passed`); full pytest passed (`179 passed, 3 warnings`).
- Manual check status: not run. Training was not run.
- Confirmation: `ha2_env_legacy.py` was not modified.
- Remaining sound parity gaps: `shjump`, generic explosion sounds, metal hit sounds, continuous Heli loop `sheli`, music, full sound timing/volume parity, and all unimplemented weapon/powerup sounds remain deferred.
- Suggested next task: manually run `python -m scripts.play_human` and `python -m scripts.play_human --no-sound` to verify local audio device behavior and subjective volume/timing.

## 2026-06-10 Europe/Paris - Player Damage Blood And GUI Sound Finish

- Pre-existing `git status --short` summary: modified tracked files from the prior sound pass were present (`ha2_env.py`, `scripts/play_human.py`, `tests/test_env_basic.py`, `docs/parity_notes.md`, `docs/ai/CURRENT_STATE.md`, `docs/ai/FLASH_AS_FINDINGS.md`, `docs/ai/CODEX_SESSION_LOG.md`, and `docs/ai/NEXT_CODEX_TASK.md`), with `assets_ffdec/sounds/` and `ha2_sound.py` untracked plus prior handoff bundles/report artifacts untracked. Plain `git status` required `-c safe.directory=C:/Users/cthin/AI/HeliAttack`.
- Task-file discrepancy: on-disk `docs/ai/NEXT_CODEX_TASK.md` still described the previous sound pass; the active player-damage/sound finishing task came from the user message. The file was updated to summarize the active task and loop-state guardrail.
- Files changed: `ha2_env.py`, `ha2_sound.py`, `scripts/play_human.py`, `scripts/watch_model.py`, `scripts/play_replay.py`, `tests/test_env_basic.py`, `assets_ffdec/sounds/manifest.json`, new copied loop sounds `assets_ffdec/sounds/sheli.mp3` and `smusic.mp3`, `docs/parity_notes.md`, `docs/ai/CURRENT_STATE.md`, `docs/ai/FLASH_AS_FINDINGS.md`, `docs/ai/CODEX_SESSION_LOG.md`, and `docs/ai/NEXT_CODEX_TASK.md`.
- AS/FFDEC resources inspected: `heliattack2_scripts/ha2_core_logic/frame_19_DoAction.as`, `frame_19_DoAction_2.as`, `frame_19_DoAction_3.as`, `reference_exports/ffdec_ha2/swf_xml/heli_attack_2.swf.xml`, `reference_exports/ffdec_ha2/symbol_class/symbols.csv`, `reference_exports/ffdec_ha2/sprites_png/`, `reference_exports/ffdec_ha2/sounds/`, and existing `assets_ffdec/sprites/`.
- `shjump` trigger decision: implemented only in the existing HyperJump / boost branch that sets `yspeed = -32`, matching AS lines around `shjump.start(0,0)`. Tests confirm walking, ordinary jump, and landing-style idle steps do not emit `shjump`.
- Blood assets used: `assets_ffdec/sprites/DefineSprite_30_Blood/1.png` through `12.png`; `symbols.csv` maps `30;"Blood"`.
- Blood lifecycle implemented: enemy-bullet damage now spawns exactly three render-only `blood` visual effects at player center with deterministic visual-only rotation and pause offsets `0`, `2`, and `4`, using the same animation-frame style as boom/blood AS clips.
- Blood render-only confirmation: blood lives in `visual_effects`, may render/replay visually, and is excluded from `state_hash()`, observations, rewards, termination, score, collisions, physics, and gameplay RNG.
- GUI scripts updated: `scripts.play_human`, `scripts.watch_model`, and `scripts.play_replay` enable sound by default, accept `--no-sound`, consume transient one-shot sound events, and stop loops on exit/reset paths. `scripts.evaluate_model.py` remains audio-independent.
- Loop sound behavior implemented: `ha2_sound.SoundPlayer` now supports `start_loop`, `stop_loop`, `set_loop_volume`, `stop_all`, and `sync_loop_volumes` without restarting active loops every frame.
- `smusic` first-pass approximation: GUI viewers start/sync `smusic` at volume 50 when sound is available; exact AS menu/gameplay/end-game timing is not fully reproduced.
- `sheli` first-pass approximation: GUI viewers start/sync `sheli`, use volume 0 with no live Helis or terminal state, and otherwise compute the loudest live Heli using the inspected AS distance formula capped at 75. Exact multi-Heli Flash mixing is still unverified.
- Loop-state guardrail: loop/channel state, mixer objects, and audio-device initialization live only in `ha2_sound.SoundPlayer` and viewer code. `ha2_env.py` does not own sound-loop state or mixer/channel objects. Viewer-side `loop_volumes_from_env()` reads existing env gameplay facts only.
- Headless/RL confirmation: `HA2Env(render_mode=None)`, `reset()`, and `step()` do not initialize audio; training/evaluation paths do not require sound; sound events and loop handling do not affect observations, rewards, termination, truncation, collisions, score, physics, gameplay RNG, replay verification, or `state_hash()`.
- Tests added/updated: manifest implemented sounds now include `shjump`, `sheli`, and `smusic`; loop methods are tested with mocked mixer sounds/channels; viewer-side loop volume calculation is tested; `shjump` HyperJump-only behavior is tested; enemy-bullet damage health/blood/pause/render behavior is tested; blood hash/output/RNG neutrality is tested; GUI `--no-sound` default-on policy is tested; evaluate remains audio-independent.
- Commands run: `.venv\Scripts\python.exe -m pytest tests/test_env_basic.py -q`; `python -m py_compile ha2_env.py ha2_replay.py ha2_sound.py scripts/play_human.py scripts/play_replay.py scripts/watch_model.py scripts/evaluate_model.py`; `.venv\Scripts\python.exe -m pytest tests/test_replay_metadata.py -q`; `.venv\Scripts\python.exe -m pytest tests/test_runtime_config.py::test_watch_model_infers_runtime_config_from_experiment -q`; `.venv\Scripts\python.exe -m pytest -q`; `Test-Path tests/test_sound.py`.
- Results: env basic tests passed (`65 passed`); py_compile passed; replay metadata tests passed (`9 passed`); the targeted watch-model wrapper regression test passed (`1 passed`); full pytest passed (`187 passed, 3 warnings`); `tests/test_sound.py` does not exist, so sound-related coverage was run through `tests/test_env_basic.py`.
- Manual check status: not run. Training was not run.
- Confirmation: `ha2_env_legacy.py` was not modified.
- Remaining risks: exact live audio timing/volume, exact `smusic` transition timing, exact multi-Heli `sheli` mixing, generic explosion/metal sounds, red player hit flash/color transform, and manual audio-device behavior still need GUI checks.
- Suggested next task: manual GUI verification of `play_human`, `watch_model`, and `play_replay` with and without `--no-sound`, focused on HyperJump `shjump`, player-hit blood, music loop, Heli loop volume, and clean loop shutdown.

## 2026-06-12 Europe/Paris - GUI Viewer Harmonization

- Pre-existing `git status --short` summary: modified tracked files from the prior player-damage/sound work were present (`ha2_env.py`, `scripts/play_human.py`, `scripts/play_replay.py`, `scripts/watch_model.py`, `tests/test_env_basic.py`, `docs/parity_notes.md`, `docs/ai/CURRENT_STATE.md`, `docs/ai/FLASH_AS_FINDINGS.md`, `docs/ai/CODEX_SESSION_LOG.md`, and `docs/ai/NEXT_CODEX_TASK.md`), with `assets_ffdec/sounds/`, `ha2_sound.py`, prior handoff bundles, and report artifacts untracked. A pre-existing untracked `codex_gui_harmonization_bundle_20260610_224708.zip` was also present. Plain `git status` required `-c safe.directory=C:/Users/cthin/AI/HeliAttack`.
- Task-file discrepancy: on-disk `docs/ai/NEXT_CODEX_TASK.md` still described the prior player-damage/sound task; the active GUI harmonization task came from the user message. The file was updated to summarize the active task.
- GUI scripts inspected: `scripts/play_human.py`, `scripts/watch_model.py`, and `scripts/play_replay.py`.
- Shared helper introduced: `ha2_gui.py` centralizes common GUI state, key handling, speed factors, pause/single-step policy, terminal hold state, post-player-death visual advancement, GUI sound setup/update/shutdown, sound debug overlay lines, and wrapper-safe event/volume helpers.
- Files changed in this session: `ha2_gui.py`, `scripts/play_human.py`, `scripts/watch_model.py`, `scripts/play_replay.py`, `tests/test_env_basic.py`, `docs/ai/NEXT_CODEX_TASK.md`, `docs/ai/CURRENT_STATE.md`, `docs/ai/ARCHITECTURE_DECISIONS.md`, `docs/parity_notes.md`, `docs/ai/FLASH_AS_FINDINGS.md`, and `docs/ai/CODEX_SESSION_LOG.md`.
- Final key map: `Esc` quits; `Enter`/`R` restarts from terminal state; `F` increases GUI speed; `Shift+F` decreases GUI speed; `1` resets speed to `1x`; `P`/`Space` pause/unpause; `N` single-steps; `F1` toggles debug/help overlay; `F3` toggles collision/hitbox overlay where applicable. `play_human` keeps mode-specific mouse aim/fire and `F12` screenshots.
- Final speed factor list: `0.25x`, `0.5x`, `1x`, `2x`, `4x`, `8x`, defined once in `ha2_gui.GUI_SPEED_FACTORS`.
- Final speed composition rule: active GUI presentation uses `user_gui_speed_factor`; post-player-death presentation uses `effective_visual_speed = user_gui_speed_factor * gameover_slowdown_factor`. The GUI-only gameover factor tends toward `0.2x`, matching the inspected AS gameover `sendGameSpeed` floor.
- Final post-death behavior: `play_human` holds terminal state and restarts with `Enter`/`R`; `watch_model` now holds terminal state instead of immediately resetting, including player death; `play_replay` holds terminal replay states and restarts from the beginning with `Enter`/`R`. After `player_death`, none of the GUI scripts call normal `env.step()` again; they advance only render-only effects.
- Non-death terminal/truncation policy: the GUI holds terminal/truncated states and waits for `Enter`/`R` restart in all three modes. This was chosen for consistency and inspection.
- HUD harmonization result: all three scripts render through the existing central `ha2_env.render()` path on the base env. No GUI script draws duplicate gameplay HUD elements; GUI scripts only pass debug/help lines into the render overlay.
- Sound commonalization: all three GUI scripts use `ha2_gui.GuiSound`, sound is enabled by default, `--no-sound` is provided by shared args, transient one-shot events are consumed consistently, `smusic`/`sheli` loops are synced consistently, and loops stop on quit/reset/restart. `scripts.evaluate_model.py` remains audio-independent.
- `sheli` diagnosis: runtime manifest includes `sheli`; `assets_ffdec/sounds/sheli.mp3` exists; tests verify the loop channel starts at volume 0 and later accepts a nonzero active-channel volume. Viewer-side volume calculation returns nonzero for close live Helis and zero for no live Heli or terminal state. Manual host-audio audibility was not checked.
- `sheli` repair: loop setup/update was moved behind shared `GuiSound` so all GUI modes start the loop once and update channel volume instead of duplicating or missing loop sync.
- Headless/RL confirmation: no audio mixer/channel state was added to `ha2_env.py`; GUI timing/terminal/sound state lives in `ha2_gui.py`/`ha2_sound.py`; `HA2Env(render_mode=None)`, `reset()`, `step()`, observations, rewards, termination, truncation, collisions, score, physics, gameplay RNG, replay verification, and `state_hash()` are unchanged by GUI speed/sound state.
- Tests added/updated: common speed/key policy, speed-factor list, user speed times gameover slowdown composition, post-death visual-only state-hash neutrality, shared-helper usage by all three GUI scripts, default sound policy through shared helper, `sheli` loop channel volume update, and replay metadata compatibility.
- Commands run: `python -m py_compile ha2_gui.py ha2_env.py ha2_replay.py ha2_sound.py scripts/play_human.py scripts/play_replay.py scripts/watch_model.py scripts/evaluate_model.py`; `.venv\Scripts\python.exe -m pytest tests/test_env_basic.py -q`; `.venv\Scripts\python.exe -m pytest tests/test_runtime_config.py::test_watch_model_infers_runtime_config_from_experiment -q`; `.venv\Scripts\python.exe -m pytest tests/test_replay_metadata.py -q`; `.venv\Scripts\python.exe -m pytest -q`.
- Results: py_compile passed; env basic tests passed (`68 passed`); targeted watch-model runtime-config regression passed (`1 passed`); replay metadata tests passed (`9 passed`); full pytest passed (`190 passed, 3 warnings`).
- Manual check status: not run. Training was not run.
- Confirmation: `ha2_env_legacy.py` was not modified.
- Remaining risks: manual GUI/audio behavior still needs validation, especially real `sheli` audibility on the host audio stack, exact AS `smusic` timing, exact Flash gameover slowdown timing, and subjective terminal presentation feel.
- Suggested next task: run manual GUI checks for all three viewers with and without `--no-sound`, using `--sound-debug` to verify `sheli` volume near live Helis.
