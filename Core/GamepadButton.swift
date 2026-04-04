/// Every physical button on the 8BitDo Micro that the app can respond to.
///
/// Using a dedicated enum rather than the raw GameController framework types
/// keeps mode definitions clean and decoupled from Apple's framework internals.
/// If the controller hardware changes, only `ControllerManager` needs updating.
enum GamepadButton: String, CaseIterable, Hashable {

    // MARK: - Face Buttons

    case a = "A"
    case b = "B"
    case x = "X"
    case y = "Y"

    // MARK: - D-Pad

    case dpadUp    = "D-Pad Up"
    case dpadDown  = "D-Pad Down"
    case dpadLeft  = "D-Pad Left"
    case dpadRight = "D-Pad Right"

    // MARK: - Shoulder Buttons

    case leftShoulder  = "L1"
    case rightShoulder = "R1"
    case leftTrigger   = "L2"
    case rightTrigger  = "R2"

    // MARK: - Menu Buttons

    case start  = "Start"
    case select = "Select"

    // MARK: - Computed Properties

    /// A display-friendly label for preferences UI and accessibility labels.
    var displayName: String { rawValue }
}
