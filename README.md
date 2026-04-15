# ButtonBridge

A context-aware macOS menu bar app that maps a Bluetooth gamepad (for example an **8BitDo Micro**) to keyboard shortcuts and system actions. It detects the **frontmost application** and switches controller mappings automatically.

There is **no main document window** — only the menu bar icon (and a Dock tile while you run it from Terminal). Background work starts at launch; you do not need to click anything to “start” the app.

**Repository:** https://github.com/amirb101/buttonbridge

---

## Pre-built app (no Python required)

Build a drag-and-drop **`.app`** on your Mac, zip it, and share it. Recipients install it like any small utility: Applications folder, Accessibility, Bluetooth.

- **Beginner-oriented steps (developer + recipient):** [docs/beginner-installation-guide.md](docs/beginner-installation-guide.md)
- **Build command:** `./scripts/build_mac_app.sh` → `dist/ButtonBridge.app` ([PyInstaller](https://pyinstaller.org); version pinned in `requirements-build.txt`)

The first PyInstaller build is the most sensitive to environment (PyObjC + GameController). If the `.app` misbehaves on another Mac, the same guide includes a **fallback** (run from source with `./scripts/run.sh`).

---

## How modes work

1. **App detection** periodically reads the active app’s bundle identifier.
2. **Mode registry** (`buttonbridge/main.py`) maps that bundle ID to a mode class (Spotify, Browser, Global, …).
3. If nothing matches, **Global** mode is used as the fallback.
4. Each mode exposes a list of **actions** (play/pause, new tab, …). Your **keybindings** map physical buttons → action IDs. Edit mappings from the menu bar (keybinding editor subprocess).

Bundle IDs live in `buttonbridge/constants.py`. If a mode never activates for an app you care about, add or correct the bundle ID and register it in `_build_registry()`.

---

## Mode reference (all built-in modes)

Summary: which app(s) activate each mode. Exact bundle strings are in `constants.py` → `BundleID`.

| Mode | `id` | Activated when frontmost app is |
|------|------|----------------------------------|
| **Global** | `global` | Fallback — any app not matched below |
| **Browser** | `browser` | Chrome, Safari, Arc, Edge, Brave, Firefox (incl. Nightly), Opera, Vivaldi, Orion, Zen, Comet |
| **Spotify** | `spotify` | Spotify |
| **Apple Music** | `apple_music` | Apple Music |
| **Anki** | `anki` | Anki |
| **Obsidian** | `obsidian` | Obsidian |
| **Notion** | `notion` | Notion |
| **Finder** | `finder` | Finder |
| **Preview** | `preview` | Preview |
| **VS Code** | `vscode` | Visual Studio Code or Cursor |
| **Messages** | `messages` | Messages |
| **WhatsApp** | `whatsapp` | WhatsApp |
| **FaceTime** | `facetime` | FaceTime |
| **Phone** | `phone` | Phone (`com.apple.mobilephone` — verify on your OS if the app does not switch mode) |

### Global (`global`)

System-wide shortcuts and utilities (many use AppleScript or small helpers, not only raw keys):

- Play / Pause, Next track, Previous track (Spotify via AppleScript)
- Volume up / down, Toggle mute
- Screenshot (region), Screenshot (full screen)
- Mission Control, Spotlight, Lock screen
- Open Obsidian, Open Spotify
- Switch space left / right

### Browser (`browser`)

Standard macOS browser shortcuts (same idea across the browsers in the table above):

- New tab, Close tab, Reopen closed tab, New window
- Page back / forward, Previous / next tab
- Scroll up / down (Page Up / Page Down)
- Tab search, Focus address bar, Bookmark page

### Spotify (`spotify`)

- Play/pause, Next / previous track
- Volume up / down (in-app)
- Shuffle, Repeat, Like/unlike, Search

### Apple Music (`apple_music`)

- Play/pause, Next / previous track
- Volume up / down, Love track, Shuffle, Search

### Anki (`anki`)

- Show answer (`Space`)
- Rate card: Again (`1`), Hard (`2`), Good (`3`), Easy (`4`)
- Undo, Bury card, Suspend card

### Obsidian (`obsidian`)

Uses Obsidian’s default shortcuts where noted, plus **custom chords** you should bind in Obsidian → **Settings → Hotkeys** to match:

| Action in ButtonBridge | Suggested Obsidian hotkey |
|------------------------|-------------------------|
| Today’s daily note | `Ctrl+Shift+D` |
| Toggle checklist | `Ctrl+Shift+C` |
| Insert template | `Ctrl+Shift+T` |
| Graph view | `Ctrl+Shift+G` |

Also includes: Command palette, Quick switcher, Navigate back/forward, Toggle sidebar, Search all files, New note, Search current file — align or remap in the keybinding GUI if your vault differs.

### Notion (`notion`)

- Quick find, New page, Toggle todo, Slash command
- Go back / forward, Command palette

### Finder (`finder`)

- New folder, Quick Look, Get Info, Search
- Go back / forward, Move to Trash

### Preview (`preview`)

- Next / previous page, Zoom in / out, Actual size
- Share, Rotate left / right

### VS Code (`vscode`)

Active for **VS Code** and **Cursor**:

- Command palette, Quick open, Toggle terminal
- Go to definition, Find, Save, New file, Close tab

### Messages (`messages`)

- New message, Send
- Next / previous conversation, Search, Chat info

### WhatsApp (`whatsapp`)

- New chat, Send, Search, Search in chat
- Archive chat, Mute chat

### FaceTime (`facetime`)

- Answer / decline / end call
- Toggle mute, Toggle camera, Flip camera
- Video effects, Full screen

### Phone (`phone`)

- Answer / decline / end call
- Toggle mute
- Keypad, Contacts, Recents, Voicemail

If Phone mode does not trigger, run:

```bash
mdls -name kMDItemCFBundleIdentifier /System/Applications/Phone.app
# or: /Applications/Phone.app
```

and update `BundleID.PHONE` in `constants.py` to match your Mac.

---

## Keybindings and config

- **Editor:** launched from the menu bar (separate process so Tkinter stays on its own main thread).
- **Storage:** `~/.buttonbridge/keybindings.json` (path may vary slightly by version — check `buttonbridge/config/keybind_config.py` for `CONFIG_FILE`).
- **Per mode:** each tab lists that mode’s **actions**; you assign **gamepad buttons** (and optional combo behaviour where supported).
- Unmapped actions simply do nothing until you assign them.

Defaults are recreated when you reset; merge behaviour for old JSON files is defined in code.

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
├── modes/              # One module per app mode (see table above)
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
