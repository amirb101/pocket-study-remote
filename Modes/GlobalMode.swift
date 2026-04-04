import AppKit

/// The fallback mode, active whenever no specific app mode is matched.
///
/// Provides universally useful controls that work regardless of context:
/// music playback, volume, system navigation, and quick app launch.
///
/// Design principle: every button here should feel natural to press "blindly"
/// (without looking at the screen). Stick to high-frequency, low-risk actions.
struct GlobalMode: AppMode {

    let id           = "global"
    let displayName  = "Global"
    let sfSymbolName = "gamecontroller"

    var buttonMap: [GamepadButton: Action] {
        [
            // ── Face buttons ──────────────────────────────────────────────

            .a: .appleScript(
                AppleScriptExecutor.Spotify.playpause,
                id: "global-play-pause",
                name: "Play / Pause"
            ),

            .b: .appleScript(
                AppleScriptExecutor.System.toggleMute,
                id: "global-toggle-mute",
                name: "Toggle Mute"
            ),

            .x: .screenshot(
                region: true,
                id: "global-screenshot-region",
                name: "Screenshot (Region)"
            ),

            .y: .screenshot(
                region: false,
                id: "global-screenshot-full",
                name: "Screenshot (Full Screen)"
            ),

            // ── D-Pad ─────────────────────────────────────────────────────

            .dpadUp: .adjustVolume(
                by: Constants.Volume.stepSize,
                id: "global-volume-up",
                name: "Volume Up"
            ),

            .dpadDown: .adjustVolume(
                by: -Constants.Volume.stepSize,
                id: "global-volume-down",
                name: "Volume Down"
            ),

            .dpadLeft: .appleScript(
                AppleScriptExecutor.Spotify.previousTrack,
                id: "global-previous-track",
                name: "Previous Track"
            ),

            .dpadRight: .appleScript(
                AppleScriptExecutor.Spotify.nextTrack,
                id: "global-next-track",
                name: "Next Track"
            ),

            // ── Shoulder buttons ──────────────────────────────────────────

            .leftShoulder: .switchSpace(
                direction: .left,
                id: "global-space-left",
                name: "Switch Space Left"
            ),

            .rightShoulder: .switchSpace(
                direction: .right,
                id: "global-space-right",
                name: "Switch Space Right"
            ),

            // ── Triggers ─────────────────────────────────────────────────

            .leftTrigger: .keystroke(
                .upArrow,
                modifiers: .maskControl,
                id: "global-mission-control",
                name: "Mission Control"
            ),

            // rightTrigger intentionally unassigned in V1

            // ── Menu buttons ──────────────────────────────────────────────

            .start: .openApp(
                bundleIdentifier: Constants.BundleID.obsidian,
                id: "global-open-obsidian",
                name: "Open Obsidian"
            ),

            .select: .openApp(
                bundleIdentifier: Constants.BundleID.spotify,
                id: "global-open-spotify",
                name: "Open Spotify"
            ),
        ]
    }
}
