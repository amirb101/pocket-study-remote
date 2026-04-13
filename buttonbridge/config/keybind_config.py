"""Configuration for button mappings and actions."""

import dataclasses
import json
import logging
import pathlib
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class KeybindAction:
    """Definition of an action that can be bound to a button."""
    action_id: str
    display_name: str
    description: str
    default_button: Optional[str] = None
    is_combo: bool = False


@dataclasses.dataclass
class ModeConfig:
    """Configuration for a specific app mode."""
    mode_id: str
    display_name: str
    actions: List[KeybindAction]
    button_map: Dict[str, str]  # button -> action_id
    combo_map: Dict[str, str]  # combo -> action_id


class KeybindConfig:
    """Manages keybinding configurations for all modes."""
    
    CONFIG_FILE = pathlib.Path.home() / ".buttonbridge" / "keybindings.json"
    
    def __init__(self):
        self._modes: Dict[str, ModeConfig] = {}
        self._setup_default_configs()
    
    def _setup_default_configs(self):
        """Initialize default configurations for all modes."""
        # Browser mode
        self._modes["browser"] = ModeConfig(
            mode_id="browser",
            display_name="Browser",
            actions=[
                KeybindAction("new_tab", "New Tab", "Open a new browser tab", "Y"),
                KeybindAction("close_tab", "Close Tab", "Close the current tab", "X"),
                KeybindAction("next_tab", "Next Tab", "Switch to next tab", "RB"),
                KeybindAction("prev_tab", "Previous Tab", "Switch to previous tab", "LB"),
                KeybindAction("refresh", "Refresh", "Reload the current page", "A"),
                KeybindAction("back", "Go Back", "Navigate back in history", "View"),
                KeybindAction("forward", "Go Forward", "Navigate forward in history", "Menu"),
                KeybindAction("scroll_up", "Scroll Up", "Scroll page up", "RT"),
                KeybindAction("scroll_down", "Scroll Down", "Scroll page down", "LT"),
            ],
            button_map={
                "Y": "new_tab",
                "X": "close_tab",
                "RB": "next_tab",
                "LB": "prev_tab",
                "A": "refresh",
                "View": "back",
                "Menu": "forward",
                "RT": "scroll_up",
                "LT": "scroll_down",
            },
            combo_map={}
        )
        
        # Spotify mode
        self._modes["spotify"] = ModeConfig(
            mode_id="spotify",
            display_name="Spotify",
            actions=[
                KeybindAction("play_pause", "Play/Pause", "Toggle playback", "A"),
                KeybindAction("next_track", "Next Track", "Skip to next track", "RB"),
                KeybindAction("prev_track", "Previous Track", "Go to previous track", "LB"),
                KeybindAction("volume_up", "Volume Up", "Increase volume", "RT"),
                KeybindAction("volume_down", "Volume Down", "Decrease volume", "LT"),
                KeybindAction("shuffle", "Shuffle", "Toggle shuffle mode", "X"),
                KeybindAction("repeat", "Repeat", "Toggle repeat mode", "Y"),
                KeybindAction("like", "Like", "Save to liked songs", "B"),
            ],
            button_map={
                "A": "play_pause",
                "RB": "next_track",
                "LB": "prev_track",
                "RT": "volume_up",
                "LT": "volume_down",
                "X": "shuffle",
                "Y": "repeat",
                "B": "like",
            },
            combo_map={}
        )
        
        # Obsidian mode
        self._modes["obsidian"] = ModeConfig(
            mode_id="obsidian",
            display_name="Obsidian",
            actions=[
                KeybindAction("new_note", "New Note", "Create a new note", "Y"),
                KeybindAction("quick_switcher", "Quick Switcher", "Open quick switcher", "X"),
                KeybindAction("command_palette", "Command Palette", "Open command palette", "A"),
                KeybindAction("graph_view", "Graph View", "Open graph view", "B"),
                KeybindAction("toggle_sidebar", "Toggle Sidebar", "Toggle left sidebar", "View"),
                KeybindAction("toggle_right_sidebar", "Toggle Right Sidebar", "Toggle right sidebar", "Menu"),
                KeybindAction("daily_note", "Daily Note", "Open daily note", "RT"),
                KeybindAction("search", "Search", "Open global search", "LT"),
            ],
            button_map={
                "Y": "new_note",
                "X": "quick_switcher",
                "A": "command_palette",
                "B": "graph_view",
                "View": "toggle_sidebar",
                "Menu": "toggle_right_sidebar",
                "RT": "daily_note",
                "LT": "search",
            },
            combo_map={}
        )
        
        # Global mode (system-wide)
        self._modes["global"] = ModeConfig(
            mode_id="global",
            display_name="Global",
            actions=[
                KeybindAction("media_play_pause", "Media Play/Pause", "System media play/pause", None),
                KeybindAction("media_next", "Media Next", "Next media track", None),
                KeybindAction("media_prev", "Media Previous", "Previous media track", None),
                KeybindAction("volume_up_global", "Volume Up", "System volume up", None),
                KeybindAction("volume_down_global", "Volume Down", "System volume down", None),
                KeybindAction("mute", "Mute", "Mute system audio", None),
                KeybindAction("brightness_up", "Brightness Up", "Increase screen brightness", None),
                KeybindAction("brightness_down", "Brightness Down", "Decrease screen brightness", None),
            ],
            button_map={},
            combo_map={}
        )
        
        # Finder mode
        self._modes["finder"] = ModeConfig(
            mode_id="finder",
            display_name="Finder",
            actions=[
                KeybindAction("new_folder", "New Folder", "Create new folder", "Y"),
                KeybindAction("new_tab_finder", "New Tab", "Open new Finder tab", "A"),
                KeybindAction("quick_look", "Quick Look", "Open Quick Look preview", "X"),
                KeybindAction("search_finder", "Search", "Open Finder search", "B"),
                KeybindAction("view_icons", "Icon View", "Switch to icon view", "View"),
                KeybindAction("view_list", "List View", "Switch to list view", "Menu"),
                KeybindAction("go_back", "Go Back", "Navigate back", "LB"),
                KeybindAction("go_forward_finder", "Go Forward", "Navigate forward", "RB"),
            ],
            button_map={
                "Y": "new_folder",
                "A": "new_tab_finder",
                "X": "quick_look",
                "B": "search_finder",
                "View": "view_icons",
                "Menu": "view_list",
                "LB": "go_back",
                "RB": "go_forward_finder",
            },
            combo_map={}
        )
        
        # Apple Music mode
        self._modes["apple_music"] = ModeConfig(
            mode_id="apple_music",
            display_name="Apple Music",
            actions=[
                KeybindAction("am_play_pause", "Play/Pause", "Toggle playback", "A"),
                KeybindAction("am_next", "Next Track", "Next track", "RB"),
                KeybindAction("am_prev", "Previous Track", "Previous track", "LB"),
                KeybindAction("am_volume_up", "Volume Up", "Increase volume", "RT"),
                KeybindAction("am_volume_down", "Volume Down", "Decrease volume", "LT"),
                KeybindAction("am_shuffle", "Shuffle", "Toggle shuffle", "X"),
                KeybindAction("am_repeat", "Repeat", "Toggle repeat", "Y"),
                KeybindAction("am_lyrics", "Lyrics", "Show/hide lyrics", "B"),
            ],
            button_map={
                "A": "am_play_pause",
                "RB": "am_next",
                "LB": "am_prev",
                "RT": "am_volume_up",
                "LT": "am_volume_down",
                "X": "am_shuffle",
                "Y": "am_repeat",
                "B": "am_lyrics",
            },
            combo_map={}
        )
        
        # Preview mode
        self._modes["preview"] = ModeConfig(
            mode_id="preview",
            display_name="Preview",
            actions=[
                KeybindAction("zoom_in", "Zoom In", "Zoom in on document", "RT"),
                KeybindAction("zoom_out", "Zoom Out", "Zoom out of document", "LT"),
                KeybindAction("next_page", "Next Page", "Go to next page", "RB"),
                KeybindAction("prev_page", "Previous Page", "Go to previous page", "LB"),
                KeybindAction("rotate_left", "Rotate Left", "Rotate counterclockwise", "X"),
                KeybindAction("rotate_right", "Rotate Right", "Rotate clockwise", "Y"),
                KeybindAction("markup", "Markup", "Open markup toolbar", "A"),
                KeybindAction("share", "Share", "Open share sheet", "B"),
            ],
            button_map={
                "RT": "zoom_in",
                "LT": "zoom_out",
                "RB": "next_page",
                "LB": "prev_page",
                "X": "rotate_left",
                "Y": "rotate_right",
                "A": "markup",
                "B": "share",
            },
            combo_map={}
        )
        
        # VSCode mode
        self._modes["vscode"] = ModeConfig(
            mode_id="vscode",
            display_name="VS Code",
            actions=[
                KeybindAction("command_palette_vscode", "Command Palette", "Open command palette", "A"),
                KeybindAction("quick_open", "Quick Open", "Open quick file navigator", "Y"),
                KeybindAction("go_to_line", "Go to Line", "Jump to specific line", "X"),
                KeybindAction("toggle_terminal", "Toggle Terminal", "Show/hide integrated terminal", "B"),
                KeybindAction("next_editor", "Next Editor", "Switch to next editor tab", "RB"),
                KeybindAction("prev_editor", "Previous Editor", "Switch to previous editor tab", "LB"),
                KeybindAction("format_document", "Format Document", "Format current file", "View"),
                KeybindAction("save", "Save", "Save current file", "Menu"),
            ],
            button_map={
                "A": "command_palette_vscode",
                "Y": "quick_open",
                "X": "go_to_line",
                "B": "toggle_terminal",
                "RB": "next_editor",
                "LB": "prev_editor",
                "View": "format_document",
                "Menu": "save",
            },
            combo_map={}
        )
        
        # Notion mode
        self._modes["notion"] = ModeConfig(
            mode_id="notion",
            display_name="Notion",
            actions=[
                KeybindAction("new_page", "New Page", "Create new page", "Y"),
                KeybindAction("search_notion", "Search", "Open Notion search", "X"),
                KeybindAction("command_palette_notion", "Command Palette", "Open command palette", "A"),
                KeybindAction("toggle_sidebar_notion", "Toggle Sidebar", "Toggle sidebar visibility", "B"),
                KeybindAction("next_page_notion", "Next Page", "Navigate to next page", "RB"),
                KeybindAction("prev_page_notion", "Previous Page", "Navigate to previous page", "LB"),
                KeybindAction("add_comment", "Add Comment", "Add a comment", "RT"),
                KeybindAction("emoji", "Emoji", "Open emoji picker", "LT"),
            ],
            button_map={
                "Y": "new_page",
                "X": "search_notion",
                "A": "command_palette_notion",
                "B": "toggle_sidebar_notion",
                "RB": "next_page_notion",
                "LB": "prev_page_notion",
                "RT": "add_comment",
                "LT": "emoji",
            },
            combo_map={}
        )
        
        # Messages mode
        self._modes["messages"] = ModeConfig(
            mode_id="messages",
            display_name="Messages",
            actions=[
                KeybindAction("new_message", "New Message", "Start new conversation", "Y"),
                KeybindAction("search_messages", "Search", "Search messages", "X"),
                KeybindAction("send_message", "Send", "Send message", "A"),
                KeybindAction("add_emoji", "Add Emoji", "Add tapback reaction", "B"),
                KeybindAction("next_conversation", "Next Conversation", "Go to next conversation", "RB"),
                KeybindAction("prev_conversation", "Previous Conversation", "Go to previous conversation", "LB"),
                KeybindAction("details", "Details", "Show conversation details", "View"),
                KeybindAction("attachments", "Attachments", "Open attachments browser", "Menu"),
            ],
            button_map={
                "Y": "new_message",
                "X": "search_messages",
                "A": "send_message",
                "B": "add_emoji",
                "RB": "next_conversation",
                "LB": "prev_conversation",
                "View": "details",
                "Menu": "attachments",
            },
            combo_map={}
        )
        
        # WhatsApp mode
        self._modes["whatsapp"] = ModeConfig(
            mode_id="whatsapp",
            display_name="WhatsApp",
            actions=[
                KeybindAction("new_chat", "New Chat", "Start new chat", "Y"),
                KeybindAction("search_whatsapp", "Search", "Search chats", "X"),
                KeybindAction("send_message_whatsapp", "Send", "Send message", "A"),
                KeybindAction("attach", "Attach", "Attach file/media", "B"),
                KeybindAction("next_chat", "Next Chat", "Go to next chat", "RB"),
                KeybindAction("prev_chat", "Previous Chat", "Go to previous chat", "LB"),
                KeybindAction("archive", "Archive", "Archive chat", "View"),
                KeybindAction("mute", "Mute", "Mute chat", "Menu"),
            ],
            button_map={
                "Y": "new_chat",
                "X": "search_whatsapp",
                "A": "send_message_whatsapp",
                "B": "attach",
                "RB": "next_chat",
                "LB": "prev_chat",
                "View": "archive",
                "Menu": "mute",
            },
            combo_map={}
        )
    
    def get_mode_config(self, mode_id: str) -> Optional[ModeConfig]:
        """Get configuration for a specific mode."""
        return self._modes.get(mode_id)
    
    def get_all_modes(self) -> Dict[str, ModeConfig]:
        """Get all mode configurations."""
        return self._modes.copy()
    
    def save_to_file(self):
        """Save current configuration to file."""
        self.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        data = {}
        for mode_id, config in self._modes.items():
            data[mode_id] = {
                "mode_id": config.mode_id,
                "display_name": config.display_name,
                "actions": [
                    {
                        "action_id": a.action_id,
                        "display_name": a.display_name,
                        "description": a.description,
                        "default_button": a.default_button,
                        "is_combo": a.is_combo,
                    }
                    for a in config.actions
                ],
                "button_map": config.button_map,
                "combo_map": config.combo_map,
            }
        
        with open(self.CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved keybind config to {self.CONFIG_FILE}")
    
    def load_from_file(self) -> bool:
        """Load configuration from file. Returns True if successful."""
        if not self.CONFIG_FILE.exists():
            logger.info(f"Config file not found at {self.CONFIG_FILE}, using defaults")
            return False
        
        try:
            with open(self.CONFIG_FILE, "r") as f:
                data = json.load(f)
            
            for mode_id, mode_data in data.items():
                actions = [
                    KeybindAction(
                        action_id=a["action_id"],
                        display_name=a["display_name"],
                        description=a["description"],
                        default_button=a.get("default_button"),
                        is_combo=a.get("is_combo", False),
                    )
                    for a in mode_data.get("actions", [])
                ]
                
                self._modes[mode_id] = ModeConfig(
                    mode_id=mode_data["mode_id"],
                    display_name=mode_data["display_name"],
                    actions=actions,
                    button_map=mode_data.get("button_map", {}),
                    combo_map=mode_data.get("combo_map", {}),
                )
            
            logger.info(f"Loaded keybind config from {self.CONFIG_FILE}")
            return True
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Failed to load config: {e}")
            return False


# Global instance
_config: Optional[KeybindConfig] = None


def get_config() -> KeybindConfig:
    """Get the global keybind configuration."""
    global _config
    if _config is None:
        _config = KeybindConfig()
        _config.load_from_file()
    return _config


def reload_config() -> KeybindConfig:
    """Reload the configuration from file."""
    global _config
    _config = KeybindConfig()
    _config.load_from_file()
    return _config
