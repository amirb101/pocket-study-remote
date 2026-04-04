import Foundation
import os

/// Shared `Logger` instances, one per subsystem category.
///
/// Usage:
/// ```swift
/// Logger.controller.info("Controller connected: \(name)")
/// Logger.actions.debug("Firing action: '\(id)'")
/// Logger.detection.warning("Unknown bundle ID: \(bundleID)")
/// ```
///
/// Logs are viewable in Console.app by filtering on the subsystem
/// `com.pocketstudyremote` or the individual category names.
extension Logger {

    private static let subsystem = Bundle.main.bundleIdentifier ?? "com.pocketstudyremote"

    /// Events from `ControllerManager` — connection, disconnection, button presses.
    static let controller = Logger(subsystem: subsystem, category: "Controller")

    /// Events from `AppDetector` and `ActionRouter` — app switches, mode changes.
    static let detection  = Logger(subsystem: subsystem, category: "Detection")

    /// Events from `ActionRouter`, `KeystrokeExecutor`, `AppleScriptExecutor`.
    static let actions    = Logger(subsystem: subsystem, category: "Actions")
}
