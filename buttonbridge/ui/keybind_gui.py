#!/usr/bin/env python3
"""Standalone Tkinter GUI for editing keybindings - runs in subprocess."""

import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from buttonbridge.config.keybind_config import load_config, save_config, get_default_config
from buttonbridge.core.gamepad_button import GamepadButton
from buttonbridge.core.app_mode import AppMode


class KeybindGUI:
    """GUI for editing controller keybindings."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("ButtonBridge - Keybind Editor")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Load configuration
        self.config = load_config()
        self.modified_config = {mode: dict(actions) for mode, actions in self.config.items()}
        
        # Track UI elements for each action
        self.bind_widgets = {}
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the user interface."""
        # Header
        header = ttk.Frame(self.root, padding="10")
        header.pack(fill="x")
        
        ttk.Label(
            header, 
            text="ButtonBridge Keybind Editor",
            font=("Helvetica", 16, "bold")
        ).pack(side="left")
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.root, padding="5")
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create tab for each mode
        self.mode_tabs = {}
        for mode in AppMode:
            tab = self._create_mode_tab(mode)
            self.notebook.add(tab, text=mode.value.title())
            self.mode_tabs[mode] = tab
        
        # Buttons at bottom
        button_frame = ttk.Frame(self.root, padding="10")
        button_frame.pack(fill="x", side="bottom")
        
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
    
    def _create_mode_tab(self, mode: AppMode) -> ttk.Frame:
        """Create a tab for a specific mode."""
        tab = ttk.Frame(self.notebook, padding="10")
        
        # Scrollable frame for actions
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas, padding="5")
        
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=760)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Headers
        ttk.Label(scroll_frame, text="Action", font=("Helvetica", 10, "bold")).grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        ttk.Label(scroll_frame, text="Button", font=("Helvetica", 10, "bold")).grid(
            row=0, column=1, sticky="w", padx=5, pady=5
        )
        
        # Get actions for this mode
        actions = self.modified_config.get(mode.value, {})
        
        # Create dropdown for each action
        for idx, (action_name, current_button) in enumerate(actions.items(), start=1):
            ttk.Label(scroll_frame, text=action_name).grid(
                row=idx, column=0, sticky="w", padx=5, pady=3
            )
            
            # Button dropdown
            button_var = tk.StringVar(value=current_button)
            dropdown = ttk.Combobox(
                scroll_frame,
                textvariable=button_var,
                values=[b.value for b in GamepadButton],
                state="readonly",
                width=20
            )
            dropdown.grid(row=idx, column=1, sticky="w", padx=5, pady=3)
            
            # Store reference
            self.bind_widgets[(mode.value, action_name)] = (dropdown, button_var)
        
        return tab
    
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
        for (mode, action), (_, var) in self.bind_widgets.items():
            if mode in self.modified_config and action in self.modified_config[mode]:
                var.set(self.modified_config[mode][action])
    
    def _cancel(self):
        """Close without saving."""
        self.root.destroy()
    
    def _save_and_close(self):
        """Save configuration and close."""
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


if __name__ == "__main__":
    root = tk.Tk()
    app = KeybindGUI(root)
    root.mainloop()
