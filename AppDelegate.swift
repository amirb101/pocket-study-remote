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
    private let menuBar = MenuBarController()
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
        requestAccessibilityPermissionIfNeeded()
        wireComponents()
        controllerManager.startDiscovery()
        appDetector.emitCurrentApp()

        Logger.detection.info("Pocket Study Remote launched")
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
