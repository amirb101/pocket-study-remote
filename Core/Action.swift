import AppKit
import CoreGraphics
import os

/// A single thing the controller can do when a button is pressed.
///
/// `Action` is a simple value type that wraps a closure. All the complexity
/// of *how* to do something lives in the executor layer (`KeystrokeExecutor`,
/// `AppleScriptExecutor`). Modes just declare *what* they want, using the
/// static factory methods below.
///
/// The `id` field is stable across launches and is used for persisting custom
/// button mappings to disk. The `displayName` is shown in the preferences UI.
struct Action {

    /// A stable, URL-safe identifier. Use kebab-case (e.g. `"spotify-next-track"`).
    let id: String

    /// A human-readable description shown in the preferences window.
    let displayName: String

    /// The work to perform. Threading is the factory method's responsibility:
    /// keystroke actions fire synchronously, AppleScript actions dispatch async.
    let perform: () -> Void
}

// MARK: - Factory Methods

extension Action {

    /// Sends a keyboard shortcut to the currently active application.
    ///
    /// This fires instantly and requires the Accessibility permission granted
    /// at first launch.
    static func keystroke(
        _ key: KeyCode,
        modifiers: CGEventFlags = [],
        id: String,
        name: String
    ) -> Action {
        Action(id: id, displayName: name) {
            KeystrokeExecutor.send(key: key, modifiers: modifiers)
        }
    }

    /// Runs an AppleScript source string on a background queue.
    ///
    /// AppleScript execution can block for several hundred milliseconds, so it
    /// is always dispatched off the main thread to keep the UI responsive.
    static func appleScript(
        _ source: String,
        id: String,
        name: String
    ) -> Action {
        Action(id: id, displayName: name) {
            AppleScriptExecutor.run(source)
        }
    }

    /// Brings an application to the front, launching it if it isn't running.
    static func openApp(
        bundleIdentifier: String,
        id: String,
        name: String
    ) -> Action {
        Action(id: id, displayName: name) {
            guard let url = NSWorkspace.shared.urlForApplication(
                withBundleIdentifier: bundleIdentifier
            ) else {
                Logger.actions.error("Cannot find application '\(bundleIdentifier)'")
                return
            }
            let config = NSWorkspace.OpenConfiguration()
            config.activates = true
            NSWorkspace.shared.openApplication(
                at: url,
                configuration: config,
                completionHandler: nil
            )
        }
    }

    /// Changes the system output volume by a relative number of points (0–100 scale).
    ///
    /// Positive values raise the volume; negative values lower it.
    /// Clamped to [0, 100] by the system.
    static func adjustVolume(
        by delta: Int,
        id: String,
        name: String
    ) -> Action {
        Action(id: id, displayName: name) {
            // AppleScript is used here because there is no clean public API
            // for system volume adjustment without private frameworks.
            AppleScriptExecutor.run("""
                set currentVolume to output volume of (get volume settings)
                set volume output volume (currentVolume + \(delta))
            """)
        }
    }

    /// Toggles the system mute state.
    static func toggleMute(id: String, name: String) -> Action {
        Action(id: id, displayName: name) {
            AppleScriptExecutor.run("""
                set isMuted to output muted of (get volume settings)
                set volume output muted (not isMuted)
            """)
        }
    }

    /// Sends a macOS screenshot command.
    static func screenshot(region: Bool, id: String, name: String) -> Action {
        // Cmd+Shift+4 = region select; Cmd+Shift+3 = full screen
        let key: KeyCode = region ? .four : .three
        return keystroke(
            key,
            modifiers: [.maskCommand, .maskShift],
            id: id,
            name: name
        )
    }

    /// Switches to the previous macOS Space (virtual desktop).
    static func switchSpace(direction: HorizontalDirection, id: String, name: String) -> Action {
        let key: KeyCode = direction == .left ? .leftArrow : .rightArrow
        return keystroke(key, modifiers: .maskControl, id: id, name: name)
    }

    /// A no-op placeholder for unassigned buttons.
    ///
    /// Useful during development and as a default for new buttons added in
    /// future controller hardware revisions.
    static func unassigned(button: GamepadButton) -> Action {
        Action(id: "unassigned-\(button.rawValue.lowercased())", displayName: "Unassigned") {}
    }

    // MARK: - Helpers

    enum HorizontalDirection {
        case left, right
    }
}

// MARK: - KeyCode Extension for Screenshot

private extension KeyCode {
    static let three: KeyCode = .ansi3
    static let four: KeyCode = .ansi4
}
