import CoreGraphics
import Foundation

/// App-wide constants.
///
/// All magic numbers live here. Nothing elsewhere in the codebase should
/// contain a numeric or string literal that isn't self-explanatory at the
/// call site — if it isn't obvious, it belongs here with a doc comment.
enum Constants {

    // MARK: - Overlay UI

    enum Overlay {
        /// How long the overlay remains fully visible before fading out.
        static let holdDuration: TimeInterval = 1.2

        /// Duration of the fade-in animation.
        static let fadeInDuration: TimeInterval = 0.15

        /// Duration of the fade-out animation.
        static let fadeOutDuration: TimeInterval = 0.3

        /// Distance from the bottom edge of the screen (points).
        static let bottomPadding: CGFloat = 80

        /// Horizontal padding inside the overlay pill.
        static let horizontalPadding: CGFloat = 20

        /// Vertical padding inside the overlay pill.
        static let verticalPadding: CGFloat = 12

        /// Corner radius of the overlay pill.
        static let cornerRadius: CGFloat = 14

        /// Font size for the mode label text.
        static let labelFontSize: CGFloat = 16

        /// Size of the SF Symbol icon.
        static let iconSize: CGFloat = 20

        /// Gap between icon and label.
        static let iconLabelSpacing: CGFloat = 8
    }

    // MARK: - Controller

    enum Controller {
        /// Minimum trigger axis value (0–1) to register a trigger as "pressed".
        /// Prevents accidental triggers from resting finger weight.
        static let triggerPressThreshold: Float = 0.5

        /// Time window (seconds) within which multiple simultaneous presses
        /// are treated as a combo. If two buttons are pressed within this
        /// window, the combo is evaluated before individual actions.
        static let comboDetectionWindowSeconds: TimeInterval = 0.08
    }

    // MARK: - Spotify

    enum Spotify {
        /// How many points (0–100 scale) to shift the volume per press.
        static let volumeStep: Int = 10

        /// How many seconds to seek forward or backward per press.
        static let seekStepSeconds: Double = 15.0
    }

    // MARK: - System Volume

    enum Volume {
        /// Step size for system volume adjustments.
        static let stepSize: Int = 10
    }

    // MARK: - Bundle Identifiers

    /// All bundle identifiers the app needs to know about.
    ///
    /// - Note: Comet's bundle ID must be verified on the target machine:
    ///   `mdls -name kMDItemCFBundleIdentifier /Applications/Comet.app`
    ///   Update `cometBrowser` below once confirmed.
    enum BundleID {

        // Apps with dedicated modes
        static let spotify  = "com.spotify.client"
        static let obsidian = "md.obsidian"

        // Chromium-family browsers (all share the same BrowserMode)
        static let chrome        = "com.google.Chrome"
        static let arc           = "company.thebrowser.Browser"
        static let edge          = "com.microsoft.Edge"
        static let brave         = "com.brave.Browser"
        static let vivaldi       = "com.vivaldi.Vivaldi"
        static let cometBrowser  = "ai.perplexity.comet"  // ← confirm this

        /// All recognised Chromium-family browser bundle IDs.
        static let chromiumBrowsers: [String] = [
            chrome,
            arc,
            edge,
            brave,
            vivaldi,
            cometBrowser,
        ]
    }

    // MARK: - User Defaults Keys

    /// Keys used for persisting state to `UserDefaults`.
    enum DefaultsKey {
        static let launchAtLogin      = "launchAtLogin"
        static let customButtonMappings = "customButtonMappings"
        static let hasGrantedAccessibility = "hasGrantedAccessibility"
    }
}
