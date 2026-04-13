"""Run with: ``python -m pocket_study_remote`` (from the repository root)."""

import sys
from pathlib import Path


def show_startup_choice():
    """Show startup dialog to choose between launch and configure."""
    import tkinter as tk
    from tkinter import ttk
    
    root = tk.Tk()
    root.title("Pocket Study Remote")
    root.geometry("450x200")
    root.resizable(False, False)
    
    # Center window
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"+{x}+{y}")
    
    # Main frame
    frame = tk.Frame(root, padx=20, pady=20)
    frame.pack(fill=tk.BOTH, expand=True)
    
    # Title
    tk.Label(
        frame,
        text="Pocket Study Remote",
        font=("Helvetica", 16, "bold"),
    ).pack(pady=(0, 10))
    
    # Instructions
    tk.Label(
        frame,
        text="Configure controller keybindings first?",
        font=("Helvetica", 12),
        wraplength=400,
    ).pack(pady=(0, 20))
    
    result = [None]  # Use list to store result from closure
    
    def on_yes():
        result[0] = True
        root.destroy()
    
    def on_no():
        result[0] = False
        root.destroy()
    
    # Button frame
    btn_frame = tk.Frame(frame)
    btn_frame.pack()
    
    tk.Button(
        btn_frame,
        text="Yes - Configure First",
        command=on_yes,
        bg="#2196F3",
        fg="white",
        font=("Helvetica", 11, "bold"),
        width=20,
        padx=10,
        pady=5,
    ).pack(side=tk.LEFT, padx=5)
    
    tk.Button(
        btn_frame,
        text="No - Launch Now",
        command=on_no,
        font=("Helvetica", 11),
        width=15,
        padx=10,
        pady=5,
    ).pack(side=tk.LEFT, padx=5)
    
    root.mainloop()
    return result[0]


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
