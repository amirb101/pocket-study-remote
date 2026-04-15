"""Run with: ``python -m buttonbridge`` (from the repository root)."""

import sys

# Child process: keybind editor (works when frozen as a .app — no path to keybind_gui.py).
if "--buttonbridge-keybind-gui" in sys.argv:
    from buttonbridge.ui.keybind_gui import run_standalone

    run_standalone(readonly="--readonly" in sys.argv)
    raise SystemExit(0)


def show_startup_choice():
    """Show startup dialog to choose between launch and configure."""
    import tkinter as tk
    from tkinter import ttk
    
    root = tk.Tk()
    root.title("ButtonBridge")
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
        text="ButtonBridge",
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

    def on_close():
        # Treat window close as "launch now" to avoid a dead-end.
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
        fg="black",
        font=("Helvetica", 11, "bold"),
        width=20,
        padx=10,
        pady=5,
    ).pack(side=tk.LEFT, padx=5)
    
    tk.Button(
        btn_frame,
        text="No - Launch Now",
        command=on_no,
        bg="#e6e6e6",
        fg="black",
        font=("Helvetica", 11),
        width=15,
        padx=10,
        pady=5,
    ).pack(side=tk.LEFT, padx=5)

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
    return result[0]


def launch_keybinding_gui(readonly: bool = False) -> bool:
    """Launch the keybinding GUI in a subprocess (separate Tk main loop)."""
    from buttonbridge.ui.keybind_launch import launch_keybinding_gui as _launch

    return _launch(readonly=readonly)


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
                "Keybindings saved!\n\nLaunch ButtonBridge now?"
            )
            root.destroy()
            
            if launch:
                from buttonbridge.main import main as real_main
                real_main()
        return
    
    # Check if launched with --no-gui flag (skip startup dialog)
    if "--no-gui" in sys.argv:
        try:
            from buttonbridge.main import main as real_main
            real_main()
        except Exception as e:
            import tkinter as tk
            from tkinter import messagebox
            import traceback

            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "ButtonBridge launch failed",
                f"{e}\n\n{traceback.format_exc()}",
            )
            root.destroy()
        return
    
    # Show startup choice
    choice = show_startup_choice()
    
    if choice:
        # User wants to configure first
        if launch_keybinding_gui():
            # After GUI closes, launch main app
            try:
                from buttonbridge.main import main as real_main
                real_main()
            except Exception as e:
                import tkinter as tk
                from tkinter import messagebox
                import traceback

                root = tk.Tk()
                root.withdraw()
                messagebox.showerror(
                    "ButtonBridge launch failed",
                    f"{e}\n\n{traceback.format_exc()}",
                )
                root.destroy()
    else:
        # User wants to launch directly
        try:
            from buttonbridge.main import main as real_main
            real_main()
        except Exception as e:
            import tkinter as tk
            from tkinter import messagebox
            import traceback

            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "ButtonBridge launch failed",
                f"{e}\n\n{traceback.format_exc()}",
            )
            root.destroy()


if __name__ == "__main__":
    main()
