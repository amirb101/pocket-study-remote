"""
Keybinding editor GUI using tkinter.

Provides a clean interface to configure controller bindings per mode.
Click an action on the left, press a button on your controller to assign it.
"""

from __future__ import annotations

import logging
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable

from ..config.keybind_config import get_config, InputType, KeybindMapping
from ..core.gamepad_button import GamepadButton

logger = logging.getLogger(__name__)


class KeybindEditor:
    """GUI editor for controller keybindings."""

    def __init__(self) -> None:
        self.window: tk.Tk | None = None
        self.notebook: ttk.Notebook | None = None
        self.current_mode: str = "browser"
        self.waiting_for_input = False
        self.current_action_id: str | None = None
        self.input_callback: Callable[[GamepadButton, list[GamepadButton], float], None] | None = None
        self._input_thread: threading.Thread | None = None
        self._stop_input = False

    def show(self) -> None:
        """Show the keybinding editor window."""
        if self.window is not None:
            self.window.lift()
            return

        self.window = tk.Tk()
        self.window.title("Pocket Study Remote - Keybindings")
        self.window.geometry("600x500")
        self.window.minsize(500, 400)

        # Header
        header = tk.Frame(self.window, padx=10, pady=10)
        header.pack(fill=tk.X)
        tk.Label(
            header,
            text="Configure Controller Buttons",
            font=("Helvetica", 16, "bold"),
        ).pack(side=tk.LEFT)
        tk.Button(
            header,
            text="Reset All to Defaults",
            command=self._confirm_reset,
        ).pack(side=tk.RIGHT)

        # Instructions
        instructions = tk.Label(
            self.window,
            text="Click an action, then press the controller button you want to assign. "
                 "Hold multiple buttons for combos. Click 'Clear' to unassign.",
            wraplength=550,
            justify=tk.LEFT,
            padx=10,
            pady=5,
        )
        instructions.pack(fill=tk.X)

        # Mode tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create tabs for each mode
        config = get_config()
        for mode_id, mode_config in config.modes.items():
            self._create_mode_tab(mode_id, mode_config)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(
            self.window,
            textvariable=self.status_var,
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padx=5,
        )
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # Input listener thread
        self._stop_input = False
        self._input_thread = threading.Thread(target=self._input_listener, daemon=True)
        self._input_thread.start()

        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        self.window.mainloop()

    def _create_mode_tab(self, mode_id: str, mode_config) -> None:
        """Create a tab for a specific mode."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=mode_config.mode_name)

        # Create scrollable canvas
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW, width=560)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Header row
        header = tk.Frame(scrollable_frame, padx=5, pady=5)
        header.pack(fill=tk.X)
        tk.Label(header, text="Action", font=("Helvetica", 10, "bold"), width=25).pack(side=tk.LEFT)
        tk.Label(header, text="Current Binding", font=("Helvetica", 10, "bold"), width=20).pack(side=tk.LEFT)
        tk.Label(header, text="", width=10).pack(side=tk.LEFT)

        ttk.Separator(scrollable_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5)

        # Action rows
        for action in mode_config.actions:
            self._create_action_row(scrollable_frame, mode_id, action, mode_config)

    def _create_action_row(self, parent: tk.Frame, mode_id: str, action, mode_config) -> None:
        """Create a row for a single action."""
        row = tk.Frame(parent, padx=5, pady=3)
        row.pack(fill=tk.X)

        # Action name and description
        text_frame = tk.Frame(row, width=250)
        text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        text_frame.pack_propagate(False)

        tk.Label(
            text_frame,
            text=action.name,
            font=("Helvetica", 11),
            anchor=tk.W,
        ).pack(fill=tk.X)

        desc_label = tk.Label(
            text_frame,
            text=action.description,
            font=("Helvetica", 9),
            fg="gray",
            anchor=tk.W,
        )
        desc_label.pack(fill=tk.X)

        # Current binding display
        binding_var = tk.StringVar(value="Unassigned")
        binding_label = tk.Label(
            row,
            textvariable=binding_var,
            font=("Helvetica", 10),
            width=20,
            relief=tk.SUNKEN,
            bg="#f0f0f0",
            padx=5,
        )
        binding_label.pack(side=tk.LEFT, padx=5)

        # Update binding display
        self._update_binding_display(binding_var, mode_config, action.id)

        # Assign button
        assign_btn = tk.Button(
            row,
            text="Assign",
            command=lambda: self._start_assignment(mode_id, action.id, binding_var, mode_config),
        )
        assign_btn.pack(side=tk.LEFT, padx=2)

        # Clear button
        clear_btn = tk.Button(
            row,
            text="Clear",
            command=lambda: self._clear_assignment(mode_id, action.id, binding_var, mode_config),
        )
        clear_btn.pack(side=tk.LEFT, padx=2)

    def _update_binding_display(self, var: tk.StringVar, mode_config, action_id: str) -> None:
        """Update the binding display string."""
        mapping = mode_config.get_mapping_for_action(action_id)
        if not mapping:
            var.set("Unassigned")
            return

        if mapping.input_type == InputType.SIMPLE and mapping.button:
            var.set(mapping.button.display_name)
        elif mapping.input_type == InputType.COMBO and mapping.primary_button:
            held = " + ".join(b.display_name for b in mapping.held_buttons)
            var.set(f"{mapping.primary_button.display_name} + {held}")
        elif mapping.input_type == InputType.LONG_PRESS and mapping.button:
            var.set(f"{mapping.button.display_name} (hold)")
        else:
            var.set("Unknown")

    def _start_assignment(self, mode_id: str, action_id: str, var: tk.StringVar, mode_config) -> None:
        """Start waiting for controller input."""
        if self.waiting_for_input:
            messagebox.showwarning("Already Waiting", "Already waiting for button press. Press a button or click Cancel.")
            return

        self.current_mode = mode_id
        self.current_action_id = action_id
        self.waiting_for_input = True
        self.status_var.set(f"Press a button on your controller for: {mode_config.get_action_by_id(action_id).name}")

        # Callback when input is received
        def on_input(button: GamepadButton, held: list[GamepadButton], duration: float):
            if not self.waiting_for_input or self.current_action_id != action_id:
                return

            self.waiting_for_input = False
            self.status_var.set("Ready")

            # Determine input type
            if duration >= 0.5:
                # Long press
                mapping = KeybindMapping(
                    action_id=action_id,
                    input_type=InputType.LONG_PRESS,
                    button=button,
                    duration_ms=int(duration * 1000),
                )
            elif held:
                # Combo
                mapping = KeybindMapping(
                    action_id=action_id,
                    input_type=InputType.COMBO,
                    primary_button=button,
                    held_buttons=held,
                )
            else:
                # Simple press
                mapping = KeybindMapping(
                    action_id=action_id,
                    input_type=InputType.SIMPLE,
                    button=button,
                )

            # Save the mapping
            mode_config.set_mapping(mapping)
            get_config().save_mode(mode_config)

            # Update UI
            self._update_binding_display(var, mode_config, action_id)

            # Show confirmation
            if mapping.input_type == InputType.COMBO:
                msg = f"Assigned: {button.display_name} + {' + '.join(b.display_name for b in held)}"
            else:
                msg = f"Assigned: {button.display_name}"
            messagebox.showinfo("Button Assigned", msg)

        self.input_callback = on_input

    def _clear_assignment(self, mode_id: str, action_id: str, var: tk.StringVar, mode_config) -> None:
        """Clear the assignment for an action."""
        mode_config.clear_mapping(action_id)
        get_config().save_mode(mode_config)
        self._update_binding_display(var, mode_config, action_id)
        self.status_var.set("Assignment cleared")

    def _input_listener(self) -> None:
        """Background thread to listen for controller input."""
        # This is a placeholder - actual controller input would come from the main app
        # For now, we'll poll the calibration wizard if active
        while not self._stop_input:
            time.sleep(0.05)

    def _confirm_reset(self) -> None:
        """Confirm and reset all keybindings to defaults."""
        if messagebox.askyesno(
            "Reset All Keybindings?",
            "This will reset ALL modes to their default keybindings. "
            "Your custom settings will be lost.\n\nAre you sure?",
        ):
            config = get_config()
            config.modes.clear()
            config._create_defaults()
            messagebox.showinfo("Reset Complete", "All keybindings have been reset to defaults.")
            # Refresh the window
            self._on_close()
            self.show()

    def _on_close(self) -> None:
        """Close the editor window."""
        self._stop_input = True
        self.waiting_for_input = False
        if self.window:
            self.window.destroy()
            self.window = None


# Global editor instance
_editor: KeybindEditor | None = None


def show_keybind_editor() -> None:
    """Show the keybinding editor."""
    global _editor
    if _editor is None:
        _editor = KeybindEditor()
    # Run in a separate thread so it doesn't block the main app
    threading.Thread(target=_editor.show, daemon=True).start()
