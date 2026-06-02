# NEXT_CODEX_TASK.md

## Goal

Repair the HA2 HUD graphics to use the original extracted HUD assets instead of hand-drawn placeholder bars.

This is a visual-only HUD repair.

Do not change gameplay mechanics.

## Required fixes

Fix the current HUD implementation so that:

- `HyperJump` uses the original HA2 bar graphics, not `pygame.draw.rect` placeholder graphics.
- The label is `HyperJump:` with the colon.
- Add the missing `Health:` label near the healthbar.
- Add the current weapon icon for the starting MachineGun.
- Add the ammo text `Infinite x `.
- Add the reload bar using the original HA2 reload graphics.
- Keep HUD rendering centralized in `ha2_env.py`.
- Do not duplicate HUD drawing in `play_human.py`, `watch_model.py`, or `play_replay.py`.

## What Codex should replace

The current implementation draws the HyperJump bar manually with `pygame.draw.rect`.

Replace that visual placeholder with the original extracted HUD assets.

Do not remove the exact HUD font support added in the previous task.

## Technical constants

Gameplay area:

- width: `450`
- height: `320`

Use the exact HUD font already copied to:

- `assets_ffdec/fonts/19_standard 07_63.ttf`

### Top-left dynamic text positions

Use these coordinates instead of the earlier approximate `x=2` layout:

Time line:

- foreground: `(4, 2)`
- shadow: `(5, 3)`

Score line:

- foreground: `(4, 15)`
- shadow: `(5, 16)`

High score line:

- foreground: `(4, 28)`
- shadow: `(5, 29)`

Text content remains:

- `Time: <seconds> seconds     Helis: <heli_count>`
- `Score: <display_score>`
- `High Score: <display_high_score>`

### Health label and bar

Add the label:

- text: `Health:`
- foreground: `(390, 2)`
- shadow: `(391, 3)`

Use the existing healthbar logic, but align it with the original HUD placement if practical:

- health sprite position: `(431, 0)`
- health sprite: `assets_ffdec/sprites/DefineSprite_176/1.png`
- existing component bitmaps:
  - `assets_ffdec/images/170.png`
  - `assets_ffdec/images/174.png`

Keep the current bottom-anchored health fill rule.

If changing the healthbar from the previous `(429, 0)` offset causes a visible regression, stop and report rather than guessing.

### HyperJump bar

Use original assets:

- full sprite: `assets_ffdec/sprites/DefineSprite_163/1.png`
- base bitmap: `assets_ffdec/images/157.png`
- fill bitmap: `assets_ffdec/images/161.png`

Position:

- label text: `HyperJump:`
- label foreground: `(57, 306)`
- label shadow: `(58, 307)`
- bar sprite position: `(129, 302)`

Fill rule:

- `fraction = clamp(hyperjump / 150.0, 0.0, 1.0)`
- use the original base bitmap as the empty/background bar
- crop or mask the original fill bitmap horizontally according to `fraction`
- fill grows left to right

Do not use primitive rectangle graphics for this bar.

### Reload bar

Add the reload label and bar.

Use original assets:

- full ready sprite: `assets_ffdec/sprites/DefineSprite_156/1.png`
- base bitmap: `assets_ffdec/images/147.png`
- orange fill bitmap: `assets_ffdec/images/151.png`
- ready yellow bitmap: `assets_ffdec/images/153.png`

Position:

- label text: `Reload: `
- label foreground: `(364, 306)`
- label shadow: `(365, 307)`
- bar sprite position: `(407, 302)`

AS-backed behavior:

- while reloading:
  - hide the yellow ready layer;
  - draw the base bitmap;
  - draw a horizontally cropped orange fill bitmap;
  - fraction = `gun_reloadtime / MACHINEGUN_RELOADTIME`, clamped to `[0, 1]`;
- when ready and bullets are available:
  - show the yellow ready layer;
  - this can be implemented by drawing the full ready sprite or by drawing the yellow bitmap over the base.

For the starting MachineGun:

- `MACHINEGUN_RELOADTIME = 5`
- bullets are infinite, so the gun is available when reload is ready.

### Weapon icon

Add the starting weapon icon:

- sprite: `assets_ffdec/sprites/DefineSprite_205/1.png`
- position: `(416, 269)`

Frame 1 is the starting MachineGun icon.

Do not implement weapon switching in this task.

### Ammo text

Add the ammo text for the current starting weapon:

- text: `Infinite x `
- foreground position: `(363, 287)`
- shadow position: `(364, 288)`
- right-align it in a width of about `57 px`

Use the exact HUD font and the same black-shadow/white-foreground rule.

Do not implement finite ammo counts in this task.

## Optional future constants to record, not implement now

The original HUD also includes:

- `TimeDistort:` label at foreground `(209, 306)`, shadow `(210, 307)`
- `bullettime` bar at `(282, 302)`

Do not implement bullet time behavior in this task.

Record these constants in `docs/parity_notes.md` or `docs/ai/CURRENT_STATE.md` only if useful.

## Files to inspect

- `ha2_env.py`
- `ha2_high_score.py`
- `scripts/play_human.py`
- `scripts/watch_model.py`
- `scripts/play_replay.py`
- `scripts/evaluate_model.py`
- `tests/test_env_basic.py`
- `tests/test_high_score.py`
- `docs/parity_notes.md`
- `docs/ai/CURRENT_STATE.md`
- `docs/ai/CODEX_SESSION_LOG.md`

## Files likely to modify

Likely:

- `ha2_env.py`
- `tests/test_env_basic.py`
- possibly `docs/parity_notes.md`
- `docs/ai/CURRENT_STATE.md`
- `docs/ai/CODEX_SESSION_LOG.md`

Do not modify `ha2_env_legacy.py`.

Do not modify gameplay scripts except if a test reveals that a HUD asset path is not loaded correctly.

Do not change high-score persistence behavior unless directly required by the HUD repair.

## Implementation guidance

Centralize all visual HUD composition in `ha2_env.py`.

Add image loading keys for:

- reload full sprite / base / fill / ready
- hyperjump full sprite / base / fill
- weapon icon frame 1

Add small helper functions if useful:

- draw HUD text with shadow;
- draw horizontally masked HUD bar;
- draw reload bar;
- draw HyperJump bar;
- draw weapon/ammo block.

The horizontally masked bar helper should use copied/cropped surfaces from the original fill bitmap, not colored rectangles.

Keep all rendering deterministic.

Do not add external image dependencies.

## Tests

Add or update tests to check:

- the needed HUD assets are loadable;
- HUD debug values are unchanged from the previous task;
- rgb_array rendering still works;
- the render path does not crash when drawing HyperJump, reload, weapon icon, ammo, and Health label;
- viewer scripts do not contain duplicate HUD drawing logic.

Avoid brittle pixel-perfect tests.

## Validation

Run:

- `python -m py_compile ha2_env.py ha2_high_score.py scripts/play_human.py scripts/watch_model.py scripts/play_replay.py scripts/evaluate_model.py`
- `python -m pytest tests/test_env_basic.py`
- `python -m pytest tests/test_high_score.py`
- `python -m pytest`

Do not run training.

## Manual checks

Run:

- `python -m scripts.play_human`

Verify visually:

- `Health:` appears near the healthbar.
- The healthbar remains correct.
- `HyperJump:` has the original cyan bar graphics.
- The HyperJump fill changes with charge.
- `Reload:` appears at the bottom right.
- The reload bar uses the original orange/yellow graphics.
- The starting MachineGun icon appears at the bottom right.
- `Infinite x ` appears near the weapon icon.
- Top-left text still appears with exact font and shadow.
- The debug side panel remains separate.
- `play_human`, `watch_model`, and `play_replay` all get the HUD through `env.render(...)`.

## Acceptance criteria

This task is complete if:

- no hand-drawn placeholder rectangle remains for the HyperJump bar;
- HyperJump and reload bars use original extracted graphics;
- `Health:` label is present;
- MachineGun icon is present;
- `Infinite x ` is present;
- reload readiness is visually represented with the original ready/yellow layer;
- HUD rendering remains centralized in `ha2_env.py`;
- `ha2_env_legacy.py` is unchanged;
- no gameplay mechanics changed;
- tests pass;
- docs/session log are updated.

## Stop conditions

Stop and report if:

- the needed assets are missing from `assets_ffdec`;
- the current repository does not contain the extracted bar/icon assets;
- exact healthbar placement conflicts with the previously accepted visual adjustment;
- implementing masked original bars requires a broad rendering refactor;
- this task starts touching gameplay or replay semantics;
- unrelated uncommitted changes make the task unsafe to isolate.

## Required Codex session log

Update `docs/ai/CODEX_SESSION_LOG.md` with:

- files changed;
- commands run;
- pass/fail results;
- exact HUD assets used;
- whether the healthbar was left at the previous adjusted position or restored to `(431, 0)`;
- confirmation that visual HUD drawing is still centralized;
- remaining HUD gaps.