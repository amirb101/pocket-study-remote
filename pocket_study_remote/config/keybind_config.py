"""
Keybinding configuration management.

Stores per-mode button mappings in JSON, supports simple presses,
combinations (A+B), and long presses (hold 0.5s).
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Callable

from ..core.gamepad_button import GamepadButton

logger = logging.getLogger(__name__)


class InputType(Enum):
    """Types of controller input."""
    SIMPLE = "simple"          # Just press the button
    COMBO = "combo"            # Press A while holding B
    LONG_PRESS = "long_press"  # Hold for 0.5s


@dataclass
class KeybindAction:
    """A configurable action that can be bound to controller input."""
    id: str
    name: str
    description: str
    default_button: GamepadButton | None = None
    default_combo: list[GamepadButton] | None = None


@dataclass
class KeybindMapping:
    """A single mapping from controller input to an action."""
    action_id: str
    input_type: InputType
    # For simple: just the button
    button: GamepadButton | None = None
    # For combo: primary button + held buttons
    primary_button: GamepadButton | None = None
    held_buttons: list[GamepadButton] = field(default_factory=list)
    # For long press: the button and duration
    duration_ms: int = 500

    def to_dict(self) -> dict:
        return {
            "action_id": self.action_id,
            "input_type": self.input_type.value,
            "button": self.button.name if self.button else None,
            "primary_button": self.primary_button.name if self.primary_button else None,
            "held_buttons": [b.name for b in self.held_buttons],
            "duration_ms": self.duration_ms,
        }

    @classmethod
    def from_dict(cls, data: dict) -> KeybindMapping:
        return cls(
            action_id=data["action_id"],
            input_type=InputType(data["input_type"]),
            button=GamepadButton[data["button"]] if data.get("button") else None,
            primary_button=GamepadButton[data["primary_button"]] if data.get("primary_button") else None,
            held_buttons=[GamepadButton[b] for b in data.get("held_buttons", [])],
            duration_ms=data.get("duration_ms", 500),
        )


@dataclass
class ModeConfig:
    """Configuration for a single mode (browser, spotify, etc.)."""
    mode_id: str
    mode_name: str
    actions: list[KeybindAction] = field(default_factory=list)
    mappings: list[KeybindMapping] = field(default_factory=list)

    def get_mapping_for_action(self, action_id: str) -> KeybindMapping | None:
        """Get the mapping for a specific action."""
        for m in self.mappings:
            if m.action_id == action_id:
                return m
        return None

    def get_action_by_id(self, action_id: str) -> KeybindAction | None:
        """Get action definition by ID."""
        for a in self.actions:
            if a.id == action_id:
                return a
        return None

    def set_mapping(self, mapping: KeybindMapping) -> None:
        """Set or replace a mapping."""
        # Remove existing mapping for this action
        self.mappings = [m for m in self.mappings if m.action_id != mapping.action_id]
        self.mappings.append(mapping)

    def clear_mapping(self, action_id: str) -> None:
        """Remove a mapping."""
        self.mappings = [m for m in self.mappings if m.action_id != action_id]

    def to_dict(self) -> dict:
        return {
            "mode_id": self.mode_id,
            "mode_name": self.mode_name,
            "actions": [
                {
                    "id": a.id,
                    "name": a.name,
                    "description": a.description,
                    "default_button": a.default_button.name if a.default_button else None,
                }
                for a in self.actions
            ],
            "mappings": [m.to_dict() for m in self.mappings],
        }

    @classmethod
    def from_dict(cls, data: dict) -> ModeConfig:
        actions = [
            KeybindAction(
                id=a["id"],
                name=a["name"],
                description=a["description"],
                default_button=GamepadButton[a["default_button"]] if a.get("default_button") else None,
            )
            for a in data.get("actions", [])
        ]
        mappings = [KeybindMapping.from_dict(m) for m in data.get("mappings", [])]
        return cls(
            mode_id=data["mode_id"],
            mode_name=data["mode_name"],
            actions=actions,
            mappings=mappings,
        )


class KeybindConfig:
    """Manages all keybinding configuration."""

    CONFIG_PATH = Path.home() / ".config" / "pocket-study-remote" / "keybindings.json"

    def __init__(self) -> None:
        self.modes: dict[str, ModeConfig] = {}
        self._load()

    def _load(self) -> None:
        """Load configuration from disk or create defaults."""
        if self.CONFIG_PATH.exists():
            try:
                with open(self.CONFIG_PATH, "r") as f:
                    data = json.load(f)
                for mode_data in data.get("modes", []):
                    mode = ModeConfig.from_dict(mode_data)
                    self.modes[mode.mode_id] = mode
                logger.info("Loaded keybindings from %s", self.CONFIG_PATH)
            except Exception as e:
                logger.warning("Failed to load keybindings: %s", e)
                self._create_defaults()
        else:
            self._create_defaults()

    def _create_defaults(self) -> None:
        """Create default keybinding configuration."""
        from ..modes.browser_mode import BrowserMode
        from ..modes.spotify_mode import SpotifyMode
        from ..modes.global_mode import GlobalMode

        # Browser mode defaults
        browser = ModeConfig(
            mode_id="browser",
            mode_name="Browser",
            actions=[
                KeybindAction("new_tab", "New Tab", "Open a new tab", GamepadButton.A),
                KeybindAction("go_back", "Go Back", "Navigate back", GamepadButton.B),
                KeybindAction("close_tab", "Close Tab", "Close current tab", GamepadButton.X),
                KeybindAction("reopen_tab", "Reopen Tab", "Reopen closed tab", GamepadButton.Y),
                KeybindAction("page_back", "Page Back", "Go back in history", GamepadButton.DPAD_LEFT),
                KeybindAction("page_forward", "Page Forward", "Go forward in history", GamepadButton.DPAD_RIGHT),
                KeybindAction("scroll_up", "Scroll Up", "Scroll page up", GamepadButton.DPAD_UP),
                KeybindAction("scroll_down", "Scroll Down", "Scroll page down", GamepadButton.DPAD_DOWN),
                KeybindAction("prev_tab", "Previous Tab", "Switch to previous tab", GamepadButton.LEFT_SHOULDER),
                KeybindAction("next_tab", "Next Tab", "Switch to next tab", GamepadButton.RIGHT_SHOULDER),
                KeybindAction("new_window", "New Window", "Open new browser window", GamepadButton.LEFT_TRIGGER),
                KeybindAction("tab_search", "Search Tabs", "Search open tabs", GamepadButton.RIGHT_TRIGGER),
                KeybindAction("focus_address", "Focus Address Bar", "Focus the URL bar", GamepadButton.START),
                KeybindAction("bookmark", "Bookmark Page", "Bookmark current page", None),  # Combo only
            ],
        )
        # Set default combo for bookmark
        browser.set_mapping(KeybindMapping(
            action_id="bookmark",
            input_type=InputType.COMBO,
            primary_button=GamepadButton.B,
            held_buttons=[GamepadButton.A],
        ))
        # Set simple button defaults
        for action in browser.actions:
            if action.default_button and action.id != "bookmark":
                browser.set_mapping(KeybindMapping(
                    action_id=action.id,
                    input_type=InputType.SIMPLE,
                    button=action.default_button,
                ))
        self.modes["browser"] = browser

        # Spotify mode defaults
        spotify = ModeConfig(
            mode_id="spotify",
            mode_name="Spotify",
            actions=[
                KeybindAction("play_pause", "Play/Pause", "Toggle playback", GamepadButton.A),
                KeybindAction("next_track", "Next Track", "Skip to next song", GamepadButton.RIGHT_SHOULDER),
                KeybindAction("prev_track", "Previous Track", "Go to previous song", GamepadButton.LEFT_SHOULDER),
                KeybindAction("volume_up", "Volume Up", "Increase volume", GamepadButton.DPAD_UP),
                KeybindAction("volume_down", "Volume Down", "Decrease volume", GamepadButton.DPAD_DOWN),
                KeybindAction("seek_forward", "Seek Forward", "Skip ahead in track", GamepadButton.DPAD_RIGHT),
                KeybindAction("seek_backward", "Seek Backward", "Skip back in track", GamepadButton.DPAD_LEFT),
                KeybindAction("shuffle", "Toggle Shuffle", "Toggle shuffle mode", GamepadButton.X),
                KeybindAction("like", "Like Song", "Save/like current song", GamepadButton.Y),
            ],
        )
        for action in spotify.actions:
            if action.default_button:
                spotify.set_mapping(KeybindMapping(
                    action_id=action.id,
                    input_type=InputType.SIMPLE,
                    button=action.default_button,
                ))
        self.modes["spotify"] = spotify

        # Global mode defaults
        global_mode = ModeConfig(
            mode_id="global",
            mode_name="Global",
            actions=[
                KeybindAction("play_pause", "Play/Pause", "Toggle media playback", GamepadButton.A),
                KeybindAction("next_track", "Next Track", "Next media track", GamepadButton.RIGHT_SHOULDER),
                KeybindAction("prev_track", "Previous Track", "Previous media track", GamepadButton.LEFT_SHOULDER),
                KeybindAction("volume_up", "Volume Up", "Increase system volume", GamepadButton.DPAD_UP),
                KeybindAction("volume_down", "Volume Down", "Decrease system volume", GamepadButton.DPAD_DOWN),
                KeybindAction("mute", "Mute", "Toggle mute", GamepadButton.B),
                KeybindAction("screenshot", "Screenshot", "Take screenshot", GamepadButton.Y),
                KeybindAction("mission_control", "Mission Control", "Show all windows", GamepadButton.LEFT_TRIGGER),
                KeybindAction("spotlight", "Spotlight", "Open Spotlight search", GamepadButton.RIGHT_TRIGGER),
                KeybindAction("lock_screen", "Lock Screen", "Lock the screen", GamepadButton.START),
            ],
        )
        for action in global_mode.actions:
            if action.default_button:
                global_mode.set_mapping(KeybindMapping(
                    action_id=action.id,
                    input_type=InputType.SIMPLE,
                    button=action.default_button,
                ))
        self.modes["global"] = global_mode

        self._save()
        logger.info("Created default keybindings")

    def _save(self) -> None:
        """Save configuration to disk."""
        try:
            self.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "version": 1,
                "modes": [mode.to_dict() for mode in self.modes.values()],
            }
            with open(self.CONFIG_PATH, "w") as f:
                json.dump(data, f, indent=2)
            logger.info("Saved keybindings to %s", self.CONFIG_PATH)
        except Exception as e:
            logger.error("Failed to save keybindings: %s", e)

    def get_mode(self, mode_id: str) -> ModeConfig | None:
        """Get configuration for a mode."""
        return self.modes.get(mode_id)

    def save_mode(self, mode: ModeConfig) -> None:
        """Save a mode's configuration."""
        self.modes[mode.mode_id] = mode
        self._save()

    def reset_mode(self, mode_id: str) -> None:
        """Reset a mode to defaults."""
        if mode_id in self.modes:
            del self.modes[mode_id]
        self._create_defaults()


# Global instance
_config: KeybindConfig | None = None


def get_config() -> KeybindConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = KeybindConfig()
    return _config
