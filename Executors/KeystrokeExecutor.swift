import CoreGraphics
import os

/// Sends keyboard shortcuts to the currently active application via
/// the Core Graphics event system.
///
/// This is a pure namespace (caseless enum) — all methods are static.
/// It requires the Accessibility permission granted at first launch.
///
/// - Important: Events are posted to `.cghidEventTap`, which routes them
///   through the standard HID pipeline. The frontmost app receives them
///   exactly as if the user had pressed the keys on a physical keyboard.
enum KeystrokeExecutor {

    // MARK: - Core Send

    /// Posts a key-down followed by a key-up event for the given key and modifiers.
    ///
    /// - Parameters:
    ///   - key: The virtual key code to simulate.
    ///   - modifiers: Modifier keys to hold during the event (e.g. `.maskCommand`).
    static func send(key: KeyCode, modifiers: CGEventFlags = []) {
        guard let source = CGEventSource(stateID: .hidSystemState) else {
            Logger.actions.error("KeystrokeExecutor: failed to create CGEventSource")
            return
        }

        guard
            let keyDown = CGEvent(keyboardEventSource: source, virtualKey: key.rawValue, keyDown: true),
            let keyUp   = CGEvent(keyboardEventSource: source, virtualKey: key.rawValue, keyDown: false)
        else {
            Logger.actions.error("KeystrokeExecutor: failed to create CGEvent for key \(key.rawValue)")
            return
        }

        keyDown.flags = modifiers
        keyUp.flags   = modifiers

        keyDown.post(tap: .cghidEventTap)
        keyUp.post(tap: .cghidEventTap)

        Logger.actions.debug("Keystroke: \(key.rawValue) modifiers: \(modifiers.rawValue)")
    }

    // MARK: - Convenience Combinations

    /// Sends a shortcut with the Command modifier.
    static func command(_ key: KeyCode) {
        send(key: key, modifiers: .maskCommand)
    }

    /// Sends a shortcut with Command + Shift.
    static func commandShift(_ key: KeyCode) {
        send(key: key, modifiers: [.maskCommand, .maskShift])
    }

    /// Sends a shortcut with Command + Option.
    static func commandOption(_ key: KeyCode) {
        send(key: key, modifiers: [.maskCommand, .maskAlternate])
    }

    /// Sends a shortcut with Command + Option + Shift.
    static func commandOptionShift(_ key: KeyCode) {
        send(key: key, modifiers: [.maskCommand, .maskAlternate, .maskShift])
    }

    /// Sends a shortcut with Control.
    static func control(_ key: KeyCode) {
        send(key: key, modifiers: .maskControl)
    }

    /// Sends a shortcut with Control + Shift.
    static func controlShift(_ key: KeyCode) {
        send(key: key, modifiers: [.maskControl, .maskShift])
    }
}
