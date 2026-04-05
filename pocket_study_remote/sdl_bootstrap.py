"""
SDL / pygame setup for joystick access on macOS.

``SDL_VIDEODRIVER=dummy`` (common for headless pygame) often yields **zero**
joysticks on macOS with SDL2. We skip dummy video on Darwin and open a 1×1
hidden window so the Cocoa path can see Bluetooth/USB gamepads.

``pygame.display`` must be touched from the **main thread** on macOS; the
rumps/AppKit run loop calls :func:`bootstrap_pygame_joystick` before the
controller poll thread starts.
"""

from __future__ import annotations

import logging
import os
import sys

logger = logging.getLogger(__name__)

_done = False


def configure_sdl_env() -> None:
    """Call before ``import pygame`` (any thread)."""
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    if sys.platform == "darwin":
        os.environ.setdefault("SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", "1")
        # Critical: do NOT force dummy video on macOS — SDL then often reports 0 joysticks.
        if os.environ.get("SDL_VIDEODRIVER") == "dummy":
            del os.environ["SDL_VIDEODRIVER"]
    else:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")


def bootstrap_pygame_joystick() -> None:
    """
    Run once on the **main thread** (e.g. rumps ``application_did_finish_launching``)
    before starting the background joystick poll loop.
    """
    global _done
    if _done:
        return

    configure_sdl_env()

    import pygame

    pygame.init()
    if sys.platform == "darwin":
        try:
            flags = getattr(pygame, "HIDDEN", 0)
            pygame.display.set_mode((1, 1), flags)
            logger.info("SDL (macOS): hidden display created for joystick enumeration")
        except Exception as e:
            logger.warning("SDL (macOS): hidden display failed (%s) — joysticks may not work", e)
    pygame.joystick.init()
    _done = True
    logger.info(
        "SDL bootstrap complete; pygame reports %d joystick(s)",
        pygame.joystick.get_count(),
    )
