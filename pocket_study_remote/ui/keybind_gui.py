#!/usr/bin/env python3
"""
Standalone keybinding GUI - runs in separate process to avoid thread conflicts.

This file is launched as a subprocess so tkinter can run on its own main thread.
Controller button capture works via IPC with the main app.
"""

import json
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pocket_study_remote.config.keybind_config import get_config, InputType, KeybindMapping
from pocket_study_remote.core.gamepad_button import GamepadButton


class KeybindGUI:
    """GUI for editing keybindings with controller input capture."""

    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Pocket Study Remote - Keybindings")
        self.window.geometry("850x700")
        self.window.minsize(800, 600)

        # State
        self.button_vars = {}  # (mode_id, action_id) -> StringVar
        self.combo_vars = {}   # (mode_id, action_id) -> BooleanVar
        self.capturing = False

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
            text="Click 'Assign' next to an action, then press the button (or button combo) on your controller. "
                 "Check 'Combo' if you want to assign multiple buttons pressed together.",
            wraplength=750,
            justify=tk.LEFT,
            padx=10,
            pady=5,
        )
        self.instr_label.pack(fill=tk.X)

        # Status bar
        self.status_var = tk.StringVar(value="Ready - Click Assign to capture from controller")
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

        binding_label = tk.Label(
            row,
            textvariable=var,
            font=("Helvetica", 10, "bold"),
            width=18,
            relief=tk.SUNKEN,
            bg="#ffffff",
            fg="#333333",
            cursor="hand2",
        )
        binding_label.pack(side=tk.LEFT, padx=5)
        binding_label.bind("<Button-1>", lambda e: self._start_capture(mode_id, action.id, action.name))

        # Combo checkbox
        combo_var = tk.BooleanVar(value=False)
        self.combo_vars[(mode_id, action.id)] = combo_var
        
        if mapping and mapping.input_type == InputType.COMBO:
            combo_var.set(True)

        combo_check = tk.Checkbutton(
            row,
            text="Combo",
            variable=combo_var,
        )
        combo_check.pack(side=tk.LEFT, padx=2)

        # Assign button
        assign_btn = tk.Button(
            row,
            text="Assign",
            command=lambda: self._start_capture(mode_id, action.id, action.name),
            bg="#1976D2",
            fg="white",
            font=("Helvetica", 9, "bold"),
            relief=tk.RAISED,
            padx=8,
            pady=2,
        )
        assign_btn.pack(side=tk.LEFT, padx=3)

        # Clear button
        clear_btn = tk.Button(
            row,
            text="Clear",
            command=lambda: self._clear_assignment(mode_id, action.id, var, combo_var),
            bg="#757575",
            fg="white",
            font=("Helvetica", 9),
            relief=tk.RAISED,
            padx=8,
            pady=2,
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

    def _start_capture(self, mode_id: str, action_id: str, action_name: str):
        """Start capturing button input from controller using pygame."""
        if self.capturing:
            messagebox.showwarning("Already Capturing", "Already waiting for button press. Press a button or wait to cancel.")
            return

        self.capturing = True
        
        # Check combo mode
        is_combo = self.combo_vars[(mode_id, action_id)].get()
        
        self.status_var.set(f"CAPTURING: Press button{' COMBO' if is_combo else ''} on controller for: {action_name}")
        self.status_bar.configure(bg="#FFF3CD")
        self.instr_label.configure(text=f"Press any button on your controller now...\n(Combo mode: {is_combo})")

        # Start polling thread with pygame
        self.capture_thread = threading.Thread(
            target=self._poll_for_capture,
            args=(mode_id, action_id, is_combo),
            daemon=True
        )
        self.capture_thread.start()

    def _poll_for_capture(self, mode_id: str, action_id: str, is_combo: bool):
        """Poll for captured button using pygame/SDL directly in this process."""
        try:
            import pygame
            
            # Initialize pygame joystick
            pygame.init()
            pygame.joystick.init()
            
            # Wait for joystick
            joystick = None
            start_time = time.time()
            
            while time.time() - start_time < 30.0 and not joystick:
                pygame.joystick.init()
                if pygame.joystick.get_count() > 0:
                    joystick = pygame.joystick.Joystick(0)
                    joystick.init()
                    break
                time.sleep(0.1)
            
            if not joystick:
                # No joystick found
                self.window.after(0, self._capture_timeout)
                return
            
            # Poll for button press
            captured_button = None
            start_time = time.time()
            
            while time.time() - start_time < 30.0 and not captured_button:
                for event in pygame.event.get():
                    if event.type == pygame.JOYBUTTONDOWN:
                        # Map button index to GamepadButton
                        button_map = [
                            "A", "B", "X", "Y",  # 0,1,2,3
                            "LEFT_SHOULDER", "RIGHT_SHOULDER",  # 4,5
                            "LEFT_TRIGGER", "RIGHT_TRIGGER",  # 6,7
                            "SELECT", "START",  # 8,9
                        ]
                        if event.button < len(button_map):
                            captured_button = button_map[event.button]
                            break
                
                time.sleep(0.016)  # ~60Hz
            
            pygame.quit()
            
            if captured_button:
                self.window.after(0, lambda: self._apply_capture(mode_id, action_id, captured_button, is_combo))
            else:
                self.window.after(0, self._capture_timeout)
                
        except Exception as e:
            print(f"Capture error: {e}")
            self.window.after(0, self._capture_timeout)
        finally:
            self.capturing = False
            try:
                pygame.quit()
            except:
                pass

    def _apply_capture(self, mode_id: str, action_id: str, button_name: str, is_combo: bool):
        """Apply the captured button to the action."""
        config = get_config()
        mode_config = config.get_mode(mode_id)
        if not mode_config:
            return

        button = GamepadButton[button_name]
        
        if is_combo:
            # For combo, we need to capture a second button
            # For now, just make it a simple combo with A as primary
            mapping = KeybindMapping(
                action_id=action_id,
                input_type=InputType.COMBO,
                primary_button=button,
                held_buttons=[GamepadButton.A],  # Default combo partner
            )
        else:
            mapping = KeybindMapping(
                action_id=action_id,
                input_type=InputType.SIMPLE,
                button=button,
            )
        
        mode_config.set_mapping(mapping)
        
        # Update display
        display_text = self._format_mapping(mapping)
        self.button_vars[(mode_id, action_id)].set(display_text)
        
        self.status_var.set(f"Assigned {button_name} to {action_id}")
        self.status_bar.configure(bg="#D4EDDA")
        self.instr_label.configure(text="Click 'Assign' next to an action, then press the button on your controller.")
        
        messagebox.showinfo("Button Captured", f"Assigned: {display_text}")

    def _capture_timeout(self):
        """Handle capture timeout."""
        self.status_var.set("Capture timed out - no button pressed")
        self.status_bar.configure(bg="#f0f0f0")
        self.instr_label.configure(text="Click 'Assign' next to an action, then press the button on your controller.")

    def _clear_assignment(self, mode_id: str, action_id: str, var, combo_var):
        """Clear a button assignment."""
        config = get_config()
        mode_config = config.get_mode(mode_id)
        if mode_config:
            mode_config.clear_mapping(action_id)
            var.set("Unassigned")
            combo_var.set(False)
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
            # Reset combo checkboxes
            for var in self.combo_vars.values():
                var.set(False)
            self.status_var.set("Reset to defaults")

    def _save_and_close(self):
        """Save and close."""
        stop_listening()
        config = get_config()
        config._save()
        self.window.destroy()

    def _cancel(self):
        """Cancel without saving."""
        stop_listening()
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

    # Check if pygame is available
    try:
        import pygame
    except ImportError:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Missing Dependency",
            "pygame is required for controller input capture.\n\n"
            "Install with: pip install pygame"
        )
        root.destroy()
        sys.exit(1)

    gui = KeybindGUI()
    gui.run()
