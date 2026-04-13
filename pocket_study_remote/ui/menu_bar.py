"""
MenuBarController — rumps-based status bar app.

The status item icon shows whether the controller is connected.
Clicking it opens a menu with the current mode, connection state,
launch-at-login toggle, and Quit.

The mode-change overlay is implemented here as a brief title flash:
the status item label switches to the mode name for ``Overlay.HOLD_SECONDS``
then clears back to just the icon.  Simple, zero extra dependencies.
"""

from __future__ import annotations

import logging
import subprocess

import rumps  # type: ignore[import]

from ..constants import Overlay
from ..core.app_mode import AppMode

logger = logging.getLogger(__name__)

# Status item icons (text fallbacks if SF Symbols aren't available in rumps)
_ICON_CONNECTED    = "🎮"
_ICON_DISCONNECTED = "🎮"   # same for now — swap for a dimmed icon if desired


class MenuBarApp(rumps.App):
    """
    The rumps application object.  Owns the AppKit run loop.

    All other components are started from ``application_did_finish_launching``
    (called automatically by rumps) and communicate back via callbacks set in
    ``main.py``.
    """

    def __init__(self, on_launch: "Callable[[], None]") -> None:  # noqa: F821
        super().__init__(
            name="Pocket Study Remote",
            title=_ICON_DISCONNECTED,
            quit_button=None,   # we add our own quit item below
        )
        self._on_launch    = on_launch
        self._current_mode = "—"
        self._is_connected = False
        self._overlay_timer: rumps.Timer | None = None

        self._rebuild_menu()

    # ------------------------------------------------------------------
    # Public updates (called from other threads — rumps is thread-safe
    # for menu/title updates)
    # ------------------------------------------------------------------

    def update_mode(self, mode: AppMode) -> None:
        """Reflect a mode change in the status bar and flash the mode name."""
        self._current_mode = mode.display_name
        self._rebuild_menu()
        self._flash_overlay(mode)

    def update_connection(self, is_connected: bool) -> None:
        """Reflect the controller connection state."""
        self._is_connected = is_connected
        self.title = _ICON_CONNECTED if is_connected else _ICON_DISCONNECTED
        self._rebuild_menu()

    # ------------------------------------------------------------------
    # rumps lifecycle
    # ------------------------------------------------------------------

    def application_did_finish_launching(self, notification) -> None:
        """Called by rumps after the AppKit run loop starts."""
        logger.info("MenuBarApp: application_did_finish_launching — starting controller")
        # GameController defaults to ignoring pads while this process is not key;
        # menu bar remotes must opt in or the controller appears "dead" in other apps.
        try:
            from GameController import GCController

            GCController.setShouldMonitorBackgroundEvents_(True)
            logger.info("GameController: shouldMonitorBackgroundEvents enabled")
        except Exception as e:
            logger.debug("GameController shouldMonitorBackgroundEvents: %s", e)

        try:
            self._on_launch()
        except Exception as e:
            logger.exception("MenuBarApp: _on_launch failed: %s", e)

    # ------------------------------------------------------------------
    # Private: overlay flash
    # ------------------------------------------------------------------

    def _flash_overlay(self, mode: AppMode) -> None:
        """
        Briefly show the mode name in the status bar title, then reset.

        This is the simplest possible mode-change indicator that requires
        zero extra dependencies and no Accessibility permissions.
        """
        # Cancel any in-flight reset timer
        if self._overlay_timer:
            self._overlay_timer.stop()

        self.title = f"{mode.display_name}"

        self._overlay_timer = rumps.Timer(self._reset_title, Overlay.HOLD_SECONDS)
        self._overlay_timer.start()

    def _reset_title(self, _timer) -> None:
        self.title = _ICON_CONNECTED if self._is_connected else _ICON_DISCONNECTED
        if self._overlay_timer:
            self._overlay_timer.stop()
            self._overlay_timer = None

    # ------------------------------------------------------------------
    # Private: menu
    # ------------------------------------------------------------------

    def _rebuild_menu(self) -> None:
        connection_label = (
            "Controller: Connected ✓" if self._is_connected
            else "Controller: Not Connected"
        )

        self.menu.clear()
        self.menu = [
            rumps.MenuItem("Pocket Study Remote (menu bar only — no window)", callback=None),
            None,
            rumps.MenuItem(f"Mode: {self._current_mode}", callback=None),
            rumps.MenuItem(connection_label, callback=None),
            None,
            rumps.MenuItem(
                "Open Accessibility Settings…",
                callback=self._open_accessibility_settings,
            ),
            None,
            rumps.MenuItem("Quit", callback=rumps.quit_application),
        ]

    def _open_accessibility_settings(self, _) -> None:
        """System Settings → Privacy & Security → Accessibility (for simulated keystrokes)."""
        subprocess.run(
            [
                "open",
                "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility",
            ],
            check=False,
        )
