import AppKit
import os

/// Observes `NSWorkspace` to track which application is currently in the
/// foreground, and notifies a delegate whenever that changes.
///
/// `AppDetector` is the single point of truth for "what app is the user
/// looking at right now?" All mode-switching logic lives in `ActionRouter`,
/// which subscribes to detector events via the delegate.
final class AppDetector {

    // MARK: - Delegate

    weak var delegate: AppDetectorDelegate?

    // MARK: - State

    /// The bundle identifier of the currently active application, or `nil`
    /// if it cannot be determined (e.g. the Finder desktop is focused).
    private(set) var currentBundleIdentifier: String?

    // MARK: - Initialisation

    init() {
        observeWorkspaceNotifications()
    }

    // MARK: - Startup

    /// Fires an initial delegate call for whatever app is already in the
    /// foreground when the app launches.
    ///
    /// Call this after the delegate is set, from `AppDelegate.applicationDidFinishLaunching`.
    func emitCurrentApp() {
        let bundleID = NSWorkspace.shared.frontmostApplication?.bundleIdentifier
        update(bundleIdentifier: bundleID)
    }

    // MARK: - Private

    private func observeWorkspaceNotifications() {
        NSWorkspace.shared.notificationCenter.addObserver(
            self,
            selector: #selector(activeAppDidChange(_:)),
            name: NSWorkspace.didActivateApplicationNotification,
            object: nil
        )
    }

    @objc private func activeAppDidChange(_ notification: Notification) {
        let app = notification.userInfo?[NSWorkspace.applicationUserInfoKey]
            as? NSRunningApplication
        update(bundleIdentifier: app?.bundleIdentifier)
    }

    private func update(bundleIdentifier: String?) {
        guard bundleIdentifier != currentBundleIdentifier else { return }
        currentBundleIdentifier = bundleIdentifier

        Logger.detection.debug("Active app changed to: \(bundleIdentifier ?? "nil")")

        // NSWorkspace notifications already arrive on the main thread.
        delegate?.appDetector(self, didDetectBundleIdentifier: bundleIdentifier)
    }
}

// MARK: - Delegate Protocol

/// Receives app-change events on the main thread.
protocol AppDetectorDelegate: AnyObject {

    /// Called whenever the frontmost application changes.
    ///
    /// - Parameters:
    ///   - detector: The detector that produced the event.
    ///   - bundleIdentifier: The bundle ID of the newly active app, or `nil`.
    func appDetector(_ detector: AppDetector, didDetectBundleIdentifier bundleIdentifier: String?)
}
