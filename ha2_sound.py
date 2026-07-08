from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent
SOUND_MANIFEST_PATH = REPO_ROOT / "assets_ffdec" / "sounds" / "manifest.json"


def load_sound_manifest(path: Path = SOUND_MANIFEST_PATH) -> dict[str, dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError(f"Sound manifest must be an object: {path}")
    return {str(name): dict(entry) for name, entry in data.items()}


def loop_volumes_from_env(env: Any) -> dict[str, float]:
    """Compute GUI-only loop volumes from already-existing env gameplay state."""
    if bool(getattr(env, "last_terminated", False)):
        return {"smusic": 50.0, "sheli": 0.0}
    player_x = float(getattr(env, "_x", 0.0)) + float(getattr(env, "width", 0.0)) / 2.0
    player_y = float(getattr(env, "_y", 0.0))
    heli_volume = 0.0
    for enemy in getattr(env, "enemies", []):
        if int(enemy.get("health", 0)) <= 0:
            continue
        distance = math.hypot(float(enemy["x"]) - player_x, float(enemy["y"]) - player_y)
        vol = min(max(distance / 800.0, 0.0), 1.0)
        heli_volume = max(heli_volume, 75.0 * (1.0 - vol))
    return {"smusic": 50.0, "sheli": heli_volume}


def pop_sound_events_from_env(env: Any) -> list[str]:
    pop_events = getattr(env, "pop_sound_events", None)
    if pop_events is None:
        return []
    return [str(event) for event in pop_events()]


class SoundPlayer:
    def __init__(self, *, manifest_path: Path = SOUND_MANIFEST_PATH, enabled: bool = True):
        self.manifest_path = manifest_path
        self.enabled = bool(enabled)
        self.available = False
        self.warning: str | None = None
        self._sounds: dict[str, Any] = {}
        self._loop_channels: dict[str, Any] = {}
        self._pygame = None

        if not self.enabled:
            self.warning = "sound disabled"
            return

        try:
            import pygame

            if not pygame.mixer.get_init():
                pygame.mixer.init()
            manifest = load_sound_manifest(manifest_path)
            sounds = {}
            for name, entry in manifest.items():
                asset = REPO_ROOT / str(entry["asset"])
                if not asset.exists():
                    continue
                sound = pygame.mixer.Sound(str(asset))
                sound.set_volume(float(entry.get("volume", 100)) / 100.0)
                sounds[name] = sound
            self._pygame = pygame
            self._sounds = sounds
            self.available = bool(sounds)
            if not self.available:
                self.warning = "no manifest sound assets loaded"
        except Exception as exc:  # pragma: no cover - depends on host audio stack
            self.warning = str(exc)
            self.available = False
            self._sounds = {}

    def play(self, event_name: str) -> None:
        if not self.available:
            return
        sound = self._sounds.get(str(event_name))
        if sound is not None:
            sound.play()

    def play_events(self, event_names) -> None:
        for event_name in event_names:
            self.play(str(event_name))

    def start_loop(self, name: str, volume: float | None = None) -> None:
        if not self.available:
            return
        loop_name = str(name)
        if loop_name in self._loop_channels:
            if volume is not None:
                self.set_loop_volume(loop_name, volume)
            return
        sound = self._sounds.get(loop_name)
        if sound is None:
            return
        if volume is not None:
            sound.set_volume(float(volume) / 100.0)
        channel = sound.play(loops=-1)
        if channel is not None:
            self._loop_channels[loop_name] = channel

    def stop_loop(self, name: str) -> None:
        channel = self._loop_channels.pop(str(name), None)
        if channel is not None:
            channel.stop()

    def set_loop_volume(self, name: str, volume: float) -> None:
        if not self.available:
            return
        loop_name = str(name)
        clamped = max(0.0, min(100.0, float(volume)))
        channel = self._loop_channels.get(loop_name)
        if channel is not None:
            channel.set_volume(clamped / 100.0)
            return
        sound = self._sounds.get(loop_name)
        if sound is not None:
            sound.set_volume(clamped / 100.0)

    def stop_all(self) -> None:
        for channel in list(self._loop_channels.values()):
            channel.stop()
        self._loop_channels.clear()

    def sync_loop_volumes(self, volumes: dict[str, float]) -> None:
        if not self.available:
            return
        desired = {str(name): float(volume) for name, volume in volumes.items()}
        for name in desired:
            self.start_loop(name)
        for name in list(self._loop_channels):
            if name not in desired:
                self.stop_loop(name)
        for name, volume in desired.items():
            self.set_loop_volume(name, volume)
