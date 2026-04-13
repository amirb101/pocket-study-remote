"""
Pocket Study Remote — entry point and dependency wiring.

Run with:
    python -m pocket_study_remote

This file creates every component, wires them together via callbacks,
and hands control to the rumps run loop (which owns the AppKit main thread).

Component graph
───────────────
main.py
├── ModeRegistry        — maps bundle IDs → modes
├── ActionRouter        — button + app-change → action dispatch
├── Controller backend  — macOS: GameController; else pygame (background thread)
├── AppDetector         — NSWorkspace polling (background thread)
└── MenuBarApp          — rumps status bar + AppKit run loop (main thread)
"""

from __future__ import annotations

import logging
import os
import sys
import threading
import time
from typing import Callable, Protocol

from .constants import BundleID
from .controller.controller_manager import ControllerManager
from .core.mode_registry import ModeRegistry
from .detection.app_detector import AppDetector
from .modes.browser_mode import BrowserMode
from .modes.global_mode import GlobalMode
from .modes.obsidian_mode import ObsidianMode
from .modes.spotify_mode import SpotifyMode
from .routing.action_router import ActionRouter
from .ui.menu_bar import MenuBarApp

# ---------------------------------------------------------------------------
# Logging (with forced flush so we see output before hangs)
# ---------------------------------------------------------------------------

class _FlushStreamHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[_FlushStreamHandler()],
)
logging.getLogger("pygame").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Accessibility check
# ---------------------------------------------------------------------------

def _check_accessibility() -> None:
    """Warn early if Accessibility permission is missing."""
    exe = os.path.realpath(sys.executable)
    logger.info("Accessibility: add this binary if keystrokes fail → %s", exe)
    try:
        from ApplicationServices import AXIsProcessTrusted  # type: ignore[import]
        if not AXIsProcessTrusted():
            logger.warning(
                "Accessibility permission not granted — keystrokes will not fire.\n"
                "System Settings → Privacy & Security → Accessibility → + → choose:\n"
                "  %s\n"
                "(For a venv, that is usually .venv/bin/python3 after realpath.)",
                exe,
            )
    except ImportError:
        pass


class _ControllerBackend(Protocol):
    @property
    def is_connected(self) -> bool: ...

    def start(self) -> None: ...


def _make_controller(router: ActionRouter) -> _ControllerBackend:
    """
    On macOS, prefer Apple's GameController API so Bluetooth pads work without SDL.
    Fall back to pygame if PyObjC or the framework is unavailable.
    """
    if sys.platform == "darwin":
        try:
            from .controller.apple_gc_input import AppleGCControllerInput

            logger.info(
                "Controller backend: Apple GameController (poll starts after menu bar loads)"
            )
            # Create controller with wrapped callback for calibration
            controller = AppleGCControllerInput(on_button_change=None)

            def calibrated_callback(button, is_pressed):
                # Pass through calibration if active
                if controller.on_button_event_for_calibration(str(button), is_pressed):
                    return  # Calibration consumed this event
                router.button_changed(button, is_pressed)

            # Set the callback on the controller
            controller._cb = calibrated_callback
            return controller
        except Exception as e:
            logger.warning(
                "GameController backend unavailable (%s); falling back to pygame/SDL",
                e,
            )
            logger.info("Controller backend: pygame/SDL (macOS fallback)")
            return ControllerManager(on_button_change=router.button_changed)
    logger.info("Controller backend: pygame/SDL (non-macOS)")
    return ControllerManager(on_button_change=router.button_changed)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

def _build_registry() -> ModeRegistry:
    """
    Populate the mode registry.

    To add a new mode:
    1. Create a new AppMode subclass in modes/
    2. Add its bundle ID(s) to constants.py
    3. Add one register() call here — nothing else changes.
    """
    registry = ModeRegistry(fallback=GlobalMode())
    registry.register(SpotifyMode(),  bundle_ids=[BundleID.SPOTIFY])
    registry.register(BrowserMode(),  bundle_ids=BundleID.CHROMIUM_BROWSERS)
    registry.register(ObsidianMode(), bundle_ids=[BundleID.OBSIDIAN])
    return registry


# ---------------------------------------------------------------------------
# Connection watcher
# ---------------------------------------------------------------------------

def _start_connection_watcher(
    controller: _ControllerBackend,
    on_change: Callable[[bool], None],
) -> None:
    """
    Polls controller.is_connected once per second and fires
    ``on_change`` whenever the state flips.
    """
    def _watch() -> None:
        last_state: bool | None = None
        while True:
            current = controller.is_connected
            if current != last_state:
                on_change(current)
                last_state = current
            time.sleep(1.0)

    threading.Thread(target=_watch, daemon=True, name="ConnectionWatcher").start()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

# Global references for cross-module access
controller: _ControllerBackend | None = None
app: MenuBarApp | None = None


def main() -> None:
    global controller, app
    _check_accessibility()

    registry   = _build_registry()
    router     = ActionRouter(registry=registry)
    controller = _make_controller(router)
    detector   = AppDetector(on_app_change=router.update_mode)

    def on_launch() -> None:
        """Called by rumps after the AppKit run loop starts."""
        logger.info("on_launch: starting controller...")
        try:
            controller.start()
        except Exception as e:
            logger.exception("on_launch: controller.start() failed: %s", e)
            raise
        logger.info("on_launch: controller started, starting detector...")
        detector.start()
        _start_connection_watcher(controller, app.update_connection)
        logger.info("Pocket Study Remote is running")

    logger.info("main: creating MenuBarApp...")
    app = MenuBarApp(on_launch=on_launch)  # noqa: F841 - used via global

    # Wire mode-change callback now that app exists.
    router._on_mode_changed = app.update_mode

    logger.info("main: calling app.run() — rumps will take over the main thread")
    app.run()


if __name__ == "__main__":
    main()
