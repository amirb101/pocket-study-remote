# Pocket Study Remote (Python)

A context-aware macOS menu bar app that turns an **8BitDo Micro** gamepad into a
study and life remote. Auto-detects the frontmost app and switches button mappings.

There is **no main document window** — only the menu bar icon (and the Dock tile while Terminal runs `run.sh`). Background threads start automatically at launch; you do not need to click anything to “start” the app.

## Modes

| Mode | Active when | Primary use |
|---|---|---|
| **Spotify** | Spotify is frontmost | Play/pause, next/prev, seek, volume, shuffle |
| **Browser** | Comet / Chrome / Arc / Edge | Tab navigation, back/forward, new tab, bookmark combo |
| **Obsidian** | Obsidian is frontmost | Daily note, checklist, command palette, note history |
| **Global** | Anything else | Music, volume, screenshots, Space switching, open apps |

---

## Setup

### 1. Controller

Set the physical switch on the bottom of the 8BitDo Micro to **D** (Direct Input).
Pair via Bluetooth: hold the pairing button until the lights flash, then add in
macOS System Settings → Bluetooth.

### 2. Python environment

```bash
# Recommended: use a virtual environment
python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Accessibility permission

The app sends keyboard shortcuts via the Core Graphics event system, which
requires Accessibility access:

System Settings → Privacy & Security → Accessibility → add Terminal (or your
Python interpreter) → toggle on.

You only do this once. The app logs a warning on startup if it's missing.

### 4. Run

```bash
# From the repository root:
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pocket_study_remote
```

Or use `./scripts/run.sh` (creates `.venv`, installs deps, runs the app).

---

## Verify button mapping

The 8BitDo Micro's button indices in D mode can vary slightly between firmware
versions. Before running the main app, confirm the mapping on your unit:

```bash
python -m pocket_study_remote.tools.button_logger
```

Press every button and note the index printed for each. If anything differs
from the defaults, update `pocket_study_remote/constants.py` → `Controller.ButtonIndex`.

---

## Obsidian hotkey setup

The Obsidian mode fires custom hotkeys. Open Obsidian → Settings → Hotkeys
and assign:

| Command | Shortcut |
|---|---|
| Open today's daily note | `Ctrl+Shift+D` |
| Toggle checklist status | `Ctrl+Shift+C` |
| Insert template | `Ctrl+Shift+T` |
| Open graph view | `Ctrl+Shift+G` |

The remaining buttons use Obsidian's defaults (Cmd+P, Cmd+O, Cmd+N, etc.).

---

## Confirm Comet's bundle ID

```bash
mdls -name kMDItemCFBundleIdentifier /Applications/Comet.app
```

Update `constants.py → BundleID.COMET` if it differs from `ai.perplexity.comet`.

---

## Project structure

```
pocket_study_remote/
├── __init__.py
├── main.py                     — entry point, dependency wiring
├── constants.py                — all magic numbers and bundle IDs
├── requirements.txt
├── core/
│   ├── action.py               — Action dataclass + factory functions
│   ├── app_mode.py             — AppMode abstract base class
│   ├── button_combo.py         — ButtonCombo frozen dataclass
│   ├── gamepad_button.py       — GamepadButton enum
│   └── mode_registry.py        — bundle ID → mode resolution
├── controller/
│   └── controller_manager.py   — pygame gamepad polling (background thread)
├── detection/
│   └── app_detector.py         — NSWorkspace polling (background thread)
├── routing/
│   └── action_router.py        — combo detection + action dispatch
├── executors/
│   ├── applescript_executor.py — subprocess osascript, async queue
│   └── keystroke_executor.py   — CGEventPost via PyObjC Quartz
├── modes/
│   ├── global_mode.py
│   ├── spotify_mode.py
│   ├── browser_mode.py
│   └── obsidian_mode.py
├── ui/
│   └── menu_bar.py             — rumps MenuBarApp
└── tools/
    └── button_logger.py        — debug tool: prints raw joystick events
```

---

## Adding a new mode

1. Create `modes/word_mode.py` — subclass `AppMode`, define `button_map`
2. Add the bundle ID to `constants.py → BundleID`
3. Add one line in `main.py → _build_registry()`:
   ```python
   registry.register(WordMode(), bundle_ids=[BundleID.WORD])
   ```

Nothing else changes.

---

## V2 backlog

- Word mode (all keyboard shortcuts — low complexity, just deprioritised)
- Photo Booth shutter (test the shortcut on the target Mac first)
- FaceTime live photo (likely needs PyObjC AX tree walking)
- Preferences window (per-mode remapping, saved to JSON)
- Long press support (hold A for 500ms → different action)
- LaunchAgent plist for proper launch-at-login without Terminal

---

## Architecture notes

**Why `subprocess osascript` instead of `NSAppleScript` via PyObjC?**
Simpler, more debuggable, and identical in effect. `osascript` is a stable
macOS CLI tool with no binding surprises.

**Why poll instead of NSWorkspace notifications for app detection?**
NSWorkspace notifications require the AppKit run loop. That loop is owned by
the rumps main thread. Polling from a separate daemon thread at 0.5 s
avoids any entanglement and is imperceptible to the user.

**Why pygame for gamepad input instead of PyObjC GameController?**
pygame's joystick API is simpler, better documented in Python, and handles
D mode HID devices reliably. The `SDL_VIDEODRIVER=dummy` trick prevents it
from needing a display.
