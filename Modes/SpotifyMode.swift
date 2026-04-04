/// Controller profile active when Spotify is the frontmost application.
///
/// All actions use the Spotify AppleScript dictionary — no keyboard shortcuts
/// needed. Playback control (play/pause, next/prev, seek, volume, shuffle,
/// repeat) is fully reliable via AppleScript on Mac.
///
/// - Note: "Save to library" is implemented as Cmd+S (Spotify's own keyboard
///   shortcut) rather than an AppleScript verb, because the `save` action is
///   not a first-class primitive in Spotify's scripting dictionary.
struct SpotifyMode: AppMode {

    let id           = "spotify"
    let displayName  = "Spotify"
    let sfSymbolName = "music.note"

    var buttonMap: [GamepadButton: Action] {
        [
            // ── Face buttons ──────────────────────────────────────────────

            .a: .appleScript(
                AppleScriptExecutor.Spotify.playpause,
                id: "spotify-play-pause",
                name: "Play / Pause"
            ),

            // Cmd+S = Spotify's native "Save to Library" shortcut.
            // More reliable than AppleScript for library actions.
            .b: .keystroke(
                .s,
                modifiers: .maskCommand,
                id: "spotify-save-track",
                name: "Save Track to Library"
            ),

            .x: .appleScript(
                AppleScriptExecutor.Spotify.toggleShuffle,
                id: "spotify-toggle-shuffle",
                name: "Toggle Shuffle"
            ),

            .y: .appleScript(
                AppleScriptExecutor.Spotify.toggleRepeat,
                id: "spotify-toggle-repeat",
                name: "Toggle Repeat"
            ),

            // ── D-Pad ─────────────────────────────────────────────────────

            .dpadUp: .appleScript(
                AppleScriptExecutor.Spotify.adjustVolume(by: Constants.Spotify.volumeStep),
                id: "spotify-volume-up",
                name: "Volume Up"
            ),

            .dpadDown: .appleScript(
                AppleScriptExecutor.Spotify.adjustVolume(by: -Constants.Spotify.volumeStep),
                id: "spotify-volume-down",
                name: "Volume Down"
            ),

            .dpadLeft: .appleScript(
                AppleScriptExecutor.Spotify.previousTrack,
                id: "spotify-previous-track",
                name: "Previous Track"
            ),

            .dpadRight: .appleScript(
                AppleScriptExecutor.Spotify.nextTrack,
                id: "spotify-next-track",
                name: "Next Track"
            ),

            // ── Shoulder buttons ──────────────────────────────────────────

            .leftShoulder: .appleScript(
                AppleScriptExecutor.Spotify.seekRelative(by: -Constants.Spotify.seekStepSeconds),
                id: "spotify-seek-back",
                name: "Seek Back 15s"
            ),

            .rightShoulder: .appleScript(
                AppleScriptExecutor.Spotify.seekRelative(by: Constants.Spotify.seekStepSeconds),
                id: "spotify-seek-forward",
                name: "Seek Forward 15s"
            ),

            // ── Menu buttons ──────────────────────────────────────────────

            // Start: bring Spotify to front (it's already frontmost in this mode,
            // but this is useful after mode-switching back from another app)
            .start: .openApp(
                bundleIdentifier: Constants.BundleID.spotify,
                id: "spotify-focus",
                name: "Focus Spotify"
            ),
        ]
    }
}
