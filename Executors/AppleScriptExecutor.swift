import Foundation
import os

/// Runs AppleScript source strings asynchronously on a dedicated background queue.
///
/// AppleScript execution can block for 200–800ms, so all work is dispatched
/// off the main thread. Errors are logged but not surfaced to the user —
/// if a command silently fails (e.g. Spotify quits mid-command), the app
/// continues normally.
///
/// This is a pure namespace (caseless enum) — all methods are static.
enum AppleScriptExecutor {

    // MARK: - Private

    /// Serial queue for all AppleScript work.
    /// Serial (not concurrent) because some scripts depend on prior state
    /// (e.g. Spotify volume adjustments are additive).
    private static let queue = DispatchQueue(
        label: "com.pocketstudyremote.applescript",
        qos: .userInitiated
    )

    // MARK: - Core Run

    /// Compiles and runs an AppleScript source string asynchronously.
    ///
    /// - Parameter source: A valid AppleScript source string.
    static func run(_ source: String) {
        queue.async {
            var errorDict: NSDictionary?
            guard let script = NSAppleScript(source: source) else {
                Logger.actions.error("AppleScriptExecutor: failed to initialise script")
                return
            }
            script.executeAndReturnError(&errorDict)
            if let error = errorDict {
                Logger.actions.error("AppleScript error: \(error)")
            }
        }
    }

    // MARK: - Spotify Namespace

    /// Pre-built AppleScript sources for Spotify commands.
    ///
    /// Using computed strings keeps the mode definitions readable:
    /// `AppleScriptExecutor.Spotify.playpause` rather than an inline script literal.
    enum Spotify {

        static var playpause: String {
            script("playpause")
        }

        static var nextTrack: String {
            script("next track")
        }

        static var previousTrack: String {
            script("previous track")
        }

        static var toggleShuffle: String {
            script("set shuffling to not shuffling")
        }

        static var toggleRepeat: String {
            script("set repeating to not repeating")
        }

        static func adjustVolume(by delta: Int) -> String {
            // Clamp is handled by Spotify itself; passing > 100 or < 0 is safe.
            script("set sound volume to (sound volume + \(delta))")
        }

        static func seekRelative(by seconds: Double) -> String {
            script("set player position to (player position + \(seconds))")
        }

        /// `tell application "Spotify" to <verb>  end tell`
        private static func script(_ verb: String) -> String {
            """
            tell application "Spotify"
                \(verb)
            end tell
            """
        }
    }

    // MARK: - System Namespace

    /// Pre-built AppleScript sources for system-level commands.
    enum System {

        static func adjustVolume(by delta: Int) -> String {
            """
            set currentVolume to output volume of (get volume settings)
            set volume output volume (currentVolume + \(delta))
            """
        }

        static var toggleMute: String {
            """
            set isMuted to output muted of (get volume settings)
            set volume output muted (not isMuted)
            """
        }
    }
}
