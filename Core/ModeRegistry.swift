import os

/// Associates bundle identifiers with `AppMode` conformers and resolves the
/// active mode for any given frontmost application.
///
/// Registration order does not matter — bundle IDs must be unique across all
/// registered modes. If a bundle ID is registered twice, a warning is logged
/// and the later registration wins.
///
/// Modes are registered in `AppDelegate` at startup:
/// ```swift
/// let registry = ModeRegistry(fallback: GlobalMode())
/// registry.register(SpotifyMode(), for: [BundleID.spotify])
/// registry.register(BrowserMode(), for: BundleID.chromiumBrowsers)
/// ```
final class ModeRegistry {

    // MARK: - Properties

    /// The mode used when no registered bundle ID matches the frontmost app.
    let fallback: any AppMode

    /// Flat lookup table built incrementally as modes are registered.
    private var bundleIDToMode: [String: any AppMode] = [:]

    // MARK: - Initialisation

    init(fallback: any AppMode) {
        self.fallback = fallback
    }

    // MARK: - Registration

    /// Registers an `AppMode` for one or more bundle identifiers.
    ///
    /// - Parameters:
    ///   - mode: The mode to activate when any of the given apps comes to front.
    ///   - bundleIdentifiers: One or more `CFBundleIdentifier` strings.
    func register(_ mode: any AppMode, for bundleIdentifiers: [String]) {
        for bundleID in bundleIdentifiers {
            if bundleIDToMode[bundleID] != nil {
                Logger.detection.warning(
                    "Bundle ID '\(bundleID)' is already registered — overwriting with '\(mode.id)'"
                )
            }
            bundleIDToMode[bundleID] = mode
        }
    }

    // MARK: - Resolution

    /// Returns the mode for the given bundle identifier, or `fallback` if none matches.
    func mode(for bundleIdentifier: String?) -> any AppMode {
        guard let bundleID = bundleIdentifier else { return fallback }
        return bundleIDToMode[bundleID] ?? fallback
    }

    /// Returns `true` if the given bundle identifier has a registered mode
    /// (excluding the fallback).
    func hasRegisteredMode(for bundleIdentifier: String?) -> Bool {
        guard let bundleID = bundleIdentifier else { return false }
        return bundleIDToMode[bundleID] != nil
    }
}
