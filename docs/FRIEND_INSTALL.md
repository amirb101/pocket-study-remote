# Install ButtonBridge for someone else (macOS)

You (the developer) build **one** `ButtonBridge.app` on your Mac and send it to them (AirDrop, zip, Dropbox, etc.). They do **not** need Homebrew, git, or a Python course.

---

## What you do once

1. On your Mac, from the repo root:
   ```bash
   ./scripts/run.sh          # ensures .venv + deps exist
   ./scripts/build_mac_app.sh
   ```
2. You get `dist/ButtonBridge.app`.
3. **Zip** `ButtonBridge.app` (right-click → Compress) so macOS does not strip quarantine flags oddly in some hosts.
4. Send them the zip.

**Code signing:** the script produces an **unsigned** app. That is fine for family: the first open needs an extra click (below). For wider distribution you would use Apple Developer ID + notarization (more setup).

---

## What they do (her MacBook)

### 1. Unzip and move to Applications

- Unzip → drag **ButtonBridge.app** into **Applications**.

### 2. First open (Gatekeeper)

Because the app is not from the Mac App Store:

- **Do not** double-click the first time if macOS blocks it.
- Right-click **ButtonBridge** → **Open** → confirm **Open**.

(Alternatively: **System Settings → Privacy & Security** → scroll to the blocked message → **Open Anyway**.)

### 3. Accessibility (required)

The app simulates keyboard shortcuts, so macOS needs permission:

1. Open **ButtonBridge** once (menu bar icon should appear after a few seconds).
2. **System Settings → Privacy & Security → Accessibility**.
3. Turn **on** the toggle for **ButtonBridge** (add it with **+** if it is not listed: choose `Applications` → `ButtonBridge`).

If keys do nothing, repeat this step — the wrong app is almost always the problem.

### 4. Bluetooth controller

- **System Settings → Bluetooth** — pair the gamepad (same as you would for games).
- Optional: **System Settings → Game Controllers** — confirm the device appears.

### 5. Optional: change keybindings

On first launch, ButtonBridge may ask whether to open the keybinding editor. She can adjust mappings there, or use defaults and change later if you add a menu entry for it.

Config is stored under her home folder, typically:

`~/.buttonbridge/keybindings.json`

---

## If something goes wrong

| Symptom | What to try |
|---------|-------------|
| “App is damaged” / won’t open | Right-click → **Open**, or Privacy & Security → **Open Anyway**. Re-zip and resend if download was incomplete. |
| Menu bar icon missing | Look for a Python or **ButtonBridge** process in **Activity Monitor**; quit and reopen. |
| Controller never connects | Re-pair Bluetooth; try the controller’s **mode** switch (e.g. X / S); reboot once. |
| Keys do nothing | Accessibility toggle for **ButtonBridge**; make sure **ButtonBridge.app** is allowed, not only Terminal. |

---

## Easier than a `.app` (fallback)

If the build misbehaves on her machine, she can still run from source **if** she is comfortable installing Python 3.12 from [python.org](https://www.python.org/downloads/) and running `./scripts/run.sh` from a folder you send. The `.app` route above is the “no terminal” path.
