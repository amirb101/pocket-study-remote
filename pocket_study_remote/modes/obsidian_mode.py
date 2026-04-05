from __future__ import annotations

from ..core.action import Action, keystroke, open_app
from ..core.app_mode import AppMode
from ..core.gamepad_button import GamepadButton
from ..constants import BundleID


class ObsidianMode(AppMode):
    """
    Active when Obsidian is the frontmost application.

    This mode fires custom hotkeys that the user configures once in
    Obsidian's Settings → Hotkeys.  The README contains the exact setup
    table.  This approach is more robust than trying to integrate with
    Obsidian's internals.

    Required Obsidian hotkey setup
    ──────────────────────────────
    Open Obsidian → Settings → Hotkeys, search for each command:

    Command                      │ Assign to
    ─────────────────────────────┼───────────────
    Open today's daily note      │ Ctrl+Shift+D
    Toggle checklist status      │ Ctrl+Shift+C
    Insert template              │ Ctrl+Shift+T
    Open graph view              │ Ctrl+Shift+G

    The following already have defaults — no changes needed:
    - Quick switcher:    Cmd+O
    - Command palette:   Cmd+P
    - Navigate back:     Cmd+Opt+Left
    - Navigate forward:  Cmd+Opt+Right
    - Toggle sidebar:    Cmd+Backslash
    - Search all files:  Cmd+Shift+F
    - New note:          Cmd+N
    """

    id             = "obsidian"
    display_name   = "Obsidian"
    sf_symbol_name = "note.text"

    @property
    def button_map(self) -> dict[GamepadButton, Action]:
        return {
            # ── Face buttons ──────────────────────────────────────────
            # A = command palette: the "do anything" button
            GamepadButton.A: keystroke(
                "p", ["cmd"],
                id="obsidian-command-palette",
                name="Command Palette",
            ),
            # B = quick switcher: jump between notes by name
            GamepadButton.B: keystroke(
                "o", ["cmd"],
                id="obsidian-quick-switcher",
                name="Quick Switcher",
            ),
            # X = today's daily note (requires custom hotkey in Obsidian)
            GamepadButton.X: keystroke(
                "d", ["ctrl", "shift"],
                id="obsidian-daily-note",
                name="Today's Daily Note",
            ),
            # Y = toggle checklist item (requires custom hotkey)
            GamepadButton.Y: keystroke(
                "c", ["ctrl", "shift"],
                id="obsidian-toggle-checklist",
                name="Toggle Checklist",
            ),

            # ── D-pad ─────────────────────────────────────────────────
            GamepadButton.DPAD_LEFT: keystroke(
                "left_arrow", ["cmd", "opt"],
                id="obsidian-navigate-back",
                name="Navigate Back",
            ),
            GamepadButton.DPAD_RIGHT: keystroke(
                "right_arrow", ["cmd", "opt"],
                id="obsidian-navigate-forward",
                name="Navigate Forward",
            ),
            # Up/down unassigned — scrolling is better via trackpad in a writing app

            # ── Shoulder buttons ──────────────────────────────────────
            GamepadButton.LEFT_SHOULDER: keystroke(
                "backslash", ["cmd"],
                id="obsidian-toggle-sidebar",
                name="Toggle Left Sidebar",
            ),
            GamepadButton.RIGHT_SHOULDER: keystroke(
                "f", ["cmd", "shift"],
                id="obsidian-search-all",
                name="Search All Files",
            ),

            # ── Triggers ─────────────────────────────────────────────
            # L2 = insert template (requires custom hotkey)
            GamepadButton.LEFT_TRIGGER: keystroke(
                "t", ["ctrl", "shift"],
                id="obsidian-insert-template",
                name="Insert Template",
            ),
            # R2 = graph view (requires custom hotkey)
            GamepadButton.RIGHT_TRIGGER: keystroke(
                "g", ["ctrl", "shift"],
                id="obsidian-graph-view",
                name="Graph View",
            ),

            # ── Menu buttons ──────────────────────────────────────────
            GamepadButton.START: keystroke(
                "n", ["cmd"],
                id="obsidian-new-note",
                name="New Note",
            ),
            GamepadButton.SELECT: keystroke(
                "f", ["cmd", "shift"],
                id="obsidian-search",
                name="Search",
            ),
        }
