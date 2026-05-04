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
ENV_VERSION = "0.2"


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
    ):
        super().__init__()
        self.render_mode = render_mode
        self.assets_dir = Path(assets_dir) if assets_dir is not None else HA2_ASSET_DIR
        self.auto_render = auto_render

        # ACTION SPACE: [Move(left/idle/right), Jump, Duck, Boost]
        self.action_space = spaces.MultiDiscrete([3, 2, 2, 2])

        map_pixel_width = len(const.FULL_MAP_DATA[0]) * const.TILE_SIZE
        map_pixel_height = len(const.FULL_MAP_DATA) * const.TILE_SIZE
        high = np.array(
            [map_pixel_width * 2.0, map_pixel_height * 2.0, 100.0, 100.0],
            dtype=np.float32,
        )
        self.observation_space = spaces.Box(low=-high, high=high, dtype=np.float32)

        self.map_width = len(const.FULL_MAP_DATA[0])
        self.map_height = len(const.FULL_MAP_DATA)
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

        self.jump = 0
        self.jump2 = 0
        self.duck = 0
        self.up = 0
        self.upk = 0
        self.hyperjump = 150
        self.hjump = 0
        self.boostK = 0
        self.facing_right = True

        self.tick = 0
        self.last_action = [1, 0, 0, 0]
        self.last_reward = 0.0
        self.last_terminated = False
        self.last_truncated = False
        self.last_contact = self._empty_contact()
        self.last_camera = (0.0, 0.0)

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

        self.images = {
            "guy": load_img(Path("images") / "116.png"),
            "duck": load_img(Path("images") / "120.png"),
            "jump": load_img(Path("images") / "124.png"),
            "walk1": load_img(Path("images") / "126.png"),
            "walk2": load_img(Path("images") / "128.png"),
            "jump2": load_img(Path("images") / "131.png"),
            "chute": load_img(Path("images") / "133.png"),
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
        self.jump = 0
        self.jump2 = 0
        self.duck = 0
        self.up = 0
        self.upk = 0
        self.hjump = 0
        self.hyperjump = 150
        self.boostK = 0
        self.facing_right = True
        self.tick = 0
        self.last_action = [1, 0, 0, 0]
        self.last_reward = 0.0
        self.last_terminated = False
        self.last_truncated = False
        self.last_contact = self._empty_contact()
        self.last_camera = self.get_camera()

        if self.auto_render and self.render_mode in ["human", "rgb_array"]:
            self.render()

        return self._get_obs(), self.get_debug_info()

    def _get_obs(self) -> np.ndarray:
        return np.array([self._x, self._y, self.xspeed, self.yspeed], dtype=np.float32)

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

    def step(self, action):
        action = [int(v) for v in np.asarray(action, dtype=np.int64).tolist()]
        move_action, jump_action, duck_action, boost_action = action
        contact = self._empty_contact()

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

        reward = 0.1
        terminated = bool(self._y > self.map_height * const.TILE_SIZE)
        if terminated:
            reward = -10.0

        self.tick += 1
        self.last_action = action
        self.last_reward = float(reward)
        self.last_terminated = terminated
        self.last_truncated = False
        self.last_contact = contact
        self.last_camera = self.get_camera()

        if self.auto_render and self.render_mode in ["human", "rgb_array"]:
            self.render()

        return self._get_obs(), reward, terminated, False, self.get_debug_info()

    def get_camera(self) -> tuple[float, float]:
        cam_x = -self._x + (const.SCREEN_WIDTH / 2)
        cam_x = min(0, max(cam_x, -(self.map_width * const.TILE_SIZE - const.SCREEN_WIDTH)))
        cam_y = max(
            -self._y + (const.SCREEN_HEIGHT / 2),
            -(self.map_height * const.TILE_SIZE - const.SCREEN_HEIGHT),
        )
        return float(cam_x), float(cam_y)

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

        if debug_collision:
            self._draw_collision_debug(canvas, cam_x, cam_y)

        if debug_overlay:
            self._draw_debug_overlay(canvas, debug_lines or [])

        if self.render_mode == "human":
            self.window.blit(canvas, canvas.get_rect())
            pygame.display.update()
            return None
        if self.render_mode == "rgb_array":
            return np.transpose(pygame.surfarray.array3d(canvas), axes=(1, 0, 2))
        return None

    def _draw_debug_overlay(self, canvas: pygame.Surface, extra_lines: list[str]) -> None:
        if self.font is None:
            return
        lines = [
            f"tick={self.tick} hash={self.state_hash()}",
            f"pos=({self._x:.2f},{self._y:.2f}) speed=({self.xspeed:.2f},{self.yspeed:.2f})",
            f"jump={self.jump}/{self.jump2} duck={self.duck} hjump={self.hjump} hyper={self.hyperjump}",
            f"action={self.last_action} camera=({self.last_camera[0]:.1f},{self.last_camera[1]:.1f})",
            f"contact={self.last_contact}",
        ]
        lines.extend(extra_lines)

        pad = 6
        line_h = 18
        width = max(self.font.size(line)[0] for line in lines) + pad * 2
        height = len(lines) * line_h + pad * 2
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 155))
        for idx, line in enumerate(lines):
            surface = self.font.render(line, True, (245, 245, 245))
            overlay.blit(surface, (pad, pad + idx * line_h))
        canvas.blit(overlay, (8, 8))

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
            "jump": int(self.jump),
            "jump2": int(self.jump2),
            "duck": int(self.duck),
            "up": int(self.up),
            "upk": int(self.upk),
            "hyperjump": int(self.hyperjump),
            "hjump": int(self.hjump),
            "boostK": int(self.boostK),
            "facing_right": bool(self.facing_right),
            "last_action": list(self.last_action),
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
        self.jump = int(state["jump"])
        self.jump2 = int(state["jump2"])
        self.duck = int(state["duck"])
        self.up = int(state["up"])
        self.upk = int(state["upk"])
        self.hyperjump = int(state["hyperjump"])
        self.hjump = int(state["hjump"])
        self.boostK = int(state["boostK"])
        self.facing_right = bool(state["facing_right"])
        self.last_action = [int(v) for v in state["last_action"]]
        self.last_camera = self.get_camera()

    def state_hash(self) -> str:
        payload = json.dumps(self.get_state(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def get_debug_info(self) -> dict[str, Any]:
        return {
            "tick": self.tick,
            "state_hash": self.state_hash(),
            "state": self.get_state(),
            "camera": [round(v, 6) for v in self.get_camera()],
            "grounded": bool(self.jump == 0 and self.yspeed == 0),
            "jumping": bool(self.jump),
            "ducking": bool(self.duck),
            "hyperjump_ready": bool(self.hyperjump >= 150),
            "contact": dict(self.last_contact),
            "last_action": list(self.last_action),
        }

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


if __name__ == "__main__":
    from scripts.play_human import main

    main()
