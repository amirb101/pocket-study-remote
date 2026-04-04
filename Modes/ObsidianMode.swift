/// Controller profile active when Obsidian is the frontmost application.
///
/// This mode relies on custom hotkeys configured in Obsidian's Settings → Hotkeys.
/// The app ships with a one-page setup guide (`ObsidianSetupGuide.md`) that tells
/// the user exactly which commands to assign to which shortcuts. That guide is the
/// source of truth — this file documents the expected mappings in code comments.
///
/// ## Required Obsidian hotkey setup
///
/// Open Obsidian → Settings → Hotkeys, search for each command, and assign:
///
/// | Obsidian command              | Shortcut to assign |
/// |-------------------------------|-------------------|
/// | Open today's daily note       | Ctrl+Shift+D      |
/// | Toggle checklist status       | Ctrl+Shift+C      |
/// | Insert template               | Ctrl+Shift+T      |
/// | Open graph view               | Ctrl+Shift+G      |
///
/// The following already have good defaults and need no changes:
/// - Quick switcher: Cmd+O
/// - Command palette: Cmd+P
/// - Navigate back: Cmd+Opt+Left
/// - Navigate forward: Cmd+Opt+Right
/// - Toggle left sidebar: Cmd+\
/// - Search in all files: Cmd+Shift+F
/// - New note: Cmd+N
struct ObsidianMode: AppMode {

    let id           = "obsidian"
    let displayName  = "Obsidian"
    let sfSymbolName = "note.text"

    var buttonMap: [GamepadButton: Action] {
        [
            // ── Face buttons ──────────────────────────────────────────────

            // A = Command palette: the universal "do anything" button.
            .a: .keystroke(
                .p,
                modifiers: .maskCommand,
                id: "obsidian-command-palette",
                name: "Command Palette"
            ),

            // B = Quick switcher: jump between notes by name.
            .b: .keystroke(
                .o,
                modifiers: .maskCommand,
                id: "obsidian-quick-switcher",
                name: "Quick Switcher"
            ),

            // X = Open today's daily note. Requires custom hotkey in Obsidian.
            .x: .keystroke(
                .d,
                modifiers: [.maskControl, .maskShift],
                id: "obsidian-daily-note",
                name: "Today's Daily Note"
            ),

            // Y = Toggle checklist. Great for dissertation to-do lists.
            // Requires custom hotkey in Obsidian.
            .y: .keystroke(
                .c,
                modifiers: [.maskControl, .maskShift],
                id: "obsidian-toggle-checklist",
                name: "Toggle Checklist"
            ),

            // ── D-Pad ─────────────────────────────────────────────────────

            // Left/right = navigate note history (like browser back/forward).
            .dpadLeft: .keystroke(
                .leftArrow,
                modifiers: [.maskCommand, .maskAlternate],
                id: "obsidian-navigate-back",
                name: "Navigate Back"
            ),

            .dpadRight: .keystroke(
                .rightArrow,
                modifiers: [.maskCommand, .maskAlternate],
                id: "obsidian-navigate-forward",
                name: "Navigate Forward"
            ),

            // Up/down left unassigned — scrolling is better via trackpad
            // in a writing app where precision matters.

            // ── Shoulder buttons ──────────────────────────────────────────

            // L1 = Toggle left sidebar (file explorer).
            .leftShoulder: .keystroke(
                .backslash,
                modifiers: .maskCommand,
                id: "obsidian-toggle-sidebar",
                name: "Toggle Left Sidebar"
            ),

            // R1 = Search across all files.
            .rightShoulder: .keystroke(
                .f,
                modifiers: [.maskCommand, .maskShift],
                id: "obsidian-search-all",
                name: "Search All Files"
            ),

            // ── Triggers ─────────────────────────────────────────────────

            // L2 = Insert template. Requires custom hotkey in Obsidian.
            .leftTrigger: .keystroke(
                .t,
                modifiers: [.maskControl, .maskShift],
                id: "obsidian-insert-template",
                name: "Insert Template"
            ),

            // R2 = Graph view. Requires custom hotkey in Obsidian.
            .rightTrigger: .keystroke(
                .g,
                modifiers: [.maskControl, .maskShift],
                id: "obsidian-graph-view",
                name: "Graph View"
            ),

            // ── Menu buttons ──────────────────────────────────────────────

            .start: .keystroke(
                .n,
                modifiers: .maskCommand,
                id: "obsidian-new-note",
                name: "New Note"
            ),

            .select: .keystroke(
                .f,
                modifiers: [.maskCommand, .maskShift],
                id: "obsidian-search",
                name: "Search"
            ),
        ]
    }
}
