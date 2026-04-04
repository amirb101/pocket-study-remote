import Foundation
import os

/// The central coordinator between controller input and mode-specific actions.
///
/// `ActionRouter` sits between `ControllerManager` (raw button events) and
/// the `AppMode` conformers (button → action maps). Its responsibilities are:
///
/// 1. **Mode tracking** — updates the active mode when the frontmost app changes.
/// 2. **Combo detection** — checks for multi-button combos before single-button actions.
/// 3. **Action dispatch** — calls `action.perform()` for the resolved action.
///
/// All methods run on the main thread (enforced by `@MainActor`).
@MainActor
final class ActionRouter {

    // MARK: - Callbacks

    /// Called whenever the active mode changes. Use this to update the overlay
    /// and menu bar. Fires on the main thread.
    var onModeChanged: ((any AppMode) -> Void)?

    // MARK: - State

    /// The currently active mode. Changes when the frontmost app changes.
    private(set) var currentMode: any AppMode

    /// The set of buttons currently held down. Used for combo detection.
    private var heldButtons: Set<GamepadButton> = []

    // MARK: - Dependencies

    private let registry: ModeRegistry

    // MARK: - Initialisation

    init(registry: ModeRegistry) {
        self.registry   = registry
        self.currentMode = registry.fallback
    }

    // MARK: - Mode Switching

    /// Updates the active mode based on the given bundle identifier.
    ///
    /// If the new mode has the same `id` as the current mode, this is a no-op
    /// (no unnecessary overlay toasts or UI refreshes).
    func updateMode(for bundleIdentifier: String?) {
        let newMode = registry.mode(for: bundleIdentifier)
        guard newMode.id != currentMode.id else { return }

        Logger.actions.info("Mode changed: '\(self.currentMode.id)' → '\(newMode.id)'")
        currentMode = newMode
        onModeChanged?(newMode)
    }

    // MARK: - Button Dispatch

    /// Called by `ControllerManager` (via `AppDelegate`) when any button changes state.
    func buttonChanged(_ button: GamepadButton, isPressed: Bool) {
        if isPressed {
            heldButtons.insert(button)
            dispatch(pressed: button)
        } else {
            heldButtons.remove(button)
        }
    }

    // MARK: - Private: Dispatch Logic

    private func dispatch(pressed button: GamepadButton) {
        // 1. Check combos first. A combo fires only when the newly pressed
        //    button completes the set — all other buttons in the combo must
        //    already be held. Combos take priority over single-button actions.
        if let comboAction = resolveCombo(completedBy: button) {
            Logger.actions.debug("Firing combo action: '\(comboAction.id)'")
            comboAction.perform()
            return
        }

        // 2. Fall through to single-button action for this mode.
        if let action = currentMode.buttonMap[button] {
            Logger.actions.debug("Firing action: '\(action.id)' for button: '\(button.rawValue)'")
            action.perform()
        }
    }

    /// Returns the first combo in the current mode whose complete button set
    /// is satisfied by the current `heldButtons` state — or `nil` if none match.
    private func resolveCombo(completedBy triggerButton: GamepadButton) -> Action? {
        currentMode.comboMap.first { combo, _ in
            // The newly pressed button must be part of this combo...
            combo.buttons.contains(triggerButton) &&
            // ...and every button in the combo must now be held.
            combo.matches(heldButtons: heldButtons)
        }?.value
    }
}

// MARK: - ControllerManagerDelegate Conformance

extension ActionRouter: ControllerManagerDelegate {

    nonisolated func controllerDidConnect() {
        // Nothing to do — MenuBarController observes the connection state separately.
    }

    nonisolated func controllerDidDisconnect() {
        Task { @MainActor in
            heldButtons.removeAll()
        }
    }

    nonisolated func controllerButton(_ button: GamepadButton, didChange isPressed: Bool) {
        Task { @MainActor in
            buttonChanged(button, isPressed: isPressed)
        }
    }
}

// MARK: - AppDetectorDelegate Conformance

extension ActionRouter: AppDetectorDelegate {

    nonisolated func appDetector(_ detector: AppDetector, didDetectBundleIdentifier bundleIdentifier: String?) {
        Task { @MainActor in
            updateMode(for: bundleIdentifier)
        }
    }
}
