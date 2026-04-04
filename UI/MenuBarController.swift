import AppKit
import ServiceManagement
import os

/// Owns the menu bar status item and all menu interactions.
///
/// The status item shows a controller icon. Clicking it opens a menu with:
/// - Current mode name
/// - Controller connection state
/// - Launch at login toggle
/// - Quit
///
/// `MenuBarController` has no knowledge of how modes work — it just displays
/// state that `AppDelegate` pushes into it via the two `update*` methods.
final class MenuBarController {

    // MARK: - Private State

    private let statusItem: NSStatusItem
    private var currentModeName: String = "—"
    private var isControllerConnected: Bool = false

    // MARK: - Initialisation

    init() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
        configureButton()
    }

    // MARK: - Public Updates

    /// Reflects the current mode name in the menu.
    func updateCurrentMode(_ mode: any AppMode) {
        currentModeName = mode.displayName
        // Rebuild the menu so the displayed name is always current.
        // Menus are rebuilt on click anyway, but eager updates feel snappier.
        rebuildMenu()
    }

    /// Reflects the controller connection state in the menu.
    func updateConnectionState(isConnected: Bool) {
        isControllerConnected = isConnected
        rebuildMenu()

        // Update the button icon to hint at disconnection.
        DispatchQueue.main.async { [weak self] in
            self?.configureButton()
        }
    }

    // MARK: - Private: Setup

    private func configureButton() {
        guard let button = statusItem.button else { return }
        let symbolName = isControllerConnected ? "gamecontroller.fill" : "gamecontroller"
        button.image = NSImage(
            systemSymbolName: symbolName,
            accessibilityDescription: "Pocket Study Remote"
        )
        button.image?.isTemplate = true  // renders correctly in both light and dark menu bars
        button.action = #selector(statusItemClicked)
        button.target = self
    }

    @objc private func statusItemClicked() {
        rebuildMenu()
        statusItem.popUpMenu(buildMenu())
    }

    // MARK: - Private: Menu Building

    private func rebuildMenu() {
        statusItem.menu = buildMenu()
    }

    private func buildMenu() -> NSMenu {
        let menu = NSMenu()

        // ── App name header ───────────────────────────────────────────────

        let titleItem = NSMenuItem(title: "Pocket Study Remote", action: nil, keyEquivalent: "")
        titleItem.isEnabled = false
        menu.addItem(titleItem)

        menu.addItem(.separator())

        // ── Status ────────────────────────────────────────────────────────

        let modeItem = NSMenuItem(
            title: "Mode: \(currentModeName)",
            action: nil,
            keyEquivalent: ""
        )
        modeItem.isEnabled = false
        menu.addItem(modeItem)

        let connectionLabel = isControllerConnected ? "Controller: Connected ✓" : "Controller: Not Connected"
        let connectionItem = NSMenuItem(title: connectionLabel, action: nil, keyEquivalent: "")
        connectionItem.isEnabled = false
        menu.addItem(connectionItem)

        menu.addItem(.separator())

        // ── Accessibility warning (shown only when permission is missing) ──

        if !AccessibilityPermission.isGranted {
            let warningItem = NSMenuItem(
                title: "⚠️ Accessibility Permission Needed",
                action: #selector(openAccessibilitySettings),
                keyEquivalent: ""
            )
            warningItem.target = self
            menu.addItem(warningItem)
            menu.addItem(.separator())
        }

        // ── Preferences ───────────────────────────────────────────────────

        let launchAtLoginItem = NSMenuItem(
            title: "Launch at Login",
            action: #selector(toggleLaunchAtLogin),
            keyEquivalent: ""
        )
        launchAtLoginItem.target = self
        launchAtLoginItem.state = LaunchAtLoginManager.isEnabled ? .on : .off
        menu.addItem(launchAtLoginItem)

        menu.addItem(.separator())

        // ── Quit ─────────────────────────────────────────────────────────

        let quitItem = NSMenuItem(
            title: "Quit Pocket Study Remote",
            action: #selector(NSApplication.terminate(_:)),
            keyEquivalent: "q"
        )
        menu.addItem(quitItem)

        return menu
    }

    // MARK: - Actions

    @objc private func toggleLaunchAtLogin() {
        LaunchAtLoginManager.toggle()
        rebuildMenu()
    }

    @objc private func openAccessibilitySettings() {
        AccessibilityPermission.openSystemSettings()
    }
}

// MARK: - Accessibility Permission Helpers

/// Thin wrapper around the Accessibility API trust check.
private enum AccessibilityPermission {

    static var isGranted: Bool {
        AXIsProcessTrusted()
    }

    /// Prompts the user for Accessibility permission if not already granted.
    static func requestIfNeeded() {
        let options: NSDictionary = [kAXTrustedCheckOptionPrompt: true]
        AXIsProcessTrustedWithOptions(options)
    }

    static func openSystemSettings() {
        let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility")!
        NSWorkspace.shared.open(url)
    }
}

// MARK: - Launch at Login Helpers

/// Manages the "Launch at Login" state using `SMAppService` (macOS 13+).
private enum LaunchAtLoginManager {

    static var isEnabled: Bool {
        SMAppService.mainApp.status == .enabled
    }

    static func toggle() {
        do {
            if isEnabled {
                try SMAppService.mainApp.unregister()
            } else {
                try SMAppService.mainApp.register()
            }
        } catch {
            Logger.detection.error("Launch at login toggle failed: \(error)")
        }
    }
}
