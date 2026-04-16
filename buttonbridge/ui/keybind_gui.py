#!/usr/bin/env python3
"""Standalone Tkinter GUI for editing keybindings - runs in subprocess."""

import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from buttonbridge.config.keybind_config import (
    get_default_config,
    load_config,
    load_hotkey_list,
    save_config,
)
from buttonbridge.core.gamepad_button import GamepadButton

UNASSIGNED = "Unassigned"


class KeybindGUI:
    """GUI for editing controller keybindings."""
    
    def __init__(self, root, readonly: bool = False):
        self.root = root
        self.readonly = readonly
        self.root.title("ButtonBridge - Hotkey List" if readonly else "ButtonBridge - Keybind Editor")
        self.root.geometry("620x480" if readonly else "500x480")
        self.root.minsize(460, 360)
        
        # Load configuration (readonly: controller + macOS shortcut per action)
        self.config = load_hotkey_list() if readonly else load_config()
        self.modified_config = {mode: dict(actions) for mode, actions in self.config.items()}
        
        # Track UI elements for each action
        self.bind_widgets = {}
        self.active_mode_id: str | None = None
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the user interface."""
        # Header
        header = ttk.Frame(self.root, padding="10")
        header.pack(fill="x")
        
        ttk.Label(
            header, 
            text="ButtonBridge Hotkey List" if self.readonly else "ButtonBridge Keybind Editor",
            font=("Helvetica", 16, "bold")
        ).pack(side="left")
        if self.readonly:
            hint = ttk.Frame(self.root, padding=(10, 0, 10, 4))
            hint.pack(fill="x")
            ttk.Label(
                hint,
                text="Each row shows which controller button is bound and which macOS shortcut it sends in this mode.",
                font=("Helvetica", 9),
                foreground="#555",
                wraplength=580,
            ).pack(anchor="w")
        
        # Mode selector (replaces crowded tabs)
        mode_selector = ttk.Frame(self.root, padding=(10, 0, 10, 5))
        mode_selector.pack(fill="x")
        ttk.Label(mode_selector, text="Mode:", font=("Helvetica", 10, "bold")).pack(side="left")
        self.mode_var = tk.StringVar()
        self.mode_choices = sorted(self.config.keys())
        self.mode_dropdown = ttk.Combobox(
            mode_selector,
            textvariable=self.mode_var,
            values=[m.replace("_", " ").title() for m in self.mode_choices],
            state="readonly",
            width=28,
        )
        self.mode_dropdown.pack(side="left", padx=8)
        self.mode_dropdown.bind("<<ComboboxSelected>>", self._on_mode_changed)

        # Shared panel area
        self.mode_container = ttk.Frame(self.root, padding="5")
        self.mode_container.pack(fill="both", expand=True, padx=10, pady=5)

        # Build first mode view
        if self.mode_choices:
            self.mode_var.set(self.mode_choices[0].replace("_", " ").title())
            self._render_mode(self.mode_choices[0])
        
        # Buttons at bottom
        button_frame = ttk.Frame(self.root, padding="10")
        button_frame.pack(fill="x", side="bottom")

        if self.readonly:
            ttk.Button(
                button_frame,
                text="Close",
                command=self._cancel,
            ).pack(side="right", padx=5)
        else:
            ttk.Button(
                button_frame, 
                text="Reset All to Defaults",
                command=self._reset_all
            ).pack(side="left", padx=5)
            
            ttk.Button(
                button_frame,
                text="Cancel",
                command=self._cancel
            ).pack(side="right", padx=5)
            
            ttk.Button(
                button_frame,
                text="Save & Close",
                command=self._save_and_close
            ).pack(side="right", padx=5)
    
    def _create_mode_panel(self, parent: ttk.Frame, mode_id: str) -> ttk.Frame:
        """Create panel content for a specific mode."""
        tab = ttk.Frame(parent, padding="10")
        
        # Scrollable frame for actions
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas, padding="5")
        
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window(
            (0, 0),
            window=scroll_frame,
            anchor="nw",
            width=600 if self.readonly else 560,
        )
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Headers
        ttk.Label(scroll_frame, text="Action", font=("Helvetica", 10, "bold")).grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        if self.readonly:
            ttk.Label(
                scroll_frame,
                text="Controller",
                font=("Helvetica", 10, "bold"),
            ).grid(row=0, column=1, sticky="w", padx=5, pady=5)
            ttk.Label(
                scroll_frame,
                text="Sends (macOS)",
                font=("Helvetica", 10, "bold"),
            ).grid(row=0, column=2, sticky="w", padx=5, pady=5)
        else:
            ttk.Label(
                scroll_frame,
                text="Button",
                font=("Helvetica", 10, "bold"),
            ).grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        # Get actions for this mode
        actions = self.modified_config.get(mode_id, {})
        
        # Create dropdown for each action
        for idx, (action_name, info) in enumerate(actions.items(), start=1):
            ttk.Label(scroll_frame, text=action_name).grid(
                row=idx, column=0, sticky="w", padx=5, pady=3
            )
            
            if self.readonly:
                btn = info.get("button", "—")
                keys = info.get("keys", "—")
                btn_var = tk.StringVar(value=btn)
                keys_var = tk.StringVar(value=keys)
                ttk.Label(scroll_frame, textvariable=btn_var, width=14).grid(
                    row=idx, column=1, sticky="w", padx=5, pady=3
                )
                ttk.Label(scroll_frame, textvariable=keys_var, width=28).grid(
                    row=idx, column=2, sticky="w", padx=5, pady=3
                )
                self.bind_widgets[(mode_id, action_name)] = (btn_var, keys_var)
            else:
                # Button dropdown
                button_var = tk.StringVar(value=info)
                dropdown = ttk.Combobox(
                    scroll_frame,
                    textvariable=button_var,
                    values=[UNASSIGNED] + [b.value for b in GamepadButton],
                    state="readonly",
                    width=20
                )
                dropdown.grid(row=idx, column=1, sticky="w", padx=5, pady=3)
                
                # Store reference
                self.bind_widgets[(mode_id, action_name)] = (dropdown, button_var)
        
        return tab

    def _save_current_mode_from_widgets(self) -> None:
        """Persist on-screen edits for the active mode to modified_config."""
        if self.readonly:
            return
        if not self.active_mode_id:
            return
        for (mode, action), (_, var) in self.bind_widgets.items():
            if mode == self.active_mode_id:
                self.modified_config[mode][action] = var.get()

    def _render_mode(self, mode_id: str) -> None:
        """Render exactly one mode panel."""
        # Save current state before switching.
        self._save_current_mode_from_widgets()
        self.active_mode_id = mode_id

        # Clear previous content/widgets.
        for child in self.mode_container.winfo_children():
            child.destroy()
        self.bind_widgets = {
            key: value for key, value in self.bind_widgets.items() if key[0] != mode_id
        }

        panel = self._create_mode_panel(self.mode_container, mode_id)
        panel.pack(fill="both", expand=True)

    def _on_mode_changed(self, _event=None):
        """Handle mode dropdown change."""
        label = self.mode_var.get()
        normalized = label.lower().replace(" ", "_")
        if normalized in self.modified_config:
            self._render_mode(normalized)
    
    def _reset_all(self):
        """Reset all keybindings to defaults."""
        if messagebox.askyesno(
            "Reset All",
            "Are you sure you want to reset all keybindings to defaults?"
        ):
            self.modified_config = get_default_config()
            self._refresh_ui()
    
    def _refresh_ui(self):
        """Refresh the UI with current configuration."""
        if self.readonly:
            for (mode, action), (btn_var, keys_var) in self.bind_widgets.items():
                if mode in self.modified_config and action in self.modified_config[mode]:
                    cell = self.modified_config[mode][action]
                    if isinstance(cell, dict):
                        btn_var.set(cell.get("button", ""))
                        keys_var.set(cell.get("keys", ""))
            return
        for (mode, action), (_, var) in self.bind_widgets.items():
            if mode in self.modified_config and action in self.modified_config[mode]:
                var.set(self.modified_config[mode][action])
    
    def _cancel(self):
        """Close without saving."""
        self.root.destroy()
    
    def _save_and_close(self):
        """Save configuration and close."""
        if self.readonly:
            self.root.destroy()
            return
        self._save_current_mode_from_widgets()
        # Collect all bindings from UI
        for (mode, action), (_, var) in self.bind_widgets.items():
            self.modified_config[mode][action] = var.get()
        
        # Save to file
        try:
            save_config(self.modified_config)
            messagebox.showinfo("Success", "Configuration saved successfully!")
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")


def run_standalone(readonly: bool = False) -> None:
    """Entry point for subprocess / ``python -m buttonbridge --buttonbridge-keybind-gui``."""
    root = tk.Tk()
    KeybindGUI(root, readonly=readonly)
    root.mainloop()


if __name__ == "__main__":
    run_standalone()
