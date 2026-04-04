import GameController
import os

/// Manages the lifecycle of a connected 8BitDo Micro (or any GCController)
/// and translates raw GameController framework events into typed `GamepadButton`
/// presses that the rest of the app can understand.
///
/// `ControllerManager` owns the connection — all other components receive
/// button events through the `delegate` and never touch `GCController` directly.
/// This keeps the GameController framework isolated to a single file.
///
/// ## Controller setup
/// The 8BitDo Micro must be in **D mode** (physical switch on the device bottom).
/// In D mode it presents as a standard extended gamepad, which exposes all
/// face buttons, D-pad, shoulders, triggers, and menu buttons.
///
/// ## Threading
/// GameController callbacks arrive on an unspecified background thread.
/// `ControllerManager` dispatches all delegate calls to `DispatchQueue.main`
/// before forwarding them, so delegates can safely update UI.
final class ControllerManager {

    // MARK: - Delegate

    weak var delegate: ControllerManagerDelegate?

    // MARK: - State

    private(set) var isConnected: Bool = false
    private var controller: GCController?

    // MARK: - Initialisation and Discovery

    init() {
        observeConnectionNotifications()
    }

    /// Begins scanning for wireless controllers.
    /// Call this once from `AppDelegate.applicationDidFinishLaunching`.
    func startDiscovery() {
        GCController.startWirelessControllerDiscovery {
            Logger.controller.info("Wireless controller discovery started")
        }

        // A controller may already be connected from a previous session.
        if let existing = GCController.controllers().first {
            connect(existing)
        }
    }

    // MARK: - Private: Notifications

    private func observeConnectionNotifications() {
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(controllerDidConnect(_:)),
            name: .GCControllerDidConnect,
            object: nil
        )
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(controllerDidDisconnect(_:)),
            name: .GCControllerDidDisconnect,
            object: nil
        )
    }

    @objc private func controllerDidConnect(_ notification: Notification) {
        guard let controller = notification.object as? GCController else { return }
        connect(controller)
    }

    @objc private func controllerDidDisconnect(_ notification: Notification) {
        Logger.controller.info("Controller disconnected")
        self.controller = nil
        isConnected = false
        DispatchQueue.main.async { [weak self] in
            self?.delegate?.controllerDidDisconnect()
        }
    }

    // MARK: - Private: Binding

    private func connect(_ controller: GCController) {
        guard controller.extendedGamepad != nil else {
            // The Micro in D-mode always presents as an extended gamepad.
            // If this fires, the controller is in the wrong mode.
            Logger.controller.error(
                "Connected controller does not expose an extended gamepad profile. Ensure the 8BitDo Micro switch is set to D mode."
            )
            return
        }

        self.controller = controller
        isConnected = true
        Logger.controller.info("Controller connected: \(controller.vendorName ?? "unknown")")

        bindButtons(for: controller)

        DispatchQueue.main.async { [weak self] in
            self?.delegate?.controllerDidConnect()
        }
    }

    private func bindButtons(for controller: GCController) {
        guard let pad = controller.extendedGamepad else { return }

        // MARK: Face buttons
        bind(pad.buttonA,  to: .a)
        bind(pad.buttonB,  to: .b)
        bind(pad.buttonX,  to: .x)
        bind(pad.buttonY,  to: .y)

        // MARK: D-pad
        pad.dpad.up.pressedChangedHandler    = makeHandler(for: .dpadUp)
        pad.dpad.down.pressedChangedHandler  = makeHandler(for: .dpadDown)
        pad.dpad.left.pressedChangedHandler  = makeHandler(for: .dpadLeft)
        pad.dpad.right.pressedChangedHandler = makeHandler(for: .dpadRight)

        // MARK: Shoulder buttons
        bind(pad.leftShoulder,  to: .leftShoulder)
        bind(pad.rightShoulder, to: .rightShoulder)

        // MARK: Triggers
        // Triggers are analogue (0.0–1.0). We treat them as digital using a
        // threshold defined in Constants so there is one place to tune sensitivity.
        bindTrigger(pad.leftTrigger,  to: .leftTrigger)
        bindTrigger(pad.rightTrigger, to: .rightTrigger)

        // MARK: Menu buttons
        // Note: buttonMenu and buttonOptions may map differently depending on
        // firmware version. Log the first press of each during development to
        // confirm which physical button each corresponds to on your unit.
        bind(pad.buttonMenu, to: .start)
        if let options = pad.buttonOptions {
            bind(options, to: .select)
        }
    }

    // MARK: - Private: Handler Factories

    /// Returns a handler that dispatches a typed button event to the delegate on main.
    private func makeHandler(for button: GamepadButton) -> GCControllerButtonValueChangedHandler {
        { [weak self] _, _, isPressed in
            DispatchQueue.main.async {
                self?.delegate?.controllerButton(button, didChange: isPressed)
            }
        }
    }

    private func bind(_ element: GCControllerButtonInput, to button: GamepadButton) {
        element.pressedChangedHandler = makeHandler(for: button)
    }

    private func bindTrigger(_ trigger: GCControllerButtonInput, to button: GamepadButton) {
        trigger.valueChangedHandler = { [weak self] _, value, _ in
            let isPressed = value >= Constants.Controller.triggerPressThreshold
            DispatchQueue.main.async {
                self?.delegate?.controllerButton(button, didChange: isPressed)
            }
        }
    }
}

// MARK: - Delegate Protocol

/// Receives typed controller events on the main thread.
protocol ControllerManagerDelegate: AnyObject {
    func controllerDidConnect()
    func controllerDidDisconnect()
    func controllerButton(_ button: GamepadButton, didChange isPressed: Bool)
}
