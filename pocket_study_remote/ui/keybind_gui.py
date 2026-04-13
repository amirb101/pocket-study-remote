#!/usr/bin/env python3
"""
Standalone keybinding GUI - runs in separate process to avoid thread conflicts.

This file is launched as a subprocess so tkinter can run on its own main thread.
"""

import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pocket_study_remote.config.keybind_config import get_config, InputType, KeybindMapping
from pocket_study_remote.core.gamepad_button import GamepadButton


class KeybindGUI:
    """GUI for editing keybindings."""

    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Pocket Study Remote - Keybindings")
        self.window.geometry("850x700")
        self.window.minsize(800, 600)

        # State
        self.button_vars = {}  # (mode_id, action_id) -> StringVar

        self._build_ui()
        self._load_config()

    def _build_ui(self):
        """Build the user interface."""
        # Header
        header = tk.Frame(self.window, padx=10, pady=10)
        header.pack(fill=tk.X)
        tk.Label(
            header,
            text="Controller Keybindings",
            font=("Helvetica", 18, "bold"),
        ).pack(side=tk.LEFT)

        # Instructions
        self.instr_label = tk.Label(
            self.window,
            text="Select a button from the dropdown for each action you want to assign. "
                 "Use the 'Clear' button to unassign an action.",
            wraplength=750,
            justify=tk.LEFT,
            padx=10,
            pady=5,
        )
        self.instr_label.pack(fill=tk.X)

        # Status bar
        self.status_var = tk.StringVar(value="Ready - Select buttons from dropdowns to assign")
        self.status_bar = tk.Label(
            self.window,
            textvariable=self.status_var,
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padx=5,
            bg="#f0f0f0",
        )
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # Mode tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Buttons
        btn_frame = tk.Frame(self.window, padx=10, pady=10)
        btn_frame.pack(fill=tk.X)

        tk.Button(
            btn_frame,
            text="Reset All to Defaults",
            command=self._reset_all,
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="Save & Close",
            command=self._save_and_close,
            bg="#4CAF50",
            fg="white",
            font=("Helvetica", 10, "bold"),
        ).pack(side=tk.RIGHT, padx=5)

        tk.Button(
            btn_frame,
            text="Cancel",
            command=self._cancel,
        ).pack(side=tk.RIGHT, padx=5)

    def _load_config(self):
        """Load configuration and build tabs."""
        config = get_config()

        for mode_id, mode_config in config.modes.items():
            self._create_mode_tab(mode_id, mode_config)

    def _create_mode_tab(self, mode_id: str, mode_config):
        """Create a tab for a mode."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=mode_config.mode_name)

        # Scrollable canvas
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW, width=750)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Header
        header = tk.Frame(scrollable_frame, padx=5, pady=5)
        header.pack(fill=tk.X)
        tk.Label(header, text="Action", font=("Helvetica", 10, "bold"), width=20).pack(side=tk.LEFT)
        tk.Label(header, text="Description", font=("Helvetica", 10, "bold"), width=30).pack(side=tk.LEFT)
        tk.Label(header, text="Assigned Button", font=("Helvetica", 10, "bold"), width=20).pack(side=tk.LEFT)
        tk.Label(header, text="Combo", font=("Helvetica", 10, "bold"), width=8).pack(side=tk.LEFT)
        tk.Label(header, text="", width=10).pack(side=tk.LEFT)

        ttk.Separator(scrollable_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5)

        # Actions
        for action in mode_config.actions:
            self._create_action_row(scrollable_frame, mode_id, action, mode_config)

    def _create_action_row(self, parent, mode_id: str, action, mode_config):
        """Create a row for an action."""
        row = tk.Frame(parent, padx=5, pady=3)
        row.pack(fill=tk.X)

        # Action name
        tk.Label(row, text=action.name, font=("Helvetica", 11), width=20, anchor=tk.W).pack(side=tk.LEFT)

        # Description
        tk.Label(
            row,
            text=action.description,
            font=("Helvetica", 9),
            fg="gray",
            width=30,
            anchor=tk.W,
        ).pack(side=tk.LEFT)

        # Current binding display (clickable)
        var = tk.StringVar(value="Unassigned")
        self.button_vars[(mode_id, action.id)] = var

        # Update from config
        mapping = mode_config.get_mapping_for_action(action.id)
        if mapping:
            var.set(self._format_mapping(mapping))

        # Button dropdown
        button_choices = ["Unassigned"] + [b.name for b in GamepadButton]
        current = "Unassigned"
        if mapping and mapping.button:
            current = mapping.button.name

        dropdown = ttk.Combobox(
            row,
            textvariable=var,
            values=button_choices,
            width=15,
            state="readonly",
        )
        dropdown.set(current)
        dropdown.pack(side=tk.LEFT, padx=5)
        dropdown.bind("<<ComboboxSelected>>", lambda e: self._on_button_selected(mode_id, action.id, var.get()))

        # Clear button
        clear_btn = tk.Button(
            row,
            text="Clear",
            command=lambda: self._clear_assignment(mode_id, action.id, var),
            bg="#555555",
            fg="white",
            font=("Helvetica", 9),
            relief=tk.RAISED,
            padx=10,
            pady=3,
        )
        clear_btn.pack(side=tk.LEFT, padx=3)

    def _format_mapping(self, mapping) -> str:
        """Format a mapping for display."""
        if mapping.input_type == InputType.SIMPLE and mapping.button:
            return mapping.button.display_name
        elif mapping.input_type == InputType.COMBO and mapping.primary_button:
            held = "+".join(b.name for b in mapping.held_buttons)
            return f"{mapping.primary_button.name}+{held}"
        elif mapping.input_type == InputType.LONG_PRESS and mapping.button:
            return f"{mapping.button.display_name} (hold)"
        return "Unassigned"

    def _on_button_selected(self, mode_id: str, action_id: str, button_name: str):
        """Handle button selection from dropdown."""
        config = get_config()
        mode_config = config.get_mode(mode_id)
        if not mode_config:
            return

        if button_name == "Unassigned":
            mode_config.remove_mapping(action_id)
            self.status_var.set(f"Cleared assignment for {action_id}")
        else:
            button = GamepadButton[button_name]
            mapping = KeybindMapping(
                action_id=action_id,
                input_type=InputType.SIMPLE,
                button=button,
            )
            mode_config.set_mapping(mapping)
            self.status_var.set(f"Assigned {button.name} to {action_id}")

    def _clear_assignment(self, mode_id: str, action_id: str, var):
        """Clear a button assignment."""
        config = get_config()
        mode_config = config.get_mode(mode_id)
        if mode_config:
            mode_config.remove_mapping(action_id)
            var.set("Unassigned")
            self.status_var.set(f"Cleared binding for {action_id}")
            self.status_bar.configure(bg="#f0f0f0")

    def _reset_all(self):
        """Reset all to defaults."""
        if messagebox.askyesno(
            "Reset All?",
            "This will reset ALL keybindings to defaults. Continue?",
        ):
            config = get_config()
            config.modes.clear()
            config._create_defaults()
            # Refresh display
            for (mode_id, action_id), var in self.button_vars.items():
                mode_config = config.get_mode(mode_id)
                if mode_config:
                    mapping = mode_config.get_mapping_for_action(action_id)
                    var.set(self._format_mapping(mapping) if mapping else "Unassigned")
            self.status_var.set("Reset to defaults")

    def _save_and_close(self):
        """Save and close."""
        config = get_config()
        config._save()
        self.window.destroy()

    def _cancel(self):
        """Cancel without saving."""
        self.window.destroy()

    def run(self):
        """Run the GUI."""
        self.window.mainloop()


if __name__ == "__main__":
    # Ensure config exists
    from pathlib import Path
    config_path = Path.home() / ".config" / "pocket-study-remote" / "keybindings.json"
    if not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        get_config()

    gui = KeybindGUI()
    gui.run()
