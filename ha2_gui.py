from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ha2_sound import SoundPlayer, loop_volumes_from_env, pop_sound_events_from_env


GUI_SPEED_FACTORS = (0.25, 0.5, 1.0, 2.0, 4.0, 8.0)
DEFAULT_GUI_SPEED = 1.0
GAMEOVER_SLOWDOWN_MIN = 0.2
GAMEOVER_SLOWDOWN_STEP = 0.1


COMMON_CONTROL_HELP = (
    "Esc quit Enter/R restart F speed+ Shift+F speed- 1 1x "
    "P/Space pause N step F1 debug F3 hitboxes"
)


@dataclass
class GuiCommand:
    restart: bool = False
    screenshot: bool = False


@dataclass
class GuiState:
    paused: bool = False
    debug_overlay: bool = True
    collision_overlay: bool = False
    single_step: bool = False
    running: bool = True
    terminal_hold: bool = False
    terminal_reason: str | None = None
    speed_index: int = field(
        default_factory=lambda: GUI_SPEED_FACTORS.index(DEFAULT_GUI_SPEED)
    )
    gameover_slowdown: float = 1.0
    visual_accumulator: float = 0.0

    @property
    def user_speed_factor(self) -> float:
        return float(GUI_SPEED_FACTORS[self.speed_index])

    @property
    def is_player_death_hold(self) -> bool:
        return self.terminal_hold and self.terminal_reason == "player_death"

    def effective_visual_speed(self) -> float:
        if self.is_player_death_hold:
            return self.user_speed_factor * self.gameover_slowdown
        return self.user_speed_factor

    def speed_up(self) -> None:
        self.speed_index = min(self.speed_index + 1, len(GUI_SPEED_FACTORS) - 1)

    def speed_down(self) -> None:
        self.speed_index = max(self.speed_index - 1, 0)

    def reset_speed(self) -> None:
        self.speed_index = GUI_SPEED_FACTORS.index(DEFAULT_GUI_SPEED)

    def enter_terminal(self, reason: str | None) -> None:
        self.terminal_hold = True
        self.terminal_reason = str(reason or "terminal")
        self.gameover_slowdown = 1.0
        self.visual_accumulator = 0.0
        self.single_step = False

    def clear_terminal(self) -> None:
        self.terminal_hold = False
        self.terminal_reason = None
        self.gameover_slowdown = 1.0
        self.visual_accumulator = 0.0
        self.single_step = False

    def should_advance_logic(self) -> bool:
        return not self.terminal_hold and (not self.paused or self.single_step)

    def consume_single_step(self) -> None:
        self.single_step = False

    def target_fps(self, base_fps: int) -> int:
        return max(1, int(round(float(base_fps) * self.user_speed_factor)))

    def common_debug_lines(self) -> list[str]:
        lines = [
            (
                f"speed={self.user_speed_factor:g}x "
                f"effective={self.effective_visual_speed():.2f}x "
                f"paused={self.paused}"
            ),
            COMMON_CONTROL_HELP,
        ]
        if self.terminal_hold:
            lines.append(f"terminal={self.terminal_reason} Enter/R restart Esc quit")
        return lines


class GuiSound:
    def __init__(self, *, enabled: bool, sound_debug: bool = False):
        self.sound_debug = bool(sound_debug)
        self.player = SoundPlayer(enabled=enabled)
        self.last_loop_volumes: dict[str, float] = {}
        if not enabled:
            print("Sound disabled.")
        elif not self.player.available:
            print(f"Sound unavailable; continuing without audio. {self.player.warning}")

    def sync(self, env: Any, *, play_events: bool = False) -> None:
        if play_events:
            self.player.play_events(pop_sound_events_from_env(env))
        self.last_loop_volumes = loop_volumes_from_env(env)
        self.player.sync_loop_volumes(self.last_loop_volumes)

    def stop_all(self) -> None:
        self.player.stop_all()

    def debug_lines(self) -> list[str]:
        if not self.sound_debug:
            return []
        return [
            "sound: "
            + " ".join(
                f"{name}={volume:.0f}"
                for name, volume in sorted(self.last_loop_volumes.items())
            )
        ]


def add_common_gui_args(parser: Any) -> None:
    parser.add_argument("--no-sound", action="store_true", help="Disable optional GUI sound playback.")
    parser.add_argument("--sound-debug", action="store_true", help="Show GUI-only sound loop volumes in debug overlay.")


def base_ha2_env(env: Any) -> Any:
    return getattr(env, "unwrapped", env)


def is_player_death_termination(terminated: bool, info: dict[str, Any]) -> bool:
    return bool(terminated and info.get("termination_reason") == "player_death")


def terminal_reason(terminated: bool, truncated: bool, info: dict[str, Any]) -> str | None:
    if terminated:
        return str(info.get("termination_reason") or "terminated")
    if truncated:
        return "truncated"
    return None


def _event_mod_has_shift(event: Any, pygame_module: Any) -> bool:
    mod = int(getattr(event, "mod", 0) or 0)
    key_module = getattr(pygame_module, "key", None)
    get_mods = getattr(key_module, "get_mods", None)
    if get_mods is not None:
        try:
            mod |= int(get_mods())
        except Exception:
            pass
    shift_mask = int(getattr(pygame_module, "KMOD_SHIFT", 0) or 0)
    return bool(shift_mask and (mod & shift_mask))


def handle_common_event(
    state: GuiState,
    event: Any,
    pygame_module: Any,
    *,
    allow_pause: bool = True,
    allow_single_step: bool = True,
    allow_collision_toggle: bool = True,
) -> GuiCommand:
    command = GuiCommand()
    if event.type == pygame_module.QUIT:
        state.running = False
        return command
    if event.type != pygame_module.KEYDOWN:
        return command

    key = getattr(event, "key", None)
    if key == getattr(pygame_module, "K_ESCAPE", object()):
        state.running = False
    elif key in (getattr(pygame_module, "K_RETURN", object()), getattr(pygame_module, "K_r", object())):
        command.restart = True
    elif key == getattr(pygame_module, "K_f", object()):
        if _event_mod_has_shift(event, pygame_module):
            state.speed_down()
        else:
            state.speed_up()
    elif key == getattr(pygame_module, "K_1", object()):
        state.reset_speed()
    elif allow_pause and key in (
        getattr(pygame_module, "K_p", object()),
        getattr(pygame_module, "K_SPACE", object()),
    ):
        state.paused = not state.paused
    elif allow_single_step and key == getattr(pygame_module, "K_n", object()):
        state.single_step = True
    elif key == getattr(pygame_module, "K_F1", object()):
        state.debug_overlay = not state.debug_overlay
    elif allow_collision_toggle and key == getattr(pygame_module, "K_F3", object()):
        state.collision_overlay = not state.collision_overlay
    elif key == getattr(pygame_module, "K_F12", object()):
        command.screenshot = True
    return command


def advance_post_death_visuals(env: Any, state: GuiState, *, force_one: bool = False) -> int:
    if not state.is_player_death_hold:
        return 0
    if force_one:
        env.advance_visual_effects_only()
        return 1
    state.gameover_slowdown = max(
        GAMEOVER_SLOWDOWN_MIN,
        state.gameover_slowdown - GAMEOVER_SLOWDOWN_STEP,
    )
    state.visual_accumulator += state.effective_visual_speed()
    advanced = 0
    while state.visual_accumulator >= 1.0:
        env.advance_visual_effects_only()
        state.visual_accumulator -= 1.0
        advanced += 1
    return advanced
