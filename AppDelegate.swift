import AppKit
import ApplicationServices
import GameController
import ObjectiveC
import os

// MARK: - Bundle (Debug vs Release packaging)

private extension Bundle {

    /// `Resources/Info.plist` sets `LSUIElement = true` (menu-bar-only). `Info-Debug.plist` sets `false` (Dock + windows).
    /// Do not rely on Swift `-DDEBUG` alone — match what was actually embedded in the app bundle.
    var psr_isMenuBarAgentOnly: Bool {
        guard let v = object(forInfoDictionaryKey: "LSUIElement") else { return false }
        if let b = v as? Bool { return b }
        if let n = v as? NSNumber { return n.boolValue }
        return false
    }
}

/// Entry point and dependency wiring.
///
/// `AppDelegate` is intentionally thin — it creates every component,
/// connects them together, and then gets out of the way. All real logic
/// lives in the dedicated classes below it.
///
/// ## Component graph
///
/// ```
/// AppDelegate
/// ├── ModeRegistry        ← knows which bundle ID maps to which mode
/// ├── ActionRouter        ← resolves button → action, handles combos
/// │   ├── (delegate of) ControllerManager   ← reads gamepad input
/// │   └── (delegate of) AppDetector         ← watches frontmost app
/// ├── OverlayWindow       ← toast shown on mode change
/// └── MenuBarController   ← status item and menu
/// ```
@main
@MainActor
final class AppDelegate: NSObject, NSApplicationDelegate {

    // MARK: - Components

    private let registry: ModeRegistry
    private let overlay = OverlayWindow()
    /// Created on first use — must be after `NSApp.setActivationPolicy` (see `applicationDidFinishLaunching`).
    private lazy var menuBar = MenuBarController()
    private let controllerManager = ControllerManager()
    private let appDetector = AppDetector()
    private let router: ActionRouter

    override init() {
        let registry = AppDelegate.buildRegistry()
        self.registry = registry
        self.router = ActionRouter(registry: registry)
        super.init()
    }

    // MARK: - Application Lifecycle

    func applicationDidFinishLaunching(_ notification: Notification) {
        if Bundle.main.psr_isMenuBarAgentOnly {
            if !NSApp.setActivationPolicy(.accessory) {
                Logger.detection.error("setActivationPolicy(.accessory) failed — menu bar item may be missing")
            }
        } else {
            if !NSApp.setActivationPolicy(.regular) {
                Logger.detection.error("setActivationPolicy(.regular) failed — Debug plist expects a normal app")
            }
        }

        requestAccessibilityPermissionIfNeeded()
        wireComponents()
        controllerManager.startDiscovery()
        appDetector.emitCurrentApp()

        // Lazily installs the status item now (after activation policy), and seeds UI if no delegate fired yet.
        menuBar.updateCurrentMode(router.currentMode)
        menuBar.updateConnectionState(isConnected: controllerManager.isConnected)

        Logger.detection.info("Pocket Study Remote launched")

        if !Bundle.main.psr_isMenuBarAgentOnly {
            // After AX sheet / layout; `hasVisibleWindows` on Dock click is often wrong — reopen always calls `showHostWindow` too.
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) {
                NSApp.unhide(nil)
                NSApp.activate(ignoringOtherApps: true)
                DebugLaunchSupport.showHostWindow()
            }
        }
    }

    /// Bring back the host window whenever the Dock icon is clicked (Debug / non–LSUIElement builds only).
    @objc func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        if !Bundle.main.psr_isMenuBarAgentOnly {
            DebugLaunchSupport.showHostWindow()
        }
        return true
    }

    func applicationWillTerminate(_ notification: Notification) {
        GCController.stopWirelessControllerDiscovery()
    }

    // MARK: - Wiring

    private func wireComponents() {
        // Router receives button events from the controller
        controllerManager.delegate = router

        // Router receives app-change events from the detector
        appDetector.delegate = router

        // Router notifies the overlay and menu bar on mode change
        router.onModeChanged = { [weak self] mode in
            self?.overlay.show(mode: mode)
            self?.menuBar.updateCurrentMode(mode)
        }

        // Menu bar reflects controller connection state
        // Implemented via a small extension on ControllerManager below.
        controllerManager.onConnectionChange = { [weak self] isConnected in
            self?.menuBar.updateConnectionState(isConnected: isConnected)
        }
    }

    // MARK: - Permissions

    private func requestAccessibilityPermissionIfNeeded() {
        guard !AXIsProcessTrusted() else { return }
        let options: NSDictionary = [kAXTrustedCheckOptionPrompt: true]
        AXIsProcessTrustedWithOptions(options)
    }

    // MARK: - Mode Registry

    /// Builds and populates the mode registry.
    ///
    /// **To add a new mode:**
    /// 1. Create a new `AppMode`-conforming struct in `Modes/`.
    /// 2. Add its bundle ID(s) to `Constants.BundleID`.
    /// 3. Register it here with one line.
    private static func buildRegistry() -> ModeRegistry {
        let registry = ModeRegistry(fallback: GlobalMode())

        registry.register(SpotifyMode(), for: [
            Constants.BundleID.spotify,
        ])

        registry.register(BrowserMode(), for:
            Constants.BundleID.chromiumBrowsers
        )

        registry.register(ObsidianMode(), for: [
            Constants.BundleID.obsidian,
        ])

        return registry
    }
}

private final class DebugHostWindowDelegate: NSObject, NSWindowDelegate {
    let onClosed: () -> Void

    init(onClosed: @escaping () -> Void) {
        self.onClosed = onClosed
    }

    func windowWillClose(_ notification: Notification) {
        onClosed()
    }
}

@MainActor
private enum DebugLaunchSupport {
    private static var window: NSWindow?
    private static var delegateRetain: DebugHostWindowDelegate?

    static func showHostWindow() {
        fputs("PocketStudyRemote: showHostWindow (LSUIElement=\(Bundle.main.psr_isMenuBarAgentOnly))\n", stderr)

        if let w = window {
            NSApp.unhide(nil)
            NSApp.activate(ignoringOtherApps: true)
            positionWindowOnMainScreen(w)
            w.makeKeyAndOrderFront(nil)
            w.orderFrontRegardless()
            return
        }

        let w = KeyableHostWindow(
            contentRect: NSRect(x: 0, y: 0, width: 560, height: 320),
            styleMask: [.titled, .closable, .miniaturizable, .resizable],
            backing: .buffered,
            defer: false
        )
        w.title = "Pocket Study Remote (Debug)"
        w.isReleasedWhenClosed = false
        w.level = .normal
        w.collectionBehavior = [.moveToActiveSpace]
        w.isOpaque = true
        w.backgroundColor = .windowBackgroundColor
        w.minSize = NSSize(width: 440, height: 240)

        let container = FlippedOriginView(frame: NSRect(x: 0, y: 0, width: 560, height: 300))

        let label = NSTextField(wrappingLabelWithString: """
        Debug / non–LSUIElement build — Dock icon and this window are expected. Release will be menu-bar-only.

        Main controller UI: game-controller icon in the menu bar (« overflow if needed). Tooltip: “Pocket Study Remote”.
        """)
        label.font = .systemFont(ofSize: 13)
        label.frame = NSRect(x: 20, y: 20, width: 520, height: 220)
        label.autoresizingMask = [.width, .minYMargin]
        container.addSubview(label)

        let quitBtn = NSButton(title: "Quit", target: NSApp, action: #selector(NSApplication.terminate(_:)))
        quitBtn.keyEquivalent = "q"
        quitBtn.keyEquivalentModifierMask = .command
        quitBtn.frame = NSRect(x: 20, y: 250, width: 120, height: 32)
        quitBtn.autoresizingMask = [.minYMargin]
        container.addSubview(quitBtn)

        w.contentView = container
        w.setContentSize(NSSize(width: 560, height: 320))
        positionWindowOnMainScreen(w)

        let del = DebugHostWindowDelegate {
            DebugLaunchSupport.window = nil
            DebugLaunchSupport.delegateRetain = nil
        }
        w.delegate = del
        delegateRetain = del
        window = w

        NSApp.unhide(nil)
        NSApp.activate(ignoringOtherApps: true)
        w.makeKeyAndOrderFront(nil)
        w.orderFrontRegardless()
    }

    private static func positionWindowOnMainScreen(_ w: NSWindow) {
        guard let screen = NSScreen.main else {
            w.center()
            return
        }
        let sf = screen.visibleFrame
        var frame = w.frame
        frame.origin.x = sf.midX - frame.width * 0.5
        frame.origin.y = sf.midY - frame.height * 0.5
        w.setFrame(frame, display: true)
    }
}

/// AppKit default origin is bottom-left; simple top-down placement for subviews.
private final class FlippedOriginView: NSView {
    override var isFlipped: Bool { true }
}

/// Some window server paths won’t surface a normal `NSWindow` as key; this matches panel behaviour.
private final class KeyableHostWindow: NSWindow {
    override var canBecomeKey: Bool { true }
    override var canBecomeMain: Bool { true }
}

// MARK: - ControllerManager Connection Callback

/// Adds a simple closure-based connection callback to `ControllerManager`
/// so `AppDelegate` can avoid making the menu bar a delegate of the controller.
extension ControllerManager {

    /// Called on the main thread when the controller connects or disconnects.
    var onConnectionChange: ((Bool) -> Void)? {
        get { objc_getAssociatedObject(self, &connectionChangeKey) as? (Bool) -> Void }
        set { objc_setAssociatedObject(self, &connectionChangeKey, newValue, .OBJC_ASSOCIATION_RETAIN_NONATOMIC) }
    }
}

private var connectionChangeKey = "connectionChangeKey"
