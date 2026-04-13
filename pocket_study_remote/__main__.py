"""Run with: ``python -m pocket_study_remote`` (from the repository root)."""

import sys
from pathlib import Path


def show_startup_choice():
    """Show startup dialog to choose between launch and configure."""
    import tkinter as tk
    from tkinter import messagebox
    
    root = tk.Tk()
    root.withdraw()  # Hide main window
    
    # Show choice dialog
    result = messagebox.askyesno(
        "Pocket Study Remote",
        "Welcome!\n\nWould you like to configure controller keybindings first?\n\n"
        "Select:\n"
        "• Yes - Configure keybindings (then launch)\n"
        "• No - Launch directly with current settings",
        icon="question",
    )
    
    root.destroy()
    return result


def launch_keybinding_gui():
    """Launch the keybinding GUI and wait for it to close."""
    import subprocess
    
    gui_path = Path(__file__).parent / "ui" / "keybind_gui.py"
    
    # Launch GUI and wait for it to close
    result = subprocess.run(
        [sys.executable, str(gui_path)],
        check=False,
    )
    
    return result.returncode == 0


def main():
    """Entry point with startup choice."""
    # Check if launched with --configure flag
    if "--configure" in sys.argv:
        if launch_keybinding_gui():
            # After GUI, ask if they want to launch main app
            import tkinter as tk
            from tkinter import messagebox
            
            root = tk.Tk()
            root.withdraw()
            launch = messagebox.askyesno(
                "Configuration Complete",
                "Keybindings saved!\n\nLaunch Pocket Study Remote now?"
            )
            root.destroy()
            
            if launch:
                from pocket_study_remote.main import main as real_main
                real_main()
        return
    
    # Check if launched with --no-gui flag (skip startup dialog)
    if "--no-gui" in sys.argv:
        from pocket_study_remote.main import main as real_main
        real_main()
        return
    
    # Show startup choice
    choice = show_startup_choice()
    
    if choice:
        # User wants to configure first
        if launch_keybinding_gui():
            # After GUI closes, launch main app
            from pocket_study_remote.main import main as real_main
            real_main()
    else:
        # User wants to launch directly
        from pocket_study_remote.main import main as real_main
        real_main()


if __name__ == "__main__":
    main()
