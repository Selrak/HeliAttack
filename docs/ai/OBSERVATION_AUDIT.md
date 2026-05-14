# combat_v1 Observation Audit

Last updated: 2026-05-14 Europe/Paris

## Current Layout
- `combat_v1` has 37 float32 fields, defined by `COMBAT_V1_OBS_FIELDS` in `ha2_env.py`.
- It exposes player world position, velocity, health, grounded/jump/duck state, hyperjump charge, gun/aim rotation, gun readiness, player bullet count, one primary Heli, one nearest enemy bullet, camera/world offset, Heli kills, and score.
- Player and Heli coordinates are normalized relative quantities where applicable; bullet coordinates are relative to the player.

## Enemy Bullet Exposure
- `combat_v1` exposes only one enemy bullet: the nearest engine-maintained enemy bullet to the player.
- It includes that bullet's relative x/y position and x/y velocity.
- It also exposes total engine enemy bullet count normalized by 20.
- It does not expose all visible bullets.
- It does not clip enemy bullets to the gameplay viewport before selecting the nearest bullet.
- It can therefore include an off-screen engine bullet if that bullet is nearest by world distance.

## Missing For Multi-Bullet Dodging
- The policy cannot reason about multiple simultaneous visible bullets.
- It cannot know whether a dodge away from the nearest bullet moves into another visible bullet.
- It cannot distinguish visible from off-screen enemy bullets through the current bullet-count field.

## combat_bullets_v1 Implementation
- `combat_bullets_v1` is an extension of `combat_v1` introduced to solve the multi-bullet dodging limitation.
- It removes the 5 nearest-enemy-bullet fields from `combat_v1`.
- It inserts 52 new fields:
  - `visible_enemy_bullet_count_normalized`
  - `visible_enemy_bullets_over_top10_normalized`
  - 10 blocks of 5 per-bullet fields: active flag, relative x from player, relative y from player, velocity x, velocity y.
- Total observation size is 84 `float32` fields (`COMBAT_BULLETS_V1_OBS_SIZE`).
- The bullets are drawn from `self.visible_enemy_bullets()`, which filters using the `_enemy_bullet_visible_to_player` predicate (including an 8px margin) and sorts by squared distance to the player.
- The `combat_v1` profile layout remains strictly unchanged to maintain backward compatibility with previous models.
