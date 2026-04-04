/// A named controller profile that maps buttons to actions.
///
/// Conforming types define the complete behaviour of the controller while a
/// particular application is in the foreground. Adding support for a new app
/// means creating a new struct that conforms to this protocol — nothing else
/// in the codebase needs to change.
///
/// ## Conformance
///
/// At minimum, provide `id`, `displayName`, `sfSymbolName`, and `buttonMap`.
/// The `comboMap` has a default empty implementation so it can be omitted
/// until you need it.
///
/// ```swift
/// struct WordMode: AppMode {
///     let id = "word"
///     let displayName = "Word"
///     let sfSymbolName = "doc.text"
///     var buttonMap: [GamepadButton: Action] { ... }
/// }
/// ```
protocol AppMode {

    /// A stable, URL-safe identifier. Used for serialising preferences to disk.
    var id: String { get }

    /// The name shown in the overlay toast and the menu bar.
    var displayName: String { get }

    /// An SF Symbol name for the mode icon shown in the overlay and menu bar.
    var sfSymbolName: String { get }

    /// Maps individual button presses to actions.
    ///
    /// Buttons not present in this dictionary produce no action when pressed.
    var buttonMap: [GamepadButton: Action] { get }

    /// Maps multi-button combos to actions.
    ///
    /// Combos take priority over single-button actions: if the current held-
    /// button set satisfies a combo here, only that combo's action fires.
    var comboMap: [ButtonCombo: Action] { get }
}

// MARK: - Default Implementations

extension AppMode {

    /// Modes do not define combos by default.
    var comboMap: [ButtonCombo: Action] { [:] }
}
