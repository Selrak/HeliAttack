from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pygame

import ha2_constants as const


REPO_ROOT = Path(__file__).resolve().parent
HA2_ASSET_DIR = REPO_ROOT / "assets_ffdec"
ENV_NAME = "HeliAttack2Env"
ENV_VERSION = "0.6"

AIM_BINS = 32
DEFAULT_AIM_BIN = 0
MACHINEGUN_RELOADTIME = 5
MACHINEGUN_SPEED = 8
MACHINEGUN_DAMAGE = 10
MACHINEGUN_BULLET_FRAME = 1
MACHINEGUN_SPREAD_CHOICES = 4
GUN_BARREL_LENGTH = 22.0
FLASH_HERO_GUN_X = 24.0
FLASH_HERO_GUN_Y = 29.0
FLASH_MACHINEGUN_BARREL_X = 22.7
FLASH_MACHINEGUN_BARREL_Y = -7.4
MACHINEGUN_SPRITE_ORIGIN = (24.0, 26.0)
HELI_DEFAULT_HEALTH = 300
PLAYER_DEFAULT_HEALTH = 100
HELI_HIT_OFFSET_X = -104.5
HELI_HIT_OFFSET_Y = -52.55
HELI_HIT_WIDTH = 207.0
HELI_HIT_HEIGHT = 93.0
HELI_BODY_WIDTH = 212.0
HELI_BODY_HEIGHT = 106.0
HELI_TARGET_X_OFFSET = 275.0
HELI_TARGET_Y_OFFSET = -205.0
HELI_TRACE_TARGET_Y = 449.0
HELI_MAX_SPEED = 4.0
HELI_PILOT_FRAME1_OFFSET = (104.5, 33.5)
HELI_PILOT_FRAME2_OFFSET = (84.45, 33.5)
HELI_GUN_FRAME1_OFFSET = (11.0, 7.0)
HELI_GUN_FRAME2_OFFSET = (-9.0, 7.0)
HELI_GUN_SMOOTHING_BASE = 10
HELI_SHOOT_RELOAD_BASE = 16
ENEMY_BULLET_SPEED = 7.0
ENEMY_BULLET_DAMAGE = 10
AS_STW = math.ceil(const.SCREEN_WIDTH / const.TILE_SIZE)
AS_STH = math.ceil(const.SCREEN_HEIGHT / const.TILE_SIZE)
AS_SPW = AS_STW * const.TILE_SIZE
AS_SPH = AS_STH * const.TILE_SIZE
DEBUG_PANEL_WIDTH = 520
HUD_HEALTH_X = 429
HUD_HEALTH_Y = 0
HUD_HEALTH_BITMAP_X = 4
HUD_HEALTH_BITMAP_Y = 0
TRAINING_PROFILES = {"legacy", "combat_v1"}
COMBAT_V1_OBS_FIELDS = (
    "player_x_norm",
    "player_y_norm",
    "player_xspeed_norm",
    "player_yspeed_norm",
    "player_health",
    "grounded",
    "jumping",
    "double_jump_used",
    "ducking",
    "hyperjump_charge",
    "gun_rotation_sin",
    "gun_rotation_cos",
    "aim_rotation_sin",
    "aim_rotation_cos",
    "gun_ready",
    "gun_reload_fraction",
    "player_bullet_count",
    "has_enemy",
    "enemy_rel_x",
    "enemy_rel_y",
    "enemy_xspeed",
    "enemy_yspeed",
    "enemy_health",
    "enemy_visible",
    "enemy_gun_rotation_sin",
    "enemy_gun_rotation_cos",
    "enemy_shoot_phase",
    "enemy_bullet_count",
    "has_nearest_enemy_bullet",
    "nearest_enemy_bullet_rel_x",
    "nearest_enemy_bullet_rel_y",
    "nearest_enemy_bullet_xspeed",
    "nearest_enemy_bullet_yspeed",
    "world_x",
    "world_y",
    "heli_kills",
    "score",
)
COMBAT_V1_OBS_SIZE = len(COMBAT_V1_OBS_FIELDS)


class HeliAttack2Env(gym.Env):
    """
    Custom Gymnasium environment for Heli Attack 2.

    Physics is intentionally close to the current AS2 translation. Prefer adding
    tests and AS references before changing movement/collision behavior.
    """

    metadata = {"render_modes": ["human", "rgb_array", "console"], "render_fps": 30}

    def __init__(
        self,
        render_mode: str | None = None,
        *,
        assets_dir: str | Path | None = None,
        auto_render: bool = True,
        spawn_default_heli: bool = True,
        respawn_helis: bool = True,
        training_profile: str = "legacy",
        max_episode_steps: int | None = None,
    ):
        super().__init__()
        if training_profile not in TRAINING_PROFILES:
            raise ValueError(
                f"Unknown training_profile {training_profile!r}; "
                f"expected one of {sorted(TRAINING_PROFILES)}"
            )
        if max_episode_steps is not None and int(max_episode_steps) <= 0:
            raise ValueError("max_episode_steps must be positive or None")
        self.render_mode = render_mode
        self.assets_dir = Path(assets_dir) if assets_dir is not None else HA2_ASSET_DIR
        self.auto_render = auto_render
        self.spawn_default_heli = bool(spawn_default_heli)
        self.respawn_helis = bool(respawn_helis)
        self.training_profile = training_profile
        self.max_episode_steps = None if max_episode_steps is None else int(max_episode_steps)

        # ACTION SPACE: [Move(left/idle/right), Jump, Duck, Boost, AimBin, Fire]
        self.action_space = spaces.MultiDiscrete([3, 2, 2, 2, AIM_BINS, 2])

        self.map_width = len(const.FULL_MAP_DATA[0])
        self.map_height = len(const.FULL_MAP_DATA)
        self.map_pixel_width = self.map_width * const.TILE_SIZE
        self.map_pixel_height = self.map_height * const.TILE_SIZE
        if self.training_profile == "legacy":
            high = np.array(
                [self.map_pixel_width * 2.0, self.map_pixel_height * 2.0, 100.0, 100.0],
                dtype=np.float32,
            )
            self.observation_space = spaces.Box(low=-high, high=high, dtype=np.float32)
        else:
            self.observation_space = spaces.Box(
                low=-np.ones(COMBAT_V1_OBS_SIZE, dtype=np.float32),
                high=np.ones(COMBAT_V1_OBS_SIZE, dtype=np.float32),
                dtype=np.float32,
            )
        self.map_data = self._make_runtime_map()
        self.window_size = (const.SCREEN_WIDTH, const.SCREEN_HEIGHT)

        self.window = None
        self.clock = None
        self.font = None
        self.images: dict[str, pygame.Surface | None] = {}
        self.tiles: dict[int, pygame.Surface | None] = {}

        self._x = 0.0
        self._y = 0.0
        self.xspeed = 0.0
        self.yspeed = 0.0
        self.xchange = 0.0
        self.ychange = 0.0

        self.width = 48
        self.height = 48
        self.defplayerwidth = 10
        self.defplayerheight = 42
        self.playerwidth = 10
        self.playerheight = 42
        self.health = PLAYER_DEFAULT_HEALTH
        self.lastHealth = PLAYER_DEFAULT_HEALTH

        self.jump = 0
        self.jump2 = 0
        self.duck = 0
        self.up = 0
        self.upk = 0
        self.hyperjump = 150
        self.hjump = 0
        self.boostK = 0
        self.facing_right = True

        self.cgun = 0
        self.gun_reloadtime = math.inf
        self.gun_bullets = math.inf
        self.gun_shots = 0
        self.gun_rotation = 0.0
        self.aim_rotation = 0.0
        self.bullets: list[dict[str, Any]] = []
        self.next_bullet_id = 1
        self.total_bullets_spawned = 0
        self.enemies: list[dict[str, Any]] = []
        self.enemy_bullets: list[dict[str, Any]] = []
        self.next_enemy_id = 1
        self.total_enemies_spawned = 0
        self.next_enemy_bullet_id = 1
        self.total_enemy_bullets_spawned = 0
        self.enemy_bullet_hits = 0
        self.score = 0
        self.hits = 0
        self.helis = 0
        self.rthelis = 0
        self.level = 0
        self.pending_default_heli = False
        self.default_heli_spawned = False
        self.last_player_damage_tick: int | None = None
        self.last_player_damage_amount = 0

        self.tick = 0
        self.last_action = [1, 0, 0, 0, DEFAULT_AIM_BIN, 0]
        self.last_reward = 0.0
        self.last_terminated = False
        self.last_truncated = False
        self.last_termination_reason = "none"
        self.last_reward_breakdown: dict[str, float] | None = None
        self.episode_step_count = 0
        self.last_contact = self._empty_contact()
        self.last_camera = (0.0, 0.0)
        self.world_x = 0.0
        self.world_y = 0.0
        self.worldpos = [0, 0]
        self.worldbounds = [0, 0]
        self.last_gun_event = self._empty_gun_event()
        self.last_enemy_event = self._empty_enemy_event()

    def _make_runtime_map(self) -> list[list[list[int]]]:
        map_data = [[tile.copy() for tile in row] for row in const.FULL_MAP_DATA]
        for row in map_data:
            for tile in row:
                if tile[0] == 32:
                    # AS assignents() consumes spawn markers and clears them.
                    tile[0] = 0
        return map_data

    def _empty_contact(self) -> dict[str, Any]:
        return {
            "x_blocked": False,
            "y_blocked": False,
            "wall": None,
            "ground": False,
            "ceiling": False,
            "hit_count": 0,
        }

    def _empty_gun_event(self) -> dict[str, Any]:
        return {
            "removed_bullet_ids": [],
            "fired": False,
            "spawned_bullet_id": None,
            "spawn_blocked": False,
        }

    def _empty_enemy_event(self) -> dict[str, Any]:
        return {
            "removed_enemy_bullet_ids": [],
            "spawned_enemy_bullet_ids": [],
            "spawned_enemy_ids": [],
            "killed_enemy_ids": [],
            "player_damage": 0,
        }

    def _ensure_pygame_ready(self) -> None:
        if self.render_mode == "rgb_array":
            os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

        if not pygame.display.get_init():
            pygame.display.init()

        if self.render_mode == "human":
            if self.window is None:
                self.window = pygame.display.set_mode(self.window_size)
                pygame.display.set_caption("HA2 Simulator")
                self.clock = pygame.time.Clock()
        elif self.render_mode == "rgb_array" and pygame.display.get_surface() is None:
            pygame.display.set_mode((1, 1), getattr(pygame, "HIDDEN", 0))

        if self.font is None:
            if not pygame.font.get_init():
                pygame.font.init()
            self.font = pygame.font.SysFont(None, 18)

    def _load_images(self) -> None:
        self._ensure_pygame_ready()

        def load_img(rel_path: str | Path) -> pygame.Surface | None:
            path = self.assets_dir / rel_path
            if not path.exists():
                return None
            image = pygame.image.load(str(path))
            try:
                return image.convert_alpha()
            except pygame.error:
                return image.convert()

        def compose_heli_frame(*, flipped: bool) -> pygame.Surface | None:
            body = load_img(Path("images") / "78.png")
            if body is None:
                return None
            pilot = load_img(Path("images") / "77.png")
            frame = pygame.Surface(body.get_size(), pygame.SRCALPHA)
            frame.blit(pygame.transform.flip(body, True, False) if flipped else body, (0, 0))
            if pilot is not None:
                offset = HELI_PILOT_FRAME2_OFFSET if flipped else HELI_PILOT_FRAME1_OFFSET
                frame.blit(pilot, offset)
            return frame.convert_alpha()

        self.images = {
            "guy": load_img(Path("images") / "116.png"),
            "duck": load_img(Path("images") / "120.png"),
            "jump": load_img(Path("images") / "124.png"),
            "walk1": load_img(Path("images") / "126.png"),
            "walk2": load_img(Path("images") / "128.png"),
            "jump2": load_img(Path("images") / "131.png"),
            "chute": load_img(Path("images") / "133.png"),
            "bullet": load_img(Path("images") / "35.png"),
            "machinegun": load_img(Path("sprites") / "DefineSprite_107" / "1.png"),
            "enemy_bullet": load_img(Path("sprites") / "DefineSprite_68_enemyBullet" / "1.png"),
            "hud_health": load_img(Path("sprites") / "DefineSprite_176" / "1.png"),
            "hud_health_base": load_img(Path("images") / "170.png"),
            "hud_health_fill": load_img(Path("images") / "174.png"),
            "heli1": compose_heli_frame(flipped=False),
            "heli2": compose_heli_frame(flipped=True),
            "bg": load_img(Path("images") / "410.jpg"),
            "bg1": load_img(Path("sprites") / "DefineSprite_25_bg" / "2.png"),
        }

        tiles_dir = Path("sprites") / "DefineSprite_318_tiles"
        self.tiles = {
            graphic_idx: load_img(tiles_dir / f"{graphic_idx + 1}.png")
            for graphic_idx in range(11)
        }

    def reset(self, seed: int | None = None, options: dict[str, Any] | None = None):
        super().reset(seed=seed)

        spawn_tx, _spawn_ty = const.PLAYER_SPAWN_INDEX
        self._x = (spawn_tx * const.TILE_SIZE) + (const.TILE_SIZE / 2)
        self._y = -50.0

        self.xspeed = 0.0
        self.yspeed = 0.0
        self.xchange = 0.0
        self.ychange = 0.0
        self.playerwidth = self.defplayerwidth
        self.playerheight = self.defplayerheight
        self.health = PLAYER_DEFAULT_HEALTH
        self.lastHealth = PLAYER_DEFAULT_HEALTH
        self.jump = 0
        self.jump2 = 0
        self.duck = 0
        self.up = 0
        self.upk = 0
        self.hjump = 0
        self.hyperjump = 150
        self.boostK = 0
        self.facing_right = True
        self.cgun = 0
        self.gun_reloadtime = math.inf
        self.gun_bullets = math.inf
        self.gun_shots = 0
        self.gun_rotation = 0.0
        self.aim_rotation = 0.0
        self.bullets = []
        self.next_bullet_id = 1
        self.total_bullets_spawned = 0
        self.enemies = []
        self.enemy_bullets = []
        self.next_enemy_id = 1
        self.total_enemies_spawned = 0
        self.next_enemy_bullet_id = 1
        self.total_enemy_bullets_spawned = 0
        self.enemy_bullet_hits = 0
        self.score = 0
        self.hits = 0
        self.helis = 0
        self.rthelis = 0
        self.level = 0
        self.pending_default_heli = bool(self.spawn_default_heli)
        self.default_heli_spawned = False
        self.last_player_damage_tick = None
        self.last_player_damage_amount = 0
        self.total_player_damage = 0
        self.total_player_damage = 0
        self.world_x = 0.0
        self.world_y = 0.0
        self.worldpos = [0, 0]
        self.worldbounds = [0, 0]
        self._scroll_world()
        self.tick = 0
        self.last_action = [1, 0, 0, 0, DEFAULT_AIM_BIN, 0]
        self.last_reward = 0.0
        self.last_terminated = False
        self.last_truncated = False
        self.last_termination_reason = "none"
        self.last_reward_breakdown = None
        self.episode_step_count = 0
        self.last_contact = self._empty_contact()
        self.last_camera = self.get_camera()
        self.last_gun_event = self._empty_gun_event()
        self.last_enemy_event = self._empty_enemy_event()

        if self.auto_render and self.render_mode in ["human", "rgb_array"]:
            self.render()

        return self._get_obs(), self.get_debug_info()

    def _get_obs(self) -> np.ndarray:
        if self.training_profile == "combat_v1":
            return self._get_combat_v1_obs()
        return self._get_legacy_obs()

    def _get_legacy_obs(self) -> np.ndarray:
        return np.array([self._x, self._y, self.xspeed, self.yspeed], dtype=np.float32)

    def _clip_norm(self, value: float, scale: float) -> float:
        if scale <= 0:
            return 0.0
        return float(np.clip(float(value) / scale, -1.0, 1.0))

    def _angle_sin_cos(self, degrees: float) -> tuple[float, float]:
        radians = math.radians(float(degrees))
        return math.sin(radians), math.cos(radians)

    def _primary_enemy(self) -> dict[str, Any] | None:
        live_enemies = [enemy for enemy in self.enemies if int(enemy.get("health", 0)) > 0]
        if not live_enemies:
            return None
        return min(
            live_enemies,
            key=lambda enemy: (float(enemy["x"]) - self._x) ** 2 + (float(enemy["y"]) - self._y) ** 2,
        )

    def _nearest_enemy_bullet(self) -> dict[str, Any] | None:
        if not self.enemy_bullets:
            return None
        return min(
            self.enemy_bullets,
            key=lambda bullet: (float(bullet["x"]) - self._x) ** 2 + (float(bullet["y"]) - self._y) ** 2,
        )

    def _get_combat_v1_obs(self) -> np.ndarray:
        # COMBAT_V1_OBS_FIELDS defines the stable index layout for SB3 MlpPolicy.
        gun_sin, gun_cos = self._angle_sin_cos(self.gun_rotation)
        aim_sin, aim_cos = self._angle_sin_cos(self.aim_rotation)
        if math.isinf(self.gun_reloadtime):
            reload_fraction = 1.0
            gun_ready = 1.0
        else:
            reload_fraction = float(np.clip(self.gun_reloadtime / MACHINEGUN_RELOADTIME, 0.0, 1.0))
            gun_ready = 1.0 if self.gun_reloadtime >= MACHINEGUN_RELOADTIME else 0.0

        values = [
            self._clip_norm(self._x, self.map_pixel_width),
            self._clip_norm(self._y, self.map_pixel_height),
            self._clip_norm(self.xspeed, 10.0),
            self._clip_norm(self.yspeed, float(const.TILE_SIZE)),
            float(np.clip(self.health / PLAYER_DEFAULT_HEALTH, 0.0, 1.0)),
            1.0 if self.jump == 0 and self.yspeed == 0 else 0.0,
            1.0 if self.jump else 0.0,
            1.0 if self.jump2 else 0.0,
            1.0 if self.duck else 0.0,
            float(np.clip(self.hyperjump / 150.0, 0.0, 1.0)),
            gun_sin,
            gun_cos,
            aim_sin,
            aim_cos,
            gun_ready,
            reload_fraction,
            float(np.clip(len(self.bullets) / 20.0, 0.0, 1.0)),
        ]

        enemy = self._primary_enemy()
        if enemy is None:
            values.extend([0.0] * 10)
        else:
            enemy_gun_sin, enemy_gun_cos = self._angle_sin_cos(
                float(enemy.get("rotation", 0.0)) + float(enemy.get("gun_rotation", 0.0))
            )
            shoot_period = max(10, HELI_SHOOT_RELOAD_BASE - self.level)
            values.extend(
                [
                    1.0,
                    self._clip_norm(float(enemy["x"]) - self._x, const.SCREEN_WIDTH),
                    self._clip_norm(float(enemy["y"]) - self._y, const.SCREEN_HEIGHT),
                    self._clip_norm(float(enemy["xspeed"]), 10.0),
                    self._clip_norm(float(enemy["yspeed"]), 10.0),
                    float(np.clip(int(enemy["health"]) / max(1, int(enemy["max_health"])), 0.0, 1.0)),
                    1.0 if enemy.get("visible", True) else 0.0,
                    enemy_gun_sin,
                    enemy_gun_cos,
                    float(np.clip((int(enemy.get("shoot", 0)) % shoot_period) / shoot_period, 0.0, 1.0)),
                ]
            )

        bullet = self._nearest_enemy_bullet()
        values.append(float(np.clip(len(self.enemy_bullets) / 20.0, 0.0, 1.0)))
        if bullet is None:
            values.extend([0.0] * 5)
        else:
            values.extend(
                [
                    1.0,
                    self._clip_norm(float(bullet["x"]) - self._x, const.SCREEN_WIDTH),
                    self._clip_norm(float(bullet["y"]) - self._y, const.SCREEN_HEIGHT),
                    self._clip_norm(float(bullet["xspeed"]), 10.0),
                    self._clip_norm(float(bullet["yspeed"]), 10.0),
                ]
            )

        values.extend(
            [
                self._clip_norm(self.world_x, max(1.0, abs(self._world_min_x()))),
                self._clip_norm(self.world_y, max(1.0, abs(self._world_min_y()))),
                float(np.clip(self.rthelis / 50.0, 0.0, 1.0)),
                float(np.clip(self.score / 5000.0, 0.0, 1.0)),
            ]
        )
        obs = np.asarray(values, dtype=np.float32)
        if obs.shape != (COMBAT_V1_OBS_SIZE,):
            raise AssertionError(f"combat_v1 observation size mismatch: {obs.shape}")
        return obs

    def _hit_check(self, cy, cx, cy2, cx2, type_val=1, equal=0, hold=0) -> int:
        count = 0
        for y in range(int(cy), int(cy2) + 1):
            for x in range(int(cx), int(cx2) + 1):
                if 0 <= y < self.map_height and 0 <= x < self.map_width:
                    val = self.map_data[y][x][0]
                    if 0 <= val < 100:
                        if equal:
                            if val == type_val:
                                count += 1
                                if not hold:
                                    return 1
                        elif val != type_val:
                            count += 1
                            if not hold:
                                return 1
        return count

    def _normalize_action(self, action) -> list[int]:
        values = [int(v) for v in np.asarray(action, dtype=np.int64).flatten().tolist()]
        if len(values) == 4:
            values.extend([DEFAULT_AIM_BIN, 0])
        if len(values) != 6:
            raise ValueError(f"Expected action length 6, or legacy length 4; got {len(values)}")
        values[4] %= AIM_BINS
        values[5] = 1 if values[5] else 0
        return values

    def aim_bin_to_rotation(self, aim_bin: int) -> float:
        return float((int(aim_bin) % AIM_BINS) * 360.0 / AIM_BINS)

    def aim_bin_for_world_target(self, world_x: float, world_y: float) -> int:
        muzzle_x, muzzle_y = self._gun_barrel_world_pos(self.gun_rotation)
        angle = math.degrees(math.atan2(world_y - muzzle_y, world_x - muzzle_x)) % 360.0
        bin_width = 360.0 / AIM_BINS
        return int((angle + bin_width / 2.0) // bin_width) % AIM_BINS

    def _shortest_angle_diff(self, target: float, current: float) -> float:
        diff = (target % 360.0) - (current % 360.0)
        diff = diff if diff <= 179.0 else -360.0 + diff
        diff = diff if diff >= -179.0 else 360.0 + diff
        return diff

    def _world_min_x(self) -> float:
        return -float((self.map_width - AS_STW) * const.TILE_SIZE)

    def _world_min_y(self) -> float:
        return -float((self.map_height - AS_STH) * const.TILE_SIZE)

    def _scroll_world(self) -> None:
        # Mirrors the clamping and getWorldPos side effects of AS scrollMap.
        self.world_x = min(0.0, max(self._world_min_x(), float(self.world_x)))
        self.world_y = min(0.0, max(self._world_min_y(), float(self.world_y)))
        self.worldpos = [
            math.floor((-self.world_x) / const.TILE_SIZE),
            math.floor((-self.world_y) / const.TILE_SIZE),
        ]

    def _update_world_after_player(self) -> None:
        ret = 0
        if self.xchange > 0 and self._x + self.width - (-self.world_x) > const.SCREEN_WIDTH / 2 + self.width:
            self.world_x = -(self._x + self.width) + const.SCREEN_WIDTH / 2 + self.width
            ret += 1
        if self.xchange < 0 and self._x - (-self.world_x) < const.SCREEN_WIDTH / 2 - self.width:
            self.world_x = -self._x + const.SCREEN_WIDTH / 2 - self.width
            ret += 1
        if self.ychange > 0 and self._y + self.height - (-self.world_y) > const.SCREEN_HEIGHT - const.SCREEN_HEIGHT / 4:
            self.world_y = -(self._y + self.height) + const.SCREEN_HEIGHT - const.SCREEN_HEIGHT / 4
            ret += 1
        if self.ychange < 0 and self._y - (-self.world_y) < const.SCREEN_HEIGHT / 4:
            self.world_y = -self._y + const.SCREEN_HEIGHT / 4
            ret += 1
        if ret:
            self._scroll_world()

    def _world_metrics(self) -> dict[str, Any]:
        return {
            "world_x": float(self.world_x),
            "world_y": float(self.world_y),
            "worldpos_x": int(self.worldpos[0]),
            "worldpos_y": int(self.worldpos[1]),
            "stw": AS_STW,
            "sth": AS_STH,
            "spw": AS_SPW,
            "sph": AS_SPH,
            "maxheight": self.map_height * const.TILE_SIZE - const.SCREEN_HEIGHT,
        }

    def _map_tile_empty_at(self, x: float, y: float) -> bool:
        tile_x = math.floor(x / const.TILE_SIZE)
        tile_y = math.floor(y / const.TILE_SIZE)
        if tile_x < 0 or tile_x >= self.map_width or tile_y < 0 or tile_y >= self.map_height:
            return False
        return self.map_data[tile_y][tile_x][0] == 0

    def _projectile_should_remove(self, x: float, y: float) -> bool:
        tile_x = math.floor(float(x) / const.TILE_SIZE)
        tile_y = math.floor(float(y) / const.TILE_SIZE)
        if tile_x < 0 or tile_x >= self.map_width or tile_y < 0 or tile_y >= self.map_height:
            return True
        if self.map_data[tile_y][tile_x][0] != 0:
            return True
        return (
            tile_x < self.worldpos[0] - 1
            or tile_x > self.worldpos[0] + AS_STW + 1
            or tile_y < self.worldpos[1] - 1
            or tile_y > self.worldpos[1] + AS_STH + 1
        )

    def _bullet_should_remove(self, bullet: dict[str, Any]) -> bool:
        return self._projectile_should_remove(float(bullet["x"]), float(bullet["y"]))

    def _add_enemy(
        self,
        health: int = HELI_DEFAULT_HEALTH,
        *,
        x: float | None = None,
        y: float | None = None,
        visible: bool | None = None,
    ) -> int:
        enemy_id = self.next_enemy_id
        self.next_enemy_id += 1
        if x is None and y is None:
            spawn_x, spawn_y = self._as_enemy_spawn_position()
            spawn_visible = False if visible is None else bool(visible)
        else:
            spawn_x = self._x + HELI_TARGET_X_OFFSET if x is None else float(x)
            spawn_y = HELI_TRACE_TARGET_Y if y is None else float(y)
            spawn_visible = True if visible is None else bool(visible)
        self.enemies.append(
            self._make_enemy_dict(enemy_id, health, spawn_x, spawn_y, spawn_visible)
        )
        return enemy_id

    def _as_enemy_spawn_position(self) -> tuple[float, float]:
        metrics = self._world_metrics()
        if int(self.np_random.integers(0, 3)):
            if int(self.np_random.integers(0, 2)):
                return -self.world_x - HELI_BODY_WIDTH, float(metrics["maxheight"])
            return -self.world_x + metrics["spw"] + HELI_BODY_WIDTH, float(metrics["maxheight"])
        return (
            -self.world_x + metrics["spw"] / 2,
            metrics["worldpos_y"] * const.TILE_SIZE - HELI_BODY_HEIGHT / 2,
        )

    def _make_enemy_dict(
        self,
        enemy_id: int,
        health: int,
        x: float,
        y: float,
        visible: bool,
    ) -> dict[str, Any]:
        self.total_enemies_spawned += 1
        return {
            "id": int(enemy_id),
            "type": "Heli",
            "x": float(x),
            "y": float(y),
            "xspeed": 0.0,
            "yspeed": 0.0,
            "tx": float(x),
            "ty": float(y),
            "health": int(health),
            "max_health": int(health),
            "lasthealth": int(health),
            "frame": int(self.np_random.integers(0, 2)) + 1,
            "visible": bool(visible),
            "onscreen": 150 + int(self.np_random.integers(0, 100)),
            "stepc": 0.0,
            "xt": 0,
            "yt": 0,
            "goto": None,
            "xdif": HELI_TARGET_X_OFFSET,
            "shoot": 0,
            "shots": 0,
            "rotation": 0.0,
            "gun_rotation": 0.0,
            "gun_target_rotation": 0.0,
            "gun_yscale": 100,
        }

    def _make_default_enemy(self, health: int) -> dict[str, Any]:
        enemy_id = self.next_enemy_id
        self.next_enemy_id += 1
        spawn_x, spawn_y = self._as_enemy_spawn_position()
        return self._make_enemy_dict(
            enemy_id,
            health,
            spawn_x,
            spawn_y,
            False,
        )

    def _heli_gun_offset(self, enemy: dict[str, Any]) -> tuple[float, float]:
        return HELI_GUN_FRAME2_OFFSET if int(enemy.get("frame", 1)) == 2 else HELI_GUN_FRAME1_OFFSET

    def _rotate_offset(self, x: float, y: float, rotation: float) -> tuple[float, float]:
        radians = math.radians(rotation)
        return (
            math.cos(radians) * x - math.sin(radians) * y,
            math.sin(radians) * x + math.cos(radians) * y,
        )

    def _heli_gun_pivot_world_pos(self, enemy: dict[str, Any]) -> tuple[float, float]:
        gun_x, gun_y = self._heli_gun_offset(enemy)
        offset_x, offset_y = self._rotate_offset(gun_x, gun_y, float(enemy.get("rotation", 0.0)))
        return float(enemy["x"]) + offset_x, float(enemy["y"]) + offset_y

    def _heli_gun_barrel_world_pos(self, enemy: dict[str, Any]) -> tuple[float, float]:
        pivot_x, pivot_y = self._heli_gun_pivot_world_pos(enemy)
        barrel_y = (
            -FLASH_MACHINEGUN_BARREL_Y
            if int(enemy.get("gun_yscale", 100)) < 0
            else FLASH_MACHINEGUN_BARREL_Y
        )
        rotation = float(enemy.get("rotation", 0.0)) + float(enemy.get("gun_rotation", 0.0))
        offset_x, offset_y = self._rotate_offset(
            FLASH_MACHINEGUN_BARREL_X,
            barrel_y,
            rotation,
        )
        return pivot_x + offset_x, pivot_y + offset_y

    def _enemy_hit_rect(self, enemy: dict[str, Any]) -> tuple[float, float, float, float]:
        left = float(enemy["x"]) + HELI_HIT_OFFSET_X
        top = float(enemy["y"]) + HELI_HIT_OFFSET_Y
        return left, top, left + HELI_HIT_WIDTH, top + HELI_HIT_HEIGHT

    def _player_hit_rect(self) -> tuple[float, float, float, float]:
        left = self._x + self.width / 2 - self.playerwidth / 2
        top = self._y + self.height / 2 - self.playerheight / 2
        return left, top, left + self.playerwidth, top + self.playerheight

    def _bullet_hit_enemy(self, bullet: dict[str, Any]) -> int | None:
        bx = float(bullet["x"])
        by = float(bullet["y"])
        for enemy in self.enemies:
            if int(enemy["health"]) <= 0:
                continue
            left, top, right, bottom = self._enemy_hit_rect(enemy)
            if left <= bx <= right and top <= by <= bottom:
                damage = int(bullet["damage"])
                enemy["health"] = int(enemy["health"]) - damage
                self.score += damage
                self.hits += 1
                return int(enemy["id"])
        return None

    def _add_enemy_bullet(
        self,
        x: float,
        y: float,
        rotation: float,
        speed: float = ENEMY_BULLET_SPEED,
    ) -> int:
        radians = math.radians(rotation)
        bullet_id = self.next_enemy_bullet_id
        self.next_enemy_bullet_id += 1
        self.total_enemy_bullets_spawned += 1
        self.enemy_bullets.append(
            {
                "id": bullet_id,
                "x": float(x),
                "y": float(y),
                "xspeed": float(speed) * math.cos(radians),
                "yspeed": float(speed) * math.sin(radians),
                "rotation": float(rotation),
                "damage": ENEMY_BULLET_DAMAGE,
                "frame": 1,
                "age": 0,
            }
        )
        return bullet_id

    def _enemy_bullet_hit_player(self, bullet: dict[str, Any]) -> bool:
        bx = float(bullet["x"])
        by = float(bullet["y"])
        left, top, right, bottom = self._player_hit_rect()
        return left <= bx <= right and top <= by <= bottom

    def _update_enemy_bullets(self) -> dict[str, Any]:
        event = self._empty_enemy_event()
        active: list[dict[str, Any]] = []
        for bullet in self.enemy_bullets:
            bullet = dict(bullet)
            bullet["x"] = float(bullet["x"]) + float(bullet["xspeed"])
            bullet["y"] = float(bullet["y"]) + float(bullet["yspeed"])
            bullet["age"] = int(bullet["age"]) + 1
            if self._enemy_bullet_hit_player(bullet):
                damage = int(bullet["damage"])
                self.health -= damage
                self.enemy_bullet_hits += 1
                self.last_player_damage_tick = self.tick + 1
                self.last_player_damage_amount = damage
                event["player_damage"] += damage
                event["removed_enemy_bullet_ids"].append(int(bullet["id"]))
            elif self._projectile_should_remove(float(bullet["x"]), float(bullet["y"])):
                event["removed_enemy_bullet_ids"].append(int(bullet["id"]))
            else:
                active.append(bullet)
        self.enemy_bullets = active
        return event

    def _maybe_spawn_default_heli(self, contact: dict[str, Any], event: dict[str, Any]) -> None:
        if not self.pending_default_heli or not contact.get("ground"):
            return
        # AS adds the first Heli after heroStart completes; first ground contact is
        # the current minimal proxy until the parachute/start lifecycle exists.
        enemy_id = self._add_enemy(HELI_DEFAULT_HEALTH)
        self.pending_default_heli = False
        self.default_heli_spawned = True
        event["spawned_enemy_ids"].append(enemy_id)

    def _spawn_replacement_heli(self, active: list[dict[str, Any]], event: dict[str, Any]) -> None:
        replacement = self._make_default_enemy(HELI_DEFAULT_HEALTH)
        active.append(replacement)
        event["spawned_enemy_ids"].append(int(replacement["id"]))

    def _update_enemies(self) -> dict[str, Any]:
        event = self._empty_enemy_event()
        metrics = self._world_metrics()
        active: list[dict[str, Any]] = []
        for enemy in self.enemies:
            enemy = dict(enemy)
            if int(enemy["health"]) <= 0:
                self.helis += 1
                self.rthelis += 1
                event["killed_enemy_ids"].append(int(enemy["id"]))
                if self.respawn_helis:
                    self._spawn_replacement_heli(active, event)
                continue

            enemy["stepc"] = float(enemy["stepc"]) + 1.0
            move = False
            if float(enemy["stepc"]) >= 1.0:
                move = True
                enemy["stepc"] = float(enemy["stepc"]) - 1.0

            if int(enemy.get("onscreen", 0)) <= 0:
                if enemy.get("goto") is None:
                    enemy["goto"] = int(self.np_random.integers(0, 10))
                goto = int(enemy["goto"])
                if goto < 4:
                    enemy["tx"] = metrics["worldpos_x"] * const.TILE_SIZE - metrics["spw"] * 2
                elif goto < 8:
                    enemy["tx"] = metrics["worldpos_x"] * const.TILE_SIZE + metrics["spw"] * 2
                else:
                    enemy["ty"] = metrics["worldpos_y"] * const.TILE_SIZE - metrics["sph"]

                if (
                    float(enemy["y"]) < metrics["worldpos_y"] * const.TILE_SIZE - HELI_BODY_HEIGHT
                    or float(enemy["x"]) < metrics["worldpos_x"] * const.TILE_SIZE - HELI_BODY_WIDTH
                    or float(enemy["x"]) > metrics["worldpos_x"] * const.TILE_SIZE + metrics["spw"] + HELI_BODY_WIDTH
                ):
                    replacement = self._make_default_enemy(int(enemy["health"]))
                    active.append(replacement)
                    event["spawned_enemy_ids"].append(int(replacement["id"]))
                    continue
            else:
                if move:
                    xt = int(enemy.get("xt", 0))
                    if xt % 75 == 1:
                        random_width = max(1, int(metrics["spw"] - HELI_BODY_WIDTH / 2))
                        enemy["xdif"] = (
                            (-metrics["spw"]) / 2
                            + int(self.np_random.integers(0, random_width))
                            + HELI_BODY_WIDTH / 2
                        )
                    enemy["xt"] = xt + 1
                enemy["tx"] = float(self._x) + float(enemy.get("xdif", HELI_TARGET_X_OFFSET))
                if float(enemy["tx"]) < HELI_BODY_WIDTH / 2:
                    enemy["tx"] = HELI_BODY_WIDTH / 2
                map_max_x = self.map_width * const.TILE_SIZE - HELI_BODY_WIDTH / 2
                if float(enemy["tx"]) > map_max_x:
                    enemy["tx"] = map_max_x
                if self.hjump:
                    enemy["ty"] = min(
                        self.map_height * const.TILE_SIZE - metrics["sph"] / 2 - 100,
                        self._y + 50 + int(self.np_random.integers(0, 50)),
                    )
                elif move:
                    yt = int(enemy.get("yt", 0))
                    if yt % 40 == 1:
                        enemy["ty"] = self._y - metrics["sph"] / 2 - (-2 + int(self.np_random.integers(0, 4))) * 10
                    enemy["yt"] = yt + 1

            dx = float(enemy["tx"]) - float(enemy["x"])
            dy = float(enemy["ty"]) - float(enemy["y"])
            if (
                int(enemy.get("onscreen", 0)) < 0
                or float(enemy["y"]) < metrics["worldpos_y"] * const.TILE_SIZE
                or float(enemy["x"]) < metrics["worldpos_x"] * const.TILE_SIZE
                or float(enemy["x"]) > metrics["worldpos_x"] * const.TILE_SIZE + metrics["spw"]
            ):
                enemy["xspeed"] = float(enemy["xspeed"]) + dx / 100.0
                enemy["yspeed"] = float(enemy["yspeed"]) + dy / 20.0
            else:
                enemy["xspeed"] = float(enemy["xspeed"]) + dx / 200.0
                enemy["yspeed"] = float(enemy["yspeed"]) + dy / 100.0
            if move:
                rotation = math.floor(float(enemy["xspeed"]) / 20.0 * 15.0)
                enemy["rotation"] = float(rotation if abs(rotation) > 2 else 0)
            enemy["x"] = float(enemy["x"]) + float(enemy["xspeed"])
            enemy["y"] = float(enemy["y"]) + float(enemy["yspeed"])
            if move:
                enemy["xspeed"] = float(enemy["xspeed"]) * 0.9
                enemy["yspeed"] = float(enemy["yspeed"]) * 0.9

            gun_x, gun_y = self._heli_gun_offset(enemy)
            enemy["gun_target_rotation"] = (
                360.0
                - math.degrees(
                    math.atan2(
                        float(enemy["x"]) + gun_x - self._x - self.width / 2,
                        float(enemy["y"]) + gun_y - self._y,
                    )
                )
                - 90.0
                - float(enemy["rotation"])
            )
            diff = self._shortest_angle_diff(
                float(enemy["gun_target_rotation"]),
                float(enemy.get("gun_rotation", 0.0)),
            )
            enemy["gun_rotation"] = float(enemy.get("gun_rotation", 0.0)) + diff / max(
                1,
                HELI_GUN_SMOOTHING_BASE - self.level,
            )
            enemy["gun_yscale"] = -100 if float(enemy["gun_rotation"]) > 90 or float(enemy["gun_rotation"]) < -90 else 100

            if move:
                shoot = int(enemy.get("shoot", 0))
                if shoot % max(10, HELI_SHOOT_RELOAD_BASE - self.level) == 1:
                    barrel_x, barrel_y = self._heli_gun_barrel_world_pos(enemy)
                    spread = int(self.np_random.integers(0, 10))
                    bullet_id = self._add_enemy_bullet(
                        barrel_x,
                        barrel_y,
                        float(enemy["gun_rotation"]) - 5.0 + spread,
                        ENEMY_BULLET_SPEED,
                    )
                    enemy["shots"] = int(enemy.get("shots", 0)) + 1
                    event["spawned_enemy_bullet_ids"].append(bullet_id)
                enemy["shoot"] = shoot + 1

            y = math.floor((float(enemy["y"]) - HELI_BODY_HEIGHT / 2) / const.TILE_SIZE)
            x = math.floor((float(enemy["x"]) - HELI_BODY_WIDTH / 2) / const.TILE_SIZE)
            y2 = math.floor((float(enemy["y"]) + HELI_BODY_HEIGHT / 2) / const.TILE_SIZE)
            x2 = math.floor((float(enemy["x"]) + HELI_BODY_WIDTH / 2) / const.TILE_SIZE)
            if (
                x2 < metrics["worldpos_x"] - 1
                or x > metrics["worldpos_x"] + AS_STW + 1
                or y2 < metrics["worldpos_y"] - 1
                or y > metrics["worldpos_y"] + AS_STH + 1
            ):
                enemy["visible"] = False
            else:
                if move:
                    enemy["onscreen"] = int(enemy.get("onscreen", 0)) - 1
                enemy["visible"] = True
            active.append(enemy)
        self.enemies = active
        return event

    def _machinegun_visual_pivot_world_pos(self) -> tuple[float, float]:
        return self._x + FLASH_HERO_GUN_X, self._y + FLASH_HERO_GUN_Y

    def _gun_is_flipped(self, rotation: float) -> bool:
        normalized = rotation % 360.0
        return 90.0 < normalized < 270.0

    def _machinegun_visual_barrel_world_pos(self, rotation: float) -> tuple[float, float]:
        pivot_x, pivot_y = self._machinegun_visual_pivot_world_pos()
        barrel_y = (
            -FLASH_MACHINEGUN_BARREL_Y
            if self._gun_is_flipped(rotation)
            else FLASH_MACHINEGUN_BARREL_Y
        )
        radians = math.radians(rotation)
        return (
            pivot_x
            + math.cos(radians) * FLASH_MACHINEGUN_BARREL_X
            - math.sin(radians) * barrel_y,
            pivot_y
            + math.sin(radians) * FLASH_MACHINEGUN_BARREL_X
            + math.cos(radians) * barrel_y,
        )

    def _gun_barrel_world_pos(self, rotation: float) -> tuple[float, float]:
        pivot_x = self._x + self.width / 2.0
        pivot_y = self._y + self.height / 2.0
        radians = math.radians(rotation)
        return (
            pivot_x + math.cos(radians) * GUN_BARREL_LENGTH,
            pivot_y + math.sin(radians) * GUN_BARREL_LENGTH,
        )

    def _add_bullet(self, x: float, y: float, rotation: float, damage: int) -> int:
        radians = math.radians(rotation)
        bullet_id = self.next_bullet_id
        self.next_bullet_id += 1
        self.total_bullets_spawned += 1
        self.bullets.append(
            {
                "id": bullet_id,
                "x": float(x),
                "y": float(y),
                "xspeed": MACHINEGUN_SPEED * math.cos(radians),
                "yspeed": MACHINEGUN_SPEED * math.sin(radians),
                "rotation": float(rotation),
                "damage": int(damage),
                "frame": MACHINEGUN_BULLET_FRAME,
                "age": 0,
            }
        )
        return bullet_id

    def _update_bullets(self) -> list[int]:
        active = []
        removed_ids: list[int] = []
        for bullet in self.bullets:
            bullet = dict(bullet)
            bullet["x"] = float(bullet["x"]) + float(bullet["xspeed"])
            bullet["y"] = float(bullet["y"]) + float(bullet["yspeed"])
            bullet["age"] = int(bullet["age"]) + 1
            if self._bullet_hit_enemy(bullet) is not None:
                removed_ids.append(int(bullet["id"]))
            elif self._bullet_should_remove(bullet):
                removed_ids.append(int(bullet["id"]))
            else:
                active.append(bullet)
        self.bullets = active
        return removed_ids

    def _update_machinegun(self, aim_bin: int, fire_action: int) -> dict[str, Any]:
        event = self._empty_gun_event()
        self.aim_rotation = self.aim_bin_to_rotation(aim_bin)
        self.gun_rotation += self._shortest_angle_diff(self.aim_rotation, self.gun_rotation) / 2.0

        if not math.isinf(self.gun_reloadtime):
            self.gun_reloadtime += 1

        if fire_action and self.gun_reloadtime >= MACHINEGUN_RELOADTIME and self.gun_bullets > 0:
            self.gun_shots += 1
            self.gun_reloadtime = 0
            if not math.isinf(self.gun_bullets):
                self.gun_bullets -= 1

            muzzle_x, muzzle_y = self._gun_barrel_world_pos(self.gun_rotation)
            if self._map_tile_empty_at(muzzle_x, muzzle_y):
                spread = int(self.np_random.integers(0, MACHINEGUN_SPREAD_CHOICES)) - 2
                bullet_id = self._add_bullet(
                    muzzle_x,
                    muzzle_y,
                    self.gun_rotation + spread,
                    MACHINEGUN_DAMAGE,
                )
                event["spawned_bullet_id"] = bullet_id
            else:
                event["spawn_blocked"] = True
            event["fired"] = True

        return event

    def step(self, action):
        action = self._normalize_action(action)
        move_action, jump_action, duck_action, boost_action, aim_bin, fire_action = action
        before_score = int(self.score)
        contact = self._empty_contact()
        gun_event = self._empty_gun_event()
        gun_event["removed_bullet_ids"] = self._update_bullets()
        enemy_event = self._update_enemy_bullets()
        enemy_update_event = self._update_enemies()
        enemy_event["removed_enemy_bullet_ids"].extend(
            enemy_update_event["removed_enemy_bullet_ids"]
        )
        enemy_event["spawned_enemy_bullet_ids"].extend(
            enemy_update_event["spawned_enemy_bullet_ids"]
        )
        enemy_event["spawned_enemy_ids"].extend(enemy_update_event["spawned_enemy_ids"])
        enemy_event["killed_enemy_ids"].extend(enemy_update_event["killed_enemy_ids"])
        enemy_event["player_damage"] += int(enemy_update_event["player_damage"])
        self.total_player_damage += int(enemy_event["player_damage"])

        if move_action == 0:
            self.facing_right = False
        elif move_action == 2:
            self.facing_right = True

        if duck_action == 1:
            self.playerwidth = 2 * self.defplayerwidth / 3
            self.playerheight = 2 * self.defplayerheight / 3
            self.duck = 1
        else:
            if self.duck == 1:
                self._y -= 2 * self.defplayerwidth / 3
            self.playerwidth = self.defplayerwidth
            self.playerheight = self.defplayerheight
            self.duck = 0

        if not self.duck:
            if move_action == 0:
                if self.xspeed > -5:
                    self.xspeed -= 1
            if move_action == 2:
                if self.xspeed < 5:
                    self.xspeed += 1

        if self.yspeed > 0 or self.yspeed < 0:
            if not self.jump:
                self.jump = 1

        if self.hyperjump < 150:
            self.hyperjump += 1

        if (
            self.hyperjump >= 150
            and boost_action == 1
            and (not self.jump or not self.jump2)
            and not self.hjump
        ):
            if not self.boostK:
                self.yspeed = -32
                if self.jump:
                    self.jump2 = 1
                self.jump = 1
                self.hjump = 1
                self.hyperjump = 0
            self.boostK = 1
        else:
            self.boostK = 0

        if jump_action == 1:
            if self.up > 0:
                self.yspeed = min(self.yspeed, -8)
                if not self.upk:
                    if not self.jump:
                        self.jump = 1
                    elif not self.jump2:
                        self.jump2 = 1
                self.up -= 1
            self.upk = 1
        else:
            if not self.jump or (not self.jump2 and not self.duck):
                self.up = 6
            else:
                self.up = 0
            self.upk = 0

        if move_action == 1 or (self.duck and not self.jump):
            if self.xspeed > 0:
                self.xspeed -= 1
            elif self.xspeed < 0:
                self.xspeed += 1

        if self.xspeed > 6:
            self.xspeed -= 1
        if self.xspeed < -6:
            self.xspeed += 1

        if self.yspeed > const.TILE_SIZE:
            self.yspeed = const.TILE_SIZE
        if self.yspeed < -const.TILE_SIZE:
            self.yspeed = -const.TILE_SIZE
        self.yspeed += 1

        self.xchange = self.xspeed
        self.ychange = self.yspeed

        tilex = math.floor(
            (self._x + self.xchange + self.width / 2 - self.playerwidth / 2)
            / const.TILE_SIZE
        )
        tile2x = math.floor(
            (self._x + self.xchange + self.width / 2 + self.playerwidth / 2)
            / const.TILE_SIZE
        )
        tiley = math.floor(
            (self._y + 1 + self.height / 2 - self.playerheight / 2) / const.TILE_SIZE
        )
        tile2y = math.floor(
            (self._y + self.height / 2 + self.playerheight / 2) / const.TILE_SIZE
        )

        if self.xchange != 0:
            if self.xchange > 0:
                if tile2x >= self.map_width:
                    hits = 1
                else:
                    hits = self._hit_check(tiley, tile2x, tile2y, tile2x, 1, 1, 1)

                if not hits:
                    self._x += self.xchange
                else:
                    self._x = (
                        tile2x * const.TILE_SIZE
                        - self.width
                        + (self.width - self.playerwidth) / 2
                        - 1
                    )
                    self.xspeed = 0
                    contact["x_blocked"] = True
                    contact["wall"] = "right"
                    contact["hit_count"] += int(hits)
            else:
                if tilex < 0:
                    hits = 1
                else:
                    hits = self._hit_check(tiley, tilex, tile2y, tilex, 1, 1, 1)

                if not hits:
                    self._x += self.xchange
                else:
                    self._x = (
                        (tilex + 1) * const.TILE_SIZE
                        - (self.width - self.playerwidth) / 2
                        - 1
                    )
                    self.xspeed = 0
                    contact["x_blocked"] = True
                    contact["wall"] = "left"
                    contact["hit_count"] += int(hits)

        tilex = math.floor(
            (self._x + 1 + self.width / 2 - self.playerwidth / 2) / const.TILE_SIZE
        )
        tile2x = math.floor(
            (self._x + self.width / 2 + self.playerwidth / 2) / const.TILE_SIZE
        )
        tiley = math.floor(
            (self._y + self.ychange + self.height / 2 - self.playerheight / 2)
            / const.TILE_SIZE
        )
        tile2y = math.floor(
            (self._y + self.ychange + self.height / 2 + self.playerheight / 2)
            / const.TILE_SIZE
        )

        if self.ychange != 0:
            if self.ychange > 0:
                if not self._hit_check(tile2y, tilex, tile2y, tile2x, 0, 0, 0):
                    self._y += self.ychange
                else:
                    self._y = (
                        tile2y * const.TILE_SIZE
                        - self.height
                        + (self.height - self.playerheight) / 2
                        - 1
                    )
                    self.yspeed = 0
                    self.jump = 0
                    self.jump2 = 0
                    self.hjump = 0
                    contact["y_blocked"] = True
                    contact["ground"] = True
                    contact["hit_count"] += 1
            elif self.ychange < 0:
                if not self._hit_check(tiley, tilex, tiley, tile2x, 0, 0, 0):
                    self._y += self.ychange
                else:
                    self._y = (
                        (tiley + 1) * const.TILE_SIZE
                        - (self.height - self.playerheight) / 2
                        - 1
                    )
                    self.yspeed = 0
                    self.jump = 1
                    self.jump2 = 1
                    self.up = 0
                    contact["y_blocked"] = True
                    contact["ceiling"] = True
                    contact["hit_count"] += 1

        gun_event.update(self._update_machinegun(aim_bin, fire_action))
        self._update_world_after_player()
        self._maybe_spawn_default_heli(contact, enemy_event)
        self.lastHealth = int(self.health)

        fell = bool(self._y > self.map_height * const.TILE_SIZE)
        player_dead = bool(self.health <= 0)
        self.episode_step_count += 1

        reward_breakdown = None
        termination_reason = "none"
        truncated = False
        if self.training_profile == "legacy":
            reward = 0.1
            terminated = fell
            if terminated:
                reward = -10.0
                termination_reason = "fall"
        else:
            killed_helis = len(enemy_event["killed_enemy_ids"])
            score_delta = max(0, int(self.score) - before_score)
            player_damage = int(enemy_event["player_damage"])
            terminated = fell or player_dead
            if fell:
                termination_reason = "fall"
            elif player_dead:
                termination_reason = "player_death"
            elif (
                self.max_episode_steps is not None
                and self.episode_step_count >= self.max_episode_steps
            ):
                truncated = True
                termination_reason = "time_limit"

            reward_breakdown = {
                "living": 0.01,
                "enemy_damage": 0.05 * float(score_delta),
                "kill": 5.0 * float(killed_helis),
                "player_damage": -0.10 * float(player_damage),
                "terminal": -25.0 if terminated else 0.0,
            }
            reward = float(sum(reward_breakdown.values()))

        self.tick += 1
        self.last_action = action
        self.last_reward = float(reward)
        self.last_terminated = terminated
        self.last_truncated = truncated
        self.last_termination_reason = termination_reason
        self.last_reward_breakdown = reward_breakdown
        self.last_contact = contact
        self.last_camera = self.get_camera()
        self.last_gun_event = gun_event
        self.last_enemy_event = enemy_event

        if self.auto_render and self.render_mode in ["human", "rgb_array"]:
            self.render()

        return self._get_obs(), reward, terminated, truncated, self.get_debug_info()

    def get_camera(self) -> tuple[float, float]:
        return float(self.world_x), float(self.world_y)

    def render(
        self,
        *,
        debug_overlay: bool = False,
        debug_collision: bool = False,
        debug_lines: list[str] | None = None,
    ):
        if self.render_mode is None:
            return None

        self._ensure_pygame_ready()
        if not self.images:
            self._load_images()

        canvas = pygame.Surface(self.window_size)
        cam_x, cam_y = self.get_camera()
        self.last_camera = (cam_x, cam_y)

        bg = self.images.get("bg")
        if bg:
            for i in range(0, const.SCREEN_WIDTH + bg.get_width(), bg.get_width()):
                for j in range(0, const.SCREEN_HEIGHT + bg.get_height(), bg.get_height()):
                    canvas.blit(bg, (i, j))
        else:
            canvas.fill((135, 206, 235))

        bg1 = self.images.get("bg1")
        if bg1:
            parallax_x = (cam_x * 0.5) % bg1.get_width()
            y = const.SCREEN_HEIGHT - bg1.get_height()
            canvas.blit(bg1, (parallax_x - bg1.get_width(), y))
            canvas.blit(bg1, (parallax_x, y))
            canvas.blit(bg1, (parallax_x + bg1.get_width(), y))

        for ty, row in enumerate(self.map_data):
            for tx, tile in enumerate(row):
                collision_type, graphic_idx = tile[0], tile[1]
                if collision_type != 0:
                    img = self.tiles.get(graphic_idx) or self.tiles.get(1)
                    rect = pygame.Rect(
                        tx * const.TILE_SIZE + cam_x - 1,
                        ty * const.TILE_SIZE + cam_y - 1,
                        const.TILE_SIZE + 2,
                        const.TILE_SIZE + 2,
                    )
                    if img:
                        canvas.blit(img, rect.topleft)
                    else:
                        pygame.draw.rect(canvas, (100, 100, 100), rect)

        self._draw_enemies(canvas, cam_x, cam_y)

        if self.duck:
            sprite = self.images.get("duck")
        elif self.jump:
            sprite = self.images.get("jump2") if self.jump2 else self.images.get("jump")
        elif self.xchange != 0:
            walk_frame = "walk1" if (self.tick // 4) % 2 == 0 else "walk2"
            sprite = self.images.get(walk_frame)
        else:
            sprite = self.images.get("guy")

        if sprite:
            sprite_x = self._x + cam_x + self.width / 2 - sprite.get_width() / 2
            sprite_y = self._y + cam_y + self.height - sprite.get_height()
            canvas.blit(sprite, (sprite_x, sprite_y))
        else:
            rect_x = self._x + self.width / 2 - self.playerwidth / 2 + cam_x
            rect_y = self._y + self.height / 2 - self.playerheight / 2 + cam_y
            pygame.draw.rect(
                canvas,
                (255, 0, 0),
                pygame.Rect(rect_x, rect_y, self.playerwidth, self.playerheight),
            )

        self._draw_machinegun(canvas, cam_x, cam_y)

        bullet_img = self.images.get("bullet")
        for bullet in self.bullets:
            bullet_x = float(bullet["x"]) + cam_x
            bullet_y = float(bullet["y"]) + cam_y
            if bullet_img:
                rotated = pygame.transform.rotate(bullet_img, -float(bullet["rotation"]))
                rect = rotated.get_rect(center=(bullet_x, bullet_y))
                canvas.blit(rotated, rect)
            else:
                pygame.draw.circle(canvas, (255, 196, 0), (round(bullet_x), round(bullet_y)), 3)

        enemy_bullet_img = self.images.get("enemy_bullet")
        for bullet in self.enemy_bullets:
            bullet_x = float(bullet["x"]) + cam_x
            bullet_y = float(bullet["y"]) + cam_y
            if enemy_bullet_img:
                rotated = pygame.transform.rotate(enemy_bullet_img, -float(bullet["rotation"]))
                rect = rotated.get_rect(center=(bullet_x, bullet_y))
                canvas.blit(rotated, rect)
            else:
                pygame.draw.circle(canvas, (255, 80, 0), (round(bullet_x), round(bullet_y)), 3)

        self._draw_player_health_hud(canvas)

        if debug_collision:
            self._draw_collision_debug(canvas, cam_x, cam_y)

        display_canvas = canvas
        if debug_overlay:
            display_canvas = pygame.Surface(
                (self.window_size[0] + DEBUG_PANEL_WIDTH, self.window_size[1])
            )
            display_canvas.fill((12, 14, 16))
            display_canvas.blit(canvas, (0, 0))
            self._draw_debug_panel(display_canvas, debug_lines or [], self.window_size[0])

        if self.render_mode == "human":
            if self.window is None or self.window.get_size() != display_canvas.get_size():
                self.window = pygame.display.set_mode(display_canvas.get_size())
            self.window.blit(display_canvas, display_canvas.get_rect())
            pygame.display.update()
            return None
        if self.render_mode == "rgb_array":
            return np.transpose(pygame.surfarray.array3d(display_canvas), axes=(1, 0, 2))
        return None

    def _draw_surface_at_pivot(
        self,
        canvas: pygame.Surface,
        source: pygame.Surface,
        pivot_x: float,
        pivot_y: float,
        local_pivot: pygame.math.Vector2,
        rotation: float,
    ) -> None:
        draw_angle = -rotation
        source_rect = source.get_rect(
            topleft=(pivot_x - local_pivot.x, pivot_y - local_pivot.y)
        )
        pivot = pygame.math.Vector2(pivot_x, pivot_y)
        offset_center_to_pivot = pivot - pygame.math.Vector2(source_rect.center)
        rotated_offset = offset_center_to_pivot.rotate(-draw_angle)
        rotated = pygame.transform.rotate(source, draw_angle)
        rotated_center = pivot - rotated_offset
        rotated_rect = rotated.get_rect(center=(rotated_center.x, rotated_center.y))
        canvas.blit(rotated, rotated_rect)

    def _draw_player_health_hud(self, canvas: pygame.Surface) -> None:
        base = self.images.get("hud_health_base")
        fill = self.images.get("hud_health_fill")
        x = HUD_HEALTH_X + HUD_HEALTH_BITMAP_X
        y = HUD_HEALTH_Y + HUD_HEALTH_BITMAP_Y

        if base is None or fill is None:
            sprite = self.images.get("hud_health")
            if sprite is None:
                return
            health_fraction = max(0.0, min(1.0, float(self.health) / PLAYER_DEFAULT_HEALTH))
            visible_h = round(sprite.get_height() * health_fraction)
            if visible_h <= 0:
                return
            src_y = sprite.get_height() - visible_h
            canvas.blit(
                sprite,
                (HUD_HEALTH_X, HUD_HEALTH_Y + src_y),
                pygame.Rect(0, src_y, sprite.get_width(), visible_h),
            )
            return

        canvas.blit(base, (x, y))

        health_fraction = max(0.0, min(1.0, float(self.health) / PLAYER_DEFAULT_HEALTH))
        visible_h = round(fill.get_height() * health_fraction)
        if visible_h <= 0:
            return

        src_y = fill.get_height() - visible_h
        canvas.blit(
            fill,
            (x, y + src_y),
            pygame.Rect(0, src_y, fill.get_width(), visible_h),
        )

    def _draw_machinegun(self, canvas: pygame.Surface, cam_x: float, cam_y: float) -> None:
        gun = self.images.get("machinegun")
        if gun is None:
            return

        world_pivot_x, world_pivot_y = self._machinegun_visual_pivot_world_pos()
        pivot_x = world_pivot_x + cam_x
        pivot_y = world_pivot_y + cam_y
        rotation = self.gun_rotation % 360.0
        local_pivot = pygame.math.Vector2(MACHINEGUN_SPRITE_ORIGIN)
        source = gun

        if self._gun_is_flipped(rotation):
            # AS flips local gun y-scale when aiming left, then applies rotation.
            source = pygame.transform.flip(gun, False, True)
            local_pivot.y = source.get_height() - local_pivot.y

        self._draw_surface_at_pivot(canvas, source, pivot_x, pivot_y, local_pivot, rotation)

    def _draw_enemies(self, canvas: pygame.Surface, cam_x: float, cam_y: float) -> None:
        for enemy in self.enemies:
            if not enemy.get("visible", True):
                continue
            image = self.images.get(f"heli{int(enemy.get('frame', 1))}") or self.images.get("heli1")
            screen_x = float(enemy["x"]) + cam_x
            screen_y = float(enemy["y"]) + cam_y
            if image:
                rotated = pygame.transform.rotate(image, -float(enemy.get("rotation", 0.0)))
                rect = rotated.get_rect(center=(screen_x, screen_y))
                canvas.blit(rotated, rect)
            else:
                pygame.draw.rect(
                    canvas,
                    (40, 80, 80),
                    pygame.Rect(screen_x - 106, screen_y - 53, 212, 106),
                )
            self._draw_heli_gun(canvas, enemy, cam_x, cam_y)

    def _draw_heli_gun(
        self,
        canvas: pygame.Surface,
        enemy: dict[str, Any],
        cam_x: float,
        cam_y: float,
    ) -> None:
        gun = self.images.get("machinegun")
        if gun is None:
            return
        pivot_world_x, pivot_world_y = self._heli_gun_pivot_world_pos(enemy)
        pivot_x = pivot_world_x + cam_x
        pivot_y = pivot_world_y + cam_y
        local_pivot = pygame.math.Vector2(MACHINEGUN_SPRITE_ORIGIN)
        source = gun
        if int(enemy.get("gun_yscale", 100)) < 0:
            source = pygame.transform.flip(gun, False, True)
            local_pivot.y = source.get_height() - local_pivot.y
        rotation = float(enemy.get("rotation", 0.0)) + float(enemy.get("gun_rotation", 0.0))
        self._draw_surface_at_pivot(canvas, source, pivot_x, pivot_y, local_pivot, rotation)

    def _draw_debug_panel(
        self,
        canvas: pygame.Surface,
        extra_lines: list[str],
        x_offset: int,
    ) -> None:
        if self.font is None:
            return
        enemy_healths = ",".join(
            f"{int(enemy['id'])}:{int(enemy['health'])}/{int(enemy['max_health'])}"
            for enemy in self.enemies
        )
        lines = [
            f"tick={self.tick} hash={self.state_hash()}",
            f"pos=({self._x:.2f},{self._y:.2f}) speed=({self.xspeed:.2f},{self.yspeed:.2f})",
            f"jump={self.jump}/{self.jump2} duck={self.duck} hjump={self.hjump} hyper={self.hyperjump}",
            f"action={self.last_action} camera=({self.last_camera[0]:.1f},{self.last_camera[1]:.1f})",
            f"gun=MachineGun rot={self.gun_rotation:.1f} reload={self._state_value(self.gun_reloadtime)} shots={self.gun_shots} bullets={len(self.bullets)}",
            f"combat=health:{self.health} last_damage:{self.last_player_damage_amount}@{self.last_player_damage_tick} score:{self.score} hits:{self.hits} helis:{self.helis}",
            f"enemies={len(self.enemies)} hp=[{enemy_healths}] kills={self.rthelis} pending_heli={self.pending_default_heli}",
            f"ebullets={len(self.enemy_bullets)} enemy_event={self.last_enemy_event}",
            f"gun_pivot=({self._machinegun_visual_pivot_world_pos()[0]:.1f},{self._machinegun_visual_pivot_world_pos()[1]:.1f}) barrel=({self._machinegun_visual_barrel_world_pos(self.gun_rotation)[0]:.1f},{self._machinegun_visual_barrel_world_pos(self.gun_rotation)[1]:.1f}) spawn=({self._gun_barrel_world_pos(self.gun_rotation)[0]:.1f},{self._gun_barrel_world_pos(self.gun_rotation)[1]:.1f})",
            f"contact={self.last_contact}",
        ]
        lines.extend(extra_lines)

        pad = 8
        line_h = 18
        panel = pygame.Rect(x_offset, 0, DEBUG_PANEL_WIDTH, self.window_size[1])
        pygame.draw.rect(canvas, (18, 21, 24), panel)
        pygame.draw.line(canvas, (72, 82, 90), (x_offset, 0), (x_offset, panel.height), 1)
        max_text_width = DEBUG_PANEL_WIDTH - pad * 2
        for idx, line in enumerate(lines):
            y = pad + idx * line_h
            if y + line_h > panel.height:
                break
            surface = self.font.render(
                self._fit_debug_line(line, max_text_width),
                True,
                (235, 238, 240),
            )
            canvas.blit(surface, (x_offset + pad, y))

    def _fit_debug_line(self, line: str, max_width: int) -> str:
        if self.font is None or self.font.size(line)[0] <= max_width:
            return line
        suffix = "..."
        value = line
        while value and self.font.size(value + suffix)[0] > max_width:
            value = value[:-1]
        return value + suffix if value else suffix

    def _draw_collision_debug(self, canvas: pygame.Surface, cam_x: float, cam_y: float) -> None:
        logical = pygame.Rect(self._x + cam_x, self._y + cam_y, self.width, self.height)
        hitbox = pygame.Rect(
            self._x + self.width / 2 - self.playerwidth / 2 + cam_x,
            self._y + self.height / 2 - self.playerheight / 2 + cam_y,
            self.playerwidth,
            self.playerheight,
        )
        pygame.draw.rect(canvas, (30, 144, 255), logical, 1)
        pygame.draw.rect(canvas, (255, 64, 64), hitbox, 1)
        for enemy in self.enemies:
            left, top, right, bottom = self._enemy_hit_rect(enemy)
            rect = pygame.Rect(left + cam_x, top + cam_y, right - left, bottom - top)
            pygame.draw.rect(canvas, (255, 196, 0), rect, 1)
            pivot_x, pivot_y = self._heli_gun_pivot_world_pos(enemy)
            barrel_x, barrel_y = self._heli_gun_barrel_world_pos(enemy)
            pygame.draw.circle(canvas, (0, 180, 255), (round(pivot_x + cam_x), round(pivot_y + cam_y)), 3, 1)
            pygame.draw.circle(canvas, (255, 80, 0), (round(barrel_x + cam_x), round(barrel_y + cam_y)), 3, 1)
        for bullet in self.enemy_bullets:
            pygame.draw.circle(
                canvas,
                (255, 80, 0),
                (round(float(bullet["x"]) + cam_x), round(float(bullet["y"]) + cam_y)),
                3,
                1,
            )

    def _state_value(self, value: float) -> int | float | str:
        if math.isinf(value):
            return "Infinity"
        rounded = round(float(value), 8)
        return int(rounded) if rounded == int(rounded) else rounded

    def _bullet_state(self, bullet: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": int(bullet["id"]),
            "x": round(float(bullet["x"]), 8),
            "y": round(float(bullet["y"]), 8),
            "xspeed": round(float(bullet["xspeed"]), 8),
            "yspeed": round(float(bullet["yspeed"]), 8),
            "rotation": round(float(bullet["rotation"]), 8),
            "damage": int(bullet["damage"]),
            "frame": int(bullet["frame"]),
            "age": int(bullet["age"]),
        }

    def _enemy_bullet_state(self, bullet: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": int(bullet["id"]),
            "x": round(float(bullet["x"]), 8),
            "y": round(float(bullet["y"]), 8),
            "xspeed": round(float(bullet["xspeed"]), 8),
            "yspeed": round(float(bullet["yspeed"]), 8),
            "rotation": round(float(bullet["rotation"]), 8),
            "damage": int(bullet["damage"]),
            "frame": int(bullet["frame"]),
            "age": int(bullet["age"]),
        }

    def _enemy_state(self, enemy: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": int(enemy["id"]),
            "type": str(enemy["type"]),
            "x": round(float(enemy["x"]), 8),
            "y": round(float(enemy["y"]), 8),
            "xspeed": round(float(enemy["xspeed"]), 8),
            "yspeed": round(float(enemy["yspeed"]), 8),
            "tx": round(float(enemy["tx"]), 8),
            "ty": round(float(enemy["ty"]), 8),
            "health": int(enemy["health"]),
            "max_health": int(enemy["max_health"]),
            "lasthealth": int(enemy["lasthealth"]),
            "frame": int(enemy["frame"]),
            "visible": bool(enemy["visible"]),
            "onscreen": int(enemy["onscreen"]),
            "stepc": round(float(enemy["stepc"]), 8),
            "xt": int(enemy["xt"]),
            "yt": int(enemy["yt"]),
            "goto": None if enemy.get("goto") is None else int(enemy["goto"]),
            "xdif": round(float(enemy.get("xdif", HELI_TARGET_X_OFFSET)), 8),
            "shoot": int(enemy.get("shoot", 0)),
            "shots": int(enemy.get("shots", 0)),
            "rotation": round(float(enemy["rotation"]), 8),
            "gun_rotation": round(float(enemy["gun_rotation"]), 8),
            "gun_target_rotation": round(float(enemy.get("gun_target_rotation", 0.0)), 8),
            "gun_yscale": int(enemy.get("gun_yscale", 100)),
        }

    def get_state(self) -> dict[str, Any]:
        return {
            "tick": self.tick,
            "x": round(float(self._x), 8),
            "y": round(float(self._y), 8),
            "xspeed": round(float(self.xspeed), 8),
            "yspeed": round(float(self.yspeed), 8),
            "xchange": round(float(self.xchange), 8),
            "ychange": round(float(self.ychange), 8),
            "playerwidth": round(float(self.playerwidth), 8),
            "playerheight": round(float(self.playerheight), 8),
            "health": int(self.health),
            "lastHealth": int(self.lastHealth),
            "jump": int(self.jump),
            "jump2": int(self.jump2),
            "duck": int(self.duck),
            "up": int(self.up),
            "upk": int(self.upk),
            "hyperjump": int(self.hyperjump),
            "hjump": int(self.hjump),
            "boostK": int(self.boostK),
            "facing_right": bool(self.facing_right),
            "pending_default_heli": bool(self.pending_default_heli),
            "default_heli_spawned": bool(self.default_heli_spawned),
            "respawn_helis": bool(self.respawn_helis),
            "last_player_damage_tick": self.last_player_damage_tick,
            "last_player_damage_amount": int(self.last_player_damage_amount),
            "last_action": list(self.last_action),
            "world": {
                "x": round(float(self.world_x), 8),
                "y": round(float(self.world_y), 8),
                "pos": [int(self.worldpos[0]), int(self.worldpos[1])],
                "bounds": [int(self.worldbounds[0]), int(self.worldbounds[1])],
                "stw": AS_STW,
                "sth": AS_STH,
                "spw": AS_SPW,
                "sph": AS_SPH,
            },
            "gun": {
                "cgun": int(self.cgun),
                "name": "MachineGun",
                "reloadtime": self._state_value(self.gun_reloadtime),
                "bullets": self._state_value(self.gun_bullets),
                "shots": int(self.gun_shots),
                "rotation": round(float(self.gun_rotation), 8),
                "aim_rotation": round(float(self.aim_rotation), 8),
                "total_bullets_spawned": int(self.total_bullets_spawned),
                "next_bullet_id": int(self.next_bullet_id),
            },
            "bullets": [self._bullet_state(bullet) for bullet in self.bullets],
            "enemy_bullets": [
                self._enemy_bullet_state(bullet) for bullet in self.enemy_bullets
            ],
            "combat": {
                "score": int(self.score),
                "hits": int(self.hits),
                "helis": int(self.helis),
                "rthelis": int(self.rthelis),
                "level": int(self.level),
                "next_enemy_id": int(self.next_enemy_id),
                "total_enemies_spawned": int(self.total_enemies_spawned),
                "next_enemy_bullet_id": int(self.next_enemy_bullet_id),
                "total_enemy_bullets_spawned": int(self.total_enemy_bullets_spawned),
                "enemy_bullet_hits": int(self.enemy_bullet_hits),
            },
            "enemies": [self._enemy_state(enemy) for enemy in self.enemies],
        }

    def set_state(self, state: dict[str, Any]) -> None:
        self.tick = int(state["tick"])
        self._x = float(state["x"])
        self._y = float(state["y"])
        self.xspeed = float(state["xspeed"])
        self.yspeed = float(state["yspeed"])
        self.xchange = float(state["xchange"])
        self.ychange = float(state["ychange"])
        self.playerwidth = float(state["playerwidth"])
        self.playerheight = float(state["playerheight"])
        self.health = int(state.get("health", PLAYER_DEFAULT_HEALTH))
        self.lastHealth = int(state.get("lastHealth", self.health))
        self.jump = int(state["jump"])
        self.jump2 = int(state["jump2"])
        self.duck = int(state["duck"])
        self.up = int(state["up"])
        self.upk = int(state["upk"])
        self.hyperjump = int(state["hyperjump"])
        self.hjump = int(state["hjump"])
        self.boostK = int(state["boostK"])
        self.facing_right = bool(state["facing_right"])
        self.pending_default_heli = bool(state.get("pending_default_heli", False))
        self.default_heli_spawned = bool(state.get("default_heli_spawned", bool(state.get("enemies"))))
        self.respawn_helis = bool(state.get("respawn_helis", self.respawn_helis))
        self.last_player_damage_tick = state.get("last_player_damage_tick")
        if self.last_player_damage_tick is not None:
            self.last_player_damage_tick = int(self.last_player_damage_tick)
        self.last_player_damage_amount = int(state.get("last_player_damage_amount", 0))
        self.last_action = self._normalize_action(state["last_action"])
        world = state.get("world", {})
        self.world_x = float(world.get("x", 0.0))
        self.world_y = float(world.get("y", 0.0))
        self.worldpos = [int(v) for v in world.get("pos", [0, 0])]
        self.worldbounds = [int(v) for v in world.get("bounds", [0, 0])]
        gun = state.get("gun", {})
        self.cgun = int(gun.get("cgun", 0))
        reloadtime = gun.get("reloadtime", "Infinity")
        self.gun_reloadtime = math.inf if reloadtime == "Infinity" else float(reloadtime)
        bullets = gun.get("bullets", "Infinity")
        self.gun_bullets = math.inf if bullets == "Infinity" else float(bullets)
        self.gun_shots = int(gun.get("shots", 0))
        self.gun_rotation = float(gun.get("rotation", 0.0))
        self.aim_rotation = float(gun.get("aim_rotation", 0.0))
        self.total_bullets_spawned = int(gun.get("total_bullets_spawned", 0))
        self.next_bullet_id = int(gun.get("next_bullet_id", 1))
        self.bullets = [dict(bullet) for bullet in state.get("bullets", [])]
        self.enemy_bullets = [dict(bullet) for bullet in state.get("enemy_bullets", [])]
        combat = state.get("combat", {})
        self.score = int(combat.get("score", 0))
        self.hits = int(combat.get("hits", 0))
        self.helis = int(combat.get("helis", 0))
        self.rthelis = int(combat.get("rthelis", 0))
        self.level = int(combat.get("level", 0))
        self.next_enemy_id = int(combat.get("next_enemy_id", 1))
        self.total_enemies_spawned = int(
            combat.get("total_enemies_spawned", max(0, self.next_enemy_id - 1))
        )
        self.next_enemy_bullet_id = int(combat.get("next_enemy_bullet_id", 1))
        self.total_enemy_bullets_spawned = int(
            combat.get("total_enemy_bullets_spawned", 0)
        )
        self.enemy_bullet_hits = int(combat.get("enemy_bullet_hits", 0))
        self.enemies = [dict(enemy) for enemy in state.get("enemies", [])]
        self.last_camera = self.get_camera()
        self.last_gun_event = self._empty_gun_event()
        self.last_enemy_event = self._empty_enemy_event()

    def state_hash(self) -> str:
        payload = json.dumps(self.get_state(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def get_debug_info(self) -> dict[str, Any]:
        info = {
            "tick": self.tick,
            "state_hash": self.state_hash(),
            "state": self.get_state(),
            "camera": [round(v, 6) for v in self.get_camera()],
            "player_health": int(self.health),
            "last_player_damage_tick": self.last_player_damage_tick,
            "last_player_damage_amount": int(self.last_player_damage_amount),
            "grounded": bool(self.jump == 0 and self.yspeed == 0),
            "jumping": bool(self.jump),
            "ducking": bool(self.duck),
            "hyperjump_ready": bool(self.hyperjump >= 150),
            "contact": dict(self.last_contact),
            "gun": dict(self.get_state()["gun"]),
            "combat": dict(self.get_state()["combat"]),
            "enemies": [dict(enemy) for enemy in self.get_state()["enemies"]],
            "enemy_bullets": [
                dict(bullet) for bullet in self.get_state()["enemy_bullets"]
            ],
            "gun_event": dict(self.last_gun_event),
            "enemy_event": dict(self.last_enemy_event),
            "active_bullets": len(self.bullets),
            "active_enemy_bullets": len(self.enemy_bullets),
            "last_action": list(self.last_action),
        }
        if self.training_profile == "combat_v1":
            info["training_profile"] = self.training_profile
            info["termination_reason"] = self.last_termination_reason
            info["reward_breakdown"] = (
                dict(self.last_reward_breakdown)
                if self.last_reward_breakdown is not None
                else None
            )
            info["episode_step_count"] = int(self.episode_step_count)
            info["total_player_damage"] = int(self.total_player_damage)
            info["heli_kills"] = int(self.helis)
            info["heli_hits"] = int(self.hits)
            info["player_bullets_fired"] = int(self.gun_shots)
            info["enemy_bullet_hits"] = int(self.enemy_bullet_hits)
            info["score"] = int(self.score)
        return info

    def close(self) -> None:
        if pygame.font.get_init():
            pygame.font.quit()
        if pygame.display.get_init():
            pygame.display.quit()
        self.window = None
        self.clock = None
        self.font = None
        self.images = {}
        self.tiles = {}
        self.bullets = []
        self.enemy_bullets = []


if __name__ == "__main__":
    from scripts.play_human import main

    main()
