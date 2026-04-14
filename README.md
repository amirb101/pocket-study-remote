# ButtonBridge

A context-aware macOS menu bar app that maps a Bluetooth gamepad (for example an **8BitDo Micro**) to keyboard shortcuts and system actions. It detects the frontmost application and switches mappings automatically.

There is **no main document window** — only the menu bar icon (and a Dock tile while you run it from Terminal). Background work starts at launch; you do not need to click anything to “start” the app.

Repository: **https://github.com/amirb101/buttonbridge**

---

## Modes (high level)

| Category | When active | Examples |
|----------|-------------|----------|
| **Media** | Spotify, Apple Music | Play/pause, tracks, volume |
| **Browser** | Common browsers | Tabs, back/forward, address bar |
| **Productivity** | Obsidian, Notion, Preview, Finder | Navigation, search, files |
| **Development** | VS Code, Cursor | Command palette, terminal, find |
| **Communication** | Messages, WhatsApp, FaceTime, Phone | Send, search, call controls |
| **Global** | Everything else | System volume, music, Spotlight, screenshots, spaces |

Per-button mappings are editable in the keybinding GUI; defaults live under `~/.buttonbridge/`.

---

## Setup

### 1. Controller

Pair via Bluetooth: hold the pairing button until the lights flash, then add the device in **System Settings → Bluetooth**.

On macOS the app uses **Apple GameController** for input. If the pad never connects, try the controller’s **mode switch** (e.g. **X** or **S** for a standard gamepad profile). The `button_logger` tool may use pygame/SDL for diagnostics.

### 2. Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Accessibility permission

The app posts keyboard events via the accessibility stack. There is no `.app` bundle: macOS grants access to the **Python interpreter** you actually run.

1. Start the app the same way you always will (e.g. `./scripts/run.sh` or `python -m buttonbridge` inside the venv).
2. Read the startup log for the interpreter path to add if keystrokes fail.
3. **System Settings → Privacy & Security → Accessibility →** use **+** and add that `python3` binary (⌘⇧G in the picker helps).

If you use **Cursor’s** terminal, you may need that interpreter on the list, not only Terminal.app. Remove stale paths after recreating `.venv`.

### 4. Run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m buttonbridge
```

Or:

```bash
./scripts/run.sh
```

---

## Verify button mapping

```bash
python -m buttonbridge.tools.button_logger
```

Press each control and compare indices to `buttonbridge/constants.py` → `Controller.ButtonIndex` if anything differs on your hardware.

If the main app shows “Not connected”, check **System Settings → Game Controllers**, re-pair if needed, and confirm DEBUG logs mention GameController.

---

## Obsidian hotkey setup (optional)

If you use custom Obsidian shortcuts, align them in **Obsidian → Settings → Hotkeys** with what your mode sends, or remap actions in the keybinding GUI.

---

## Confirm Comet’s bundle ID (optional)

```bash
mdls -name kMDItemCFBundleIdentifier /Applications/Comet.app
```

If it differs from `ai.perplexity.comet`, update `buttonbridge/constants.py` → `BundleID.COMET`.

---

## Project structure

```
buttonbridge/
├── __main__.py
├── main.py
├── constants.py
├── core/
├── controller/
├── detection/
├── routing/
├── executors/
├── modes/              # One module per app mode
├── config/             # Keybinding persistence
├── ui/
└── tools/
```

---

## Adding a new mode

1. Add `buttonbridge/modes/yourapp_mode.py` (subclass `ConfigurableMode`).
2. Add bundle ID(s) in `buttonbridge/constants.py` → `BundleID`.
3. Register in `buttonbridge/main.py` → `_build_registry()`.
4. Add defaults in `buttonbridge/config/keybind_config.py` if you want GUI rows out of the box.

---

## Architecture notes

**AppleScript** is often run via `osascript` in a subprocess for clarity and easy debugging.

**App detection** uses a short-interval poll from a background thread so it does not fight the AppKit main loop owned by rumps.

**Gamepad input** on macOS is wired through **GameController** in the main app path; pygame may still appear in tools or fallbacks depending on your checkout.

---

## License

MIT — fork and adapt for your machine.
