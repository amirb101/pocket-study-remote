"""
Configuration management for keybindings.

Loads and saves keybinding configurations, and provides default keybindings
for all modes.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Controller button names
CONTROLLER_BUTTONS = [
    "A", "B", "X", "Y",
    "L1", "R1", "L2", "R2",
    "SELECT", "START",
    "D_UP", "D_DOWN", "D_LEFT", "D_RIGHT",
]


@dataclass
class KeybindAction:
    """Represents a single configurable action."""
    action_id: str
    display_name: str
    description: str
    default_button: str | None = None
    is_combo: bool = False  # Whether this action can use combo (button + modifier)


@dataclass
class ModeConfig:
    """Configuration for a single mode."""
    mode_id: str
    display_name: str
    actions: List[KeybindAction] = field(default_factory=list)
    button_map: Dict[str, str] = field(default_factory=dict)  # button -> action_id
    combo_map: Dict[str, str] = field(default_factory=dict)    # button+modifier -> action_id

    def get_action_for_button(self, button: str, is_combo: bool = False) -> str | None:
        """Get action ID for a button press."""
        mapping = self.combo_map if is_combo else self.button_map
        return mapping.get(button)

    def set_mapping(self, button: str, action_id: str | None, is_combo: bool = False) -> None:
        """Set or clear a button mapping."""
        mapping = self.combo_map if is_combo else self.button_map
        if action_id:
            mapping[button] = action_id
        else:
            mapping.pop(button, None)

    def clear_mapping(self, button: str, is_combo: bool = False) -> None:
        """Clear a button mapping."""
        mapping = self.combo_map if is_combo else self.button_map
        mapping.pop(button, None)


class KeybindConfig:
    """Manages keybinding configurations for all modes."""

    CONFIG_FILE = Path.home() / ".pocket_study_remote" / "keybindings.json"

    def __init__(self) -> None:
        self.modes: Dict[str, ModeConfig] = {}
        self._create_defaults()
        self._load()

    def _create_defaults(self) -> None:
        """Create default configurations for all modes."""
        # Browser Mode
        self.modes["browser"] = ModeConfig(
            mode_id="browser",
            display_name="Browser",
            actions=[
                KeybindAction("new_tab", "New Tab", "Open a new browser tab", "Y"),
                KeybindAction("close_tab", "Close Tab", "Close the current tab", "X"),
                KeybindAction("reopen_tab", "Reopen Tab", "Reopen closed tab", "A", is_combo=True),
                KeybindAction("page_back", "Page Back", "Navigate back", "L1"),
                KeybindAction("page_forward", "Page Forward", "Navigate forward", "R1"),
                KeybindAction("prev_tab", "Previous Tab", "Switch to previous tab", "L2"),
                KeybindAction("next_tab", "Next Tab", "Switch to next tab", "R2"),
                KeybindAction("focus_address", "Focus Address", "Focus address bar", "SELECT"),
                KeybindAction("bookmark", "Bookmark", "Bookmark current page", "START"),
            ],
            button_map={
                "Y": "new_tab",
                "X": "close_tab",
                "L1": "page_back",
                "R1": "page_forward",
                "L2": "prev_tab",
                "R2": "next_tab",
                "SELECT": "focus_address",
                "START": "bookmark",
            },
            combo_map={
                "A": "reopen_tab",
            },
        )

        # Spotify Mode
        self.modes["spotify"] = ModeConfig(
            mode_id="spotify",
            display_name="Spotify",
            actions=[
                KeybindAction("play_pause", "Play/Pause", "Toggle playback", "A"),
                KeybindAction("next_track", "Next Track", "Skip to next track", "R1"),
                KeybindAction("prev_track", "Previous Track", "Go to previous track", "L1"),
                KeybindAction("volume_up", "Volume Up", "Increase volume", "R2"),
                KeybindAction("volume_down", "Volume Down", "Decrease volume", "L2"),
                KeybindAction("shuffle", "Shuffle", "Toggle shuffle", "X"),
                KeybindAction("like", "Like Song", "Save/like current song", "Y"),
            ],
            button_map={
                "A": "play_pause",
                "R1": "next_track",
                "L1": "prev_track",
                "R2": "volume_up",
                "L2": "volume_down",
                "X": "shuffle",
                "Y": "like",
            },
        )

        # Obsidian Mode
        self.modes["obsidian"] = ModeConfig(
            mode_id="obsidian",
            display_name="Obsidian",
            actions=[
                KeybindAction("command_palette", "Command Palette", "Open command palette", "Y"),
                KeybindAction("quick_switcher", "Quick Switcher", "Switch between notes", "A"),
                KeybindAction("daily_note", "Daily Note", "Open today's note", "X"),
                KeybindAction("new_note", "New Note", "Create new note", "B"),
                KeybindAction("graph_view", "Graph View", "Open graph view", "SELECT"),
                KeybindAction("search", "Search", "Search vault", "START"),
                KeybindAction("back", "Back", "Navigate back", "L1"),
                KeybindAction("forward", "Forward", "Navigate forward", "R1"),
            ],
            button_map={
                "Y": "command_palette",
                "A": "quick_switcher",
                "X": "daily_note",
                "B": "new_note",
                "SELECT": "graph_view",
                "START": "search",
                "L1": "back",
                "R1": "forward",
            },
        )

        # Global Mode
        self.modes["global"] = ModeConfig(
            mode_id="global",
            display_name="Global",
            actions=[
                KeybindAction("play_pause", "Play/Pause", "Global play/pause", "A"),
                KeybindAction("next_track", "Next Track", "Global next track", "R1"),
                KeybindAction("prev_track", "Previous Track", "Global previous track", "L1"),
                KeybindAction("volume_up", "Volume Up", "Global volume up", "R2"),
                KeybindAction("volume_down", "Volume Down", "Global volume down", "L2"),
                KeybindAction("mission_control", "Mission Control", "Open Mission Control", "SELECT"),
                KeybindAction("spotlight", "Spotlight", "Open Spotlight", "START"),
                KeybindAction("lock_screen", "Lock Screen", "Lock the screen", "Y", is_combo=True),
            ],
            button_map={
                "A": "play_pause",
                "R1": "next_track",
                "L1": "prev_track",
                "R2": "volume_up",
                "L2": "volume_down",
                "SELECT": "mission_control",
                "START": "spotlight",
            },
            combo_map={
                "Y": "lock_screen",
            },
        )

        # Finder Mode
        self.modes["finder"] = ModeConfig(
            mode_id="finder",
            display_name="Finder",
            actions=[
                KeybindAction("new_folder", "New Folder", "Create new folder", "N"),
                KeybindAction("quick_look", "Quick Look", "Quick look selected item", "Y"),
                KeybindAction("get_info", "Get Info", "Show file info", "I"),
                KeybindAction("search", "Search", "Search in Finder", "F"),
                KeybindAction("go_back", "Go Back", "Navigate back", "L1"),
                KeybindAction("go_forward", "Go Forward", "Navigate forward", "R1"),
                KeybindAction("trash", "Move to Trash", "Move selected to trash", "DELETE"),
            ],
            button_map={
                "Y": "quick_look",
                "L1": "go_back",
                "R1": "go_forward",
            },
        )

        # Apple Music Mode
        self.modes["apple_music"] = ModeConfig(
            mode_id="apple_music",
            display_name="Apple Music",
            actions=[
                KeybindAction("play_pause", "Play/Pause", "Toggle playback", "A"),
                KeybindAction("next_track", "Next Track", "Skip to next track", "R1"),
                KeybindAction("prev_track", "Previous Track", "Go to previous track", "L1"),
                KeybindAction("volume_up", "Volume Up", "Increase volume", "R2"),
                KeybindAction("volume_down", "Volume Down", "Decrease volume", "L2"),
                KeybindAction("love", "Love Track", "Love current track", "Y"),
                KeybindAction("shuffle", "Shuffle", "Toggle shuffle", "X"),
                KeybindAction("search", "Search", "Search in Apple Music", "SELECT"),
            ],
            button_map={
                "A": "play_pause",
                "R1": "next_track",
                "L1": "prev_track",
                "R2": "volume_up",
                "L2": "volume_down",
                "Y": "love",
                "X": "shuffle",
                "SELECT": "search",
            },
        )

        # Preview Mode
        self.modes["preview"] = ModeConfig(
            mode_id="preview",
            display_name="Preview",
            actions=[
                KeybindAction("next_page", "Next Page", "Go to next page", "R1"),
                KeybindAction("prev_page", "Previous Page", "Go to previous page", "L1"),
                KeybindAction("zoom_in", "Zoom In", "Zoom in on document", "R2"),
                KeybindAction("zoom_out", "Zoom Out", "Zoom out on document", "L2"),
                KeybindAction("actual_size", "Actual Size", "Reset zoom to 100%", "A"),
                KeybindAction("share", "Share", "Share document", "Y"),
                KeybindAction("rotate_left", "Rotate Left", "Rotate image left", "X"),
                KeybindAction("rotate_right", "Rotate Right", "Rotate image right", "B"),
            ],
            button_map={
                "R1": "next_page",
                "L1": "prev_page",
                "R2": "zoom_in",
                "L2": "zoom_out",
                "A": "actual_size",
                "Y": "share",
                "X": "rotate_left",
                "B": "rotate_right",
            },
        )

        # VS Code Mode
        self.modes["vscode"] = ModeConfig(
            mode_id="vscode",
            display_name="VS Code",
            actions=[
                KeybindAction("command_palette", "Command Palette", "Open command palette", "Y"),
                KeybindAction("quick_open", "Quick Open", "Quick open file", "A"),
                KeybindAction("toggle_terminal", "Toggle Terminal", "Show/hide terminal", "X"),
                KeybindAction("go_definition", "Go to Definition", "Navigate to definition", "B"),
                KeybindAction("find", "Find", "Open find dialog", "F"),
                KeybindAction("save", "Save", "Save current file", "S"),
                KeybindAction("new_file", "New File", "Create new file", "N"),
                KeybindAction("close_tab", "Close Tab", "Close current tab", "W"),
            ],
            button_map={
                "Y": "command_palette",
                "A": "quick_open",
                "X": "toggle_terminal",
                "B": "go_definition",
            },
        )

        # Notion Mode
        self.modes["notion"] = ModeConfig(
            mode_id="notion",
            display_name="Notion",
            actions=[
                KeybindAction("quick_find", "Quick Find", "Quick find in Notion", "Y"),
                KeybindAction("new_page", "New Page", "Create new page", "A"),
                KeybindAction("toggle_todo", "Toggle Todo", "Toggle todo checkbox", "X"),
                KeybindAction("slash_command", "Slash Command", "Open slash command", "B"),
                KeybindAction("back", "Go Back", "Navigate back", "L1"),
                KeybindAction("forward", "Go Forward", "Navigate forward", "R1"),
                KeybindAction("command_palette", "Command Palette", "Open command palette", "SELECT"),
            ],
            button_map={
                "Y": "quick_find",
                "A": "new_page",
                "X": "toggle_todo",
                "B": "slash_command",
                "L1": "back",
                "R1": "forward",
                "SELECT": "command_palette",
            },
        )

        # Messages Mode
        self.modes["messages"] = ModeConfig(
            mode_id="messages",
            display_name="Messages",
            actions=[
                KeybindAction("new_message", "New Message", "Start new conversation", "N"),
                KeybindAction("send_message", "Send", "Send message", "RETURN"),
                KeybindAction("next_conversation", "Next Chat", "Go to next conversation", "R1"),
                KeybindAction("prev_conversation", "Previous Chat", "Go to previous conversation", "L1"),
                KeybindAction("search", "Search", "Search messages", "F"),
                KeybindAction("details", "Chat Info", "Show chat details", "I"),
            ],
            button_map={
                "R1": "next_conversation",
                "L1": "prev_conversation",
            },
        )

        # WhatsApp Mode
        self.modes["whatsapp"] = ModeConfig(
            mode_id="whatsapp",
            display_name="WhatsApp",
            actions=[
                KeybindAction("new_chat", "New Chat", "Start new chat", "N"),
                KeybindAction("send", "Send", "Send message", "RETURN"),
                KeybindAction("search", "Search", "Search chats", "F"),
                KeybindAction("search_in_chat", "Search in Chat", "Search within current chat", "Y"),
                KeybindAction("archive_chat", "Archive Chat", "Archive current chat", "X"),
                KeybindAction("mute_chat", "Mute Chat", "Mute current chat", "B"),
            ],
            button_map={
                "Y": "search_in_chat",
                "X": "archive_chat",
                "B": "mute_chat",
            },
        )

    def _load(self) -> None:
        """Load configuration from disk."""
        if not self.CONFIG_FILE.exists():
            logger.info("No existing keybinding config found, using defaults")
            return

        try:
            with open(self.CONFIG_FILE, "r") as f:
                data = json.load(f)

            for mode_id, mode_data in data.get("modes", {}).items():
                if mode_id in self.modes:
                    self.modes[mode_id].button_map = mode_data.get("button_map", {})
                    self.modes[mode_id].combo_map = mode_data.get("combo_map", {})

            logger.info("Loaded keybinding config from %s", self.CONFIG_FILE)
        except Exception as e:
            logger.error("Failed to load keybinding config: %s", e)

    def save(self) -> None:
        """Save configuration to disk."""
        try:
            self.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "modes": {
                    mode_id: {
                        "button_map": mode.button_map,
                        "combo_map": mode.combo_map,
                    }
                    for mode_id, mode in self.modes.items()
                }
            }

            with open(self.CONFIG_FILE, "w") as f:
                json.dump(data, f, indent=2)

            logger.info("Saved keybinding config to %s", self.CONFIG_FILE)
        except Exception as e:
            logger.error("Failed to save keybinding config: %s", e)

    def get_mode_config(self, mode_id: str) -> ModeConfig | None:
        """Get configuration for a specific mode."""
        return self.modes.get(mode_id)

    def reset_to_defaults(self, mode_id: str | None = None) -> None:
        """Reset configuration to defaults. If mode_id is None, resets all."""
        if mode_id:
            if mode_id in self.modes:
                del self.modes[mode_id]
                self._create_defaults()
                logger.info("Reset keybindings for mode: %s", mode_id)
        else:
            self.modes.clear()
            self._create_defaults()
            logger.info("Reset all keybindings to defaults")


# Global config instance
_config: KeybindConfig | None = None


def get_config() -> KeybindConfig:
    """Get the global keybinding config instance."""
    global _config
    if _config is None:
        _config = KeybindConfig()
    return _config


def reload_config() -> KeybindConfig:
    """Reload configuration from disk."""
    global _config
    _config = KeybindConfig()
    return _config
