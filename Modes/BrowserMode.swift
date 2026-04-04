/// Controller profile active when any Chromium-family browser is frontmost.
///
/// Covers Comet, Chrome, Arc, Edge, Brave, and Vivaldi — all share identical
/// keyboard shortcuts so a single mode works across all of them.
///
/// Tab navigation is the primary purpose of this mode. The consistent L1/R1 =
/// prev/next-tab mapping makes it feel like a channel remote.
///
/// ## Combo
/// `A + B` = Bookmark page. Bookmarking is behind a combo to prevent accidental
/// triggers: `A` alone opens a new tab, but `B` pressed while `A` is held
/// triggers the bookmark shortcut instead of going back.
struct BrowserMode: AppMode {

    let id           = "browser"
    let displayName  = "Browser"
    let sfSymbolName = "globe"

    var buttonMap: [GamepadButton: Action] {
        [
            // ── Face buttons ──────────────────────────────────────────────

            .a: .keystroke(
                .t,
                modifiers: .maskCommand,
                id: "browser-new-tab",
                name: "New Tab"
            ),

            // B alone = navigate back.
            // B while A is held = bookmark (handled in comboMap).
            .b: .keystroke(
                .leftBracket,
                modifiers: .maskCommand,
                id: "browser-go-back",
                name: "Go Back"
            ),

            .x: .keystroke(
                .w,
                modifiers: .maskCommand,
                id: "browser-close-tab",
                name: "Close Tab"
            ),

            // Reopen the most recently closed tab.
            .y: .keystroke(
                .t,
                modifiers: [.maskCommand, .maskShift],
                id: "browser-reopen-tab",
                name: "Reopen Closed Tab"
            ),

            // ── D-Pad ─────────────────────────────────────────────────────

            .dpadLeft: .keystroke(
                .leftBracket,
                modifiers: .maskCommand,
                id: "browser-back",
                name: "Page Back"
            ),

            .dpadRight: .keystroke(
                .rightBracket,
                modifiers: .maskCommand,
                id: "browser-forward",
                name: "Page Forward"
            ),

            .dpadUp: .keystroke(
                .pageUp,
                id: "browser-scroll-up",
                name: "Scroll Up"
            ),

            .dpadDown: .keystroke(
                .pageDown,
                id: "browser-scroll-down",
                name: "Scroll Down"
            ),

            // ── Shoulder buttons (tab cycling) ────────────────────────────

            .leftShoulder: .keystroke(
                .leftBracket,
                modifiers: [.maskCommand, .maskShift],
                id: "browser-prev-tab",
                name: "Previous Tab"
            ),

            .rightShoulder: .keystroke(
                .rightBracket,
                modifiers: [.maskCommand, .maskShift],
                id: "browser-next-tab",
                name: "Next Tab"
            ),

            // ── Triggers ─────────────────────────────────────────────────

            .leftTrigger: .keystroke(
                .n,
                modifiers: .maskCommand,
                id: "browser-new-window",
                name: "New Window"
            ),

            // Cmd+Shift+A = Search tabs in Chrome/Comet/Arc.
            .rightTrigger: .keystroke(
                .a,
                modifiers: [.maskCommand, .maskShift],
                id: "browser-tab-search",
                name: "Search Tabs"
            ),

            // ── Menu buttons ──────────────────────────────────────────────

            // Focus the address bar so she can type a URL.
            .start: .keystroke(
                .l,
                modifiers: .maskCommand,
                id: "browser-focus-address-bar",
                name: "Focus Address Bar"
            ),

            // Zoom in / out could live here — leaving unassigned for now.
        ]
    }

    // MARK: - Combos

    var comboMap: [ButtonCombo: Action] {
        [
            // A + B together = Bookmark.
            // A alone fires "new tab"; B alone fires "go back".
            // When B is pressed while A is held, the bookmark shortcut fires
            // instead of "go back", because the combo takes priority.
            ButtonCombo(.a, .b): .keystroke(
                .d,
                modifiers: .maskCommand,
                id: "browser-bookmark",
                name: "Bookmark Page"
            ),
        ]
    }
}
