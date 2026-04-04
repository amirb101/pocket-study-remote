import AppKit
import ApplicationServices
import GameController
import ObjectiveC
import os

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
        // Release: accessory agent (no Dock). Debug: regular app — LSUIElement overridden in target Debug settings
        // so `NSAlert` / windows can appear; LSUIElement agent apps often never surface modals on screen.
        #if DEBUG
        if !NSApp.setActivationPolicy(.regular) {
            Logger.detection.error("setActivationPolicy(.regular) failed (Debug)")
        }
        #else
        if !NSApp.setActivationPolicy(.accessory) {
            Logger.detection.error("setActivationPolicy(.accessory) failed — menu bar item may be missing")
        }
        #endif

        requestAccessibilityPermissionIfNeeded()
        wireComponents()
        controllerManager.startDiscovery()
        appDetector.emitCurrentApp()

        // Lazily installs the status item now (after activation policy), and seeds UI if no delegate fired yet.
        menuBar.updateCurrentMode(router.currentMode)
        menuBar.updateConnectionState(isConnected: controllerManager.isConnected)

        Logger.detection.info("Pocket Study Remote launched")

        #if DEBUG
        // Order window on the next turn — same-tick ordering can leave a 0×0 layout or sit behind the AX prompt.
        DispatchQueue.main.async {
            NSApp.unhide(nil)
            NSApp.activate(ignoringOtherApps: true)
            DebugLaunchSupport.showHostWindow()
        }
        #endif
    }

    #if DEBUG
    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        if !flag {
            DebugLaunchSupport.showHostWindow()
        }
        return true
    }
    #endif

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

#if DEBUG

// LSUIElement / accessory apps often never show `NSAlert` or take focus — Debug target sets `LSUIElement=NO`
// and we use a real window + `.regular` activation so you can always see something.

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
        if let w = window {
            NSApp.unhide(nil)
            NSApp.activate(ignoringOtherApps: true)
            w.makeKeyAndOrderFront(nil)
            w.orderFrontRegardless()
            return
        }

        let w = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 560, height: 280),
            styleMask: [.titled, .closable, .miniaturizable, .resizable],
            backing: .buffered,
            defer: false
        )
        w.title = "Pocket Study Remote (Debug)"
        w.isReleasedWhenClosed = false
        // Above normal floating windows so it isn’t lost behind other apps.
        w.level = .modalPanel
        w.collectionBehavior = [.moveToActiveSpace, .fullScreenAuxiliary]
        w.isOpaque = true
        w.backgroundColor = .windowBackgroundColor
        w.minSize = NSSize(width: 440, height: 220)

        let label = NSTextField(wrappingLabelWithString: """
        Debug build — this window and a Dock icon are intentional. Release builds stay menu-bar-only (no Dock).

        The controller UI is still the game-controller item in the menu bar (try « overflow). Tooltip: “Pocket Study Remote”.
        """)
        label.font = .systemFont(ofSize: 13)
        label.maximumNumberOfLines = 0
        label.preferredMaxLayoutWidth = 500

        let quitBtn = NSButton(title: "Quit", target: NSApp, action: #selector(NSApplication.terminate(_:)))
        quitBtn.keyEquivalent = "q"
        quitBtn.keyEquivalentModifierMask = .command

        let stack = NSStackView(views: [label, quitBtn])
        stack.orientation = .vertical
        stack.alignment = .leading
        stack.spacing = 16
        stack.edgeInsets = NSEdgeInsets(top: 20, left: 20, bottom: 20, right: 20)
        stack.translatesAutoresizingMaskIntoConstraints = true
        stack.autoresizingMask = [.width, .height]

        let container = NSView(frame: NSRect(x: 0, y: 0, width: 560, height: 280))
        stack.frame = container.bounds
        container.addSubview(stack)

        w.contentView = container
        w.setContentSize(NSSize(width: 560, height: 300))
        w.center()

        let del = DebugHostWindowDelegate {
            DebugLaunchSupport.window = nil
            DebugLaunchSupport.delegateRetain = nil
        }
        w.delegate = del
        delegateRetain = del
        window = w

        container.layoutSubtreeIfNeeded()

        NSApp.unhide(nil)
        NSApp.activate(ignoringOtherApps: true)
        w.makeKeyAndOrderFront(nil)
        w.orderFrontRegardless()
    }
}

#endif

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
