/// A combination of two or more buttons that must be held simultaneously
/// to trigger a composite action.
///
/// Combos are checked before single-button actions: if the held-button set
/// satisfies a registered combo, the combo action fires and the individual
/// button actions do not. This means single presses and combos never conflict
/// from the user's perspective.
///
/// Example:
/// ```swift
/// // A alone → new tab
/// // A + B together → bookmark (A's action is suppressed when B is pressed while A is held)
/// let bookmark = ButtonCombo(.a, .b)
/// ```
struct ButtonCombo: Hashable {

    /// The set of buttons that must all be held for this combo to fire.
    let buttons: Set<GamepadButton>

    /// Creates a combo from two or more buttons.
    init(_ first: GamepadButton, _ second: GamepadButton, _ rest: GamepadButton...) {
        self.buttons = Set([first, second] + rest)
    }

    // MARK: - Matching

    /// Returns `true` if every button in this combo appears in `heldButtons`.
    /// The held set may contain additional buttons beyond this combo's members.
    func matches(heldButtons: Set<GamepadButton>) -> Bool {
        buttons.isSubset(of: heldButtons)
    }
}
