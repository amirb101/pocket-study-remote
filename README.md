# Pocket Study Remote

A context-aware macOS menu bar app that turns an **8BitDo Micro** gamepad into a personalised study and life remote. It auto-detects the frontmost app and switches button mappings accordingly.

## Modes

| Mode | Active when | Primary use |
|---|---|---|
| **Spotify** | Spotify is frontmost | Play/pause, next/prev, seek, volume, shuffle |
| **Browser** | Comet / Chrome / Arc / Edge is frontmost | Tab navigation, back/forward, new tab, bookmark combo |
| **Obsidian** | Obsidian is frontmost | Daily note, checklist, command palette, note history |
| **Global** | Anything else | Music controls, volume, screenshots, open apps |

A toast overlay appears for ~1.5 seconds whenever the mode changes.

---

## Requirements

- macOS 13 Ventura or later
- Xcode 15 or later (Swift 5.9)
- 8BitDo Micro with physical switch set to **D** (Direct Input mode)

---

## Build and run

1. Open `PocketStudyRemote.xcodeproj` in Xcode.
2. Select the **PocketStudyRemote** scheme and your Mac, then **⌘R**.
3. In **Signing & Capabilities**, choose your **Team** if automatic signing complains (or build with ad-hoc signing for local testing).
4. Ensure **App Sandbox** is off for this target (the project is configured with `ENABLE_APP_SANDBOX = NO`). Accessibility and `CGEventPost` require it.
5. On first run, grant **Accessibility** when prompted (System Settings → Privacy & Security → Accessibility).

**CLI: build + open in one step** (unsigned Debug build into `build/RunDerived`):

```bash
./scripts/run.sh
```

There is **no Dock icon** — look for the **game-controller** symbol in the **menu bar** (right). On a full menu bar, open the **«** overflow; hover until the tooltip **Pocket Study Remote** appears.

**Debug builds** use `Resources/Info-Debug.plist` (`LSUIElement = false`): you get a **Dock icon**, a **host window** shortly after launch, and `setActivationPolicy(.regular)`. The app decides this from the **embedded** `LSUIElement` value (not only the Swift `DEBUG` flag), so it matches what Xcode/`xcodebuild` actually bundled. If the window doesn’t appear, confirm the build log shows `ProcessInfoPlistFile … Info-Debug.plist` (not `Info.plist` alone). Running the executable from Terminal shows `PocketStudyRemote: showHostWindow …` on stderr when that code runs.

Raw `xcodebuild` only compiles; it does **not** launch the app unless you also `open …/PocketStudyRemote.app` or use the script above.

Command-line build only (unsigned, e.g. for CI):

```bash
xcodebuild -project PocketStudyRemote.xcodeproj -scheme PocketStudyRemote -configuration Debug -derivedDataPath build/RunDerived CODE_SIGNING_ALLOWED=NO build
```

Update `PRODUCT_BUNDLE_IDENTIFIER` in the target settings and `CFBundleIdentifier` in `Resources/Info.plist` before shipping.

---

## Repository

Upstream: [github.com/amirb101/pocket-study-remote](https://github.com/amirb101/pocket-study-remote)

To clone and build:

```bash
git clone https://github.com/amirb101/pocket-study-remote.git
cd pocket-study-remote
open PocketStudyRemote.xcodeproj
```

---

## Confirming Comet's Bundle ID

The app assumes `ai.perplexity.comet` for Comet browser. Confirm this on the target Mac:

```bash
mdls -name kMDItemCFBundleIdentifier /Applications/Comet.app
```

Update `Constants.BundleID.cometBrowser` in `Constants.swift` if it differs.

---

## Adding a New Mode

1. Create `Modes/WordMode.swift` (or whatever app you're targeting)
2. Make it conform to `AppMode`
3. Add its bundle ID to `Constants.BundleID`
4. Register it in `AppDelegate.buildRegistry()`:

```swift
registry.register(WordMode(), for: [Constants.BundleID.word])
```

That's it. No other files need to change.

---

## Obsidian Setup

Open Obsidian → Settings → Hotkeys, search for each command, and assign:

| Command | Shortcut |
|---|---|
| Open today's daily note | `Ctrl+Shift+D` |
| Toggle checklist status | `Ctrl+Shift+C` |
| Insert template | `Ctrl+Shift+T` |
| Open graph view | `Ctrl+Shift+G` |

The remaining shortcuts (Command palette, Quick switcher, Navigate back/forward, Toggle sidebar, Search) use Obsidian's defaults and need no changes.

---

## Controller Setup

1. Set the physical switch on the bottom of the 8BitDo Micro to **D**
2. Hold the pairing button until the lights flash
3. Open macOS System Settings → Bluetooth → pair the device
4. Open the app → grant Accessibility permission → done

---

## Project Structure

```
PocketStudyRemote/
├── AppDelegate.swift          — entry point, dependency wiring
├── Constants.swift            — all magic numbers and bundle IDs
├── Core/
│   ├── Action.swift           — Action value type and factory methods
│   ├── AppMode.swift          — AppMode protocol
│   ├── ButtonCombo.swift      — multi-button combo type
│   ├── GamepadButton.swift    — typed button enum
│   ├── KeyCode.swift          — typed CGKeyCode enum
│   ├── Logging.swift          — shared os.Logger instances
│   └── ModeRegistry.swift     — bundle ID → mode resolution
├── Controller/
│   └── ControllerManager.swift — GameController framework wrapper
├── Detection/
│   └── AppDetector.swift       — NSWorkspace frontmost app observer
├── Executors/
│   ├── AppleScriptExecutor.swift — async AppleScript runner + Spotify/System namespaces
│   └── KeystrokeExecutor.swift   — CGEventPost wrapper
├── Modes/
│   ├── BrowserMode.swift
│   ├── GlobalMode.swift
│   ├── ObsidianMode.swift
│   └── SpotifyMode.swift
├── Routing/
│   └── ActionRouter.swift     — button dispatch + combo detection + mode switching
├── UI/
│   ├── MenuBarController.swift — status item, menu, launch-at-login
│   └── OverlayWindow.swift    — animated mode-change toast
└── Resources/
    └── Info.plist
```

---

## V2 Backlog

- **Word mode** — Cmd+S, comment, undo/redo, track changes
- **Photo Booth mode** — capture shortcut (must test on target Mac)
- **FaceTime mode** — mute, full screen; Live Photo likely needs AX API tree walking
- **Preferences window** — drag-and-drop button remapping per mode
- **Long press** — hold A for 500ms → different action than tap
- **Import/export profiles** — share button maps as JSON

---

## Architecture Notes

**Why `Action` is a value type with a closure, not a protocol:**
Modes define tens of actions inline. A struct with a `perform: () -> Void` closure reads naturally as a dictionary literal and requires no boilerplate. Protocol conformance adds nothing here.

**Why `AppMode` *is* a protocol:**
Adding a new mode should require creating one new file and one new line in `AppDelegate`. A protocol makes that possible — anything that conforms is immediately usable by `ModeRegistry` and `ActionRouter` without changes to either.

**Why AppleScript runs on a serial background queue:**
AppleScript can block for 200–800ms. A serial queue (not concurrent) ensures volume-adjustment scripts don't pile up and overshoot — each one waits for the previous before running.

**Why `CGEventPost` rather than `AXUIElement` for keyboard shortcuts:**
`CGEventPost` is simpler, well-documented, and sufficient for everything in the current mode set. `AXUIElement` is reserved for cases where there is no keyboard shortcut equivalent (e.g. clicking a specific button in FaceTime's UI), which is a V2 concern.
