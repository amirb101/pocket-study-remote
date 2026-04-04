import AppKit
import SwiftUI

/// A brief, non-interactive toast that appears at the bottom of the screen
/// whenever the active mode changes.
///
/// The overlay is a floating `NSPanel` that sits above all other windows.
/// It fades in, holds, then fades out — and never captures focus or
/// interferes with keyboard input.
///
/// ```
/// ┌─────────────────────┐
/// │  🎵  Spotify Mode   │
/// └─────────────────────┘
/// ```
final class OverlayWindow {

    // MARK: - Private State

    private var panel: NSPanel?
    private var dismissTask: Task<Void, Never>?

    // MARK: - Public Interface

    /// Shows the overlay for the given mode, then dismisses it automatically.
    ///
    /// If the overlay is already visible, it is updated in place and the
    /// dismiss timer resets — so rapid mode switches produce smooth updates
    /// rather than flickering panels.
    @MainActor
    func show(mode: any AppMode) {
        // Cancel any in-flight dismiss
        dismissTask?.cancel()

        let panel = makePanel(for: mode)
        self.panel = panel

        // Position at bottom-centre of the main screen
        if let screen = NSScreen.main {
            let windowWidth = panel.frame.width
            let x = screen.visibleFrame.midX - windowWidth / 2
            let y = screen.visibleFrame.minY + Constants.Overlay.bottomPadding
            panel.setFrameOrigin(NSPoint(x: x, y: y))
        }

        panel.alphaValue = 0
        panel.orderFront(nil)

        NSAnimationContext.runAnimationGroup { context in
            context.duration = Constants.Overlay.fadeInDuration
            panel.animator().alphaValue = 1
        }

        dismissTask = Task { [weak self] in
            try? await Task.sleep(
                nanoseconds: UInt64(Constants.Overlay.holdDuration * 1_000_000_000)
            )
            guard !Task.isCancelled else { return }
            await self?.dismiss()
        }
    }

    // MARK: - Private

    @MainActor
    private func dismiss() {
        guard let panel else { return }
        NSAnimationContext.runAnimationGroup({ context in
            context.duration = Constants.Overlay.fadeOutDuration
            panel.animator().alphaValue = 0
        }, completionHandler: {
            panel.orderOut(nil)
            self.panel = nil
        })
    }

    private func makePanel(for mode: any AppMode) -> NSPanel {
        let contentView = OverlayContentView(
            symbolName: mode.sfSymbolName,
            label: mode.displayName
        )

        let hostingView = NSHostingView(rootView: contentView)
        hostingView.translatesAutoresizingMaskIntoConstraints = false

        // Size the panel to fit its content
        let fittingSize = hostingView.fittingSize

        let panel = NSPanel(
            contentRect: NSRect(origin: .zero, size: fittingSize),
            styleMask: [.borderless, .nonactivatingPanel],
            backing: .buffered,
            defer: false
        )
        panel.contentView = hostingView
        panel.isOpaque = false
        panel.backgroundColor = .clear
        panel.level = .floating
        panel.ignoresMouseEvents = true
        panel.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]

        return panel
    }
}

// MARK: - SwiftUI Content View

private struct OverlayContentView: View {

    let symbolName: String
    let label: String

    var body: some View {
        HStack(spacing: Constants.Overlay.iconLabelSpacing) {
            Image(systemName: symbolName)
                .font(.system(size: Constants.Overlay.iconSize, weight: .medium))

            Text(label)
                .font(.system(size: Constants.Overlay.labelFontSize, weight: .semibold))
        }
        .padding(.horizontal, Constants.Overlay.horizontalPadding)
        .padding(.vertical, Constants.Overlay.verticalPadding)
        .background(
            RoundedRectangle(cornerRadius: Constants.Overlay.cornerRadius, style: .continuous)
                .fill(.regularMaterial)
        )
        .foregroundStyle(.primary)
    }
}

// MARK: - Preview

#if DEBUG
#Preview {
    OverlayContentView(symbolName: "music.note", label: "Spotify")
        .padding()
}
#endif
