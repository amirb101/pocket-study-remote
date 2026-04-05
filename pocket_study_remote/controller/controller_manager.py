"""
ControllerManager — reads gamepad input from the 8BitDo Micro via pygame
and translates raw hardware events into typed ``GamepadButton`` presses.

Design goals:
- All pygame I/O runs on a single dedicated daemon thread.
- The rest of the app never touches pygame directly.
- Button-to-enum mapping is fully contained here; changing hardware or
  firmware requires only editing this file.

Threading:
    The polling loop runs on ``_PollThread``.  When a button changes state,
    it calls ``on_button_change(button, is_pressed)`` on whichever thread
    the callback runs on — callers should dispatch to their own thread if
    needed.  ``ActionRouter`` handles this via its own thread-safe queue.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import Callable

from ..constants import Controller
from ..core.gamepad_button import GamepadButton

logger = logging.getLogger(__name__)

# Callback type: (button, is_pressed)
ButtonChangeCallback = Callable[[GamepadButton, bool], None]


class ControllerManager:
    """
    Manages controller discovery and input translation.

    Usage::

        def on_button(button, is_pressed):
            if is_pressed:
                router.button_pressed(button)
            else:
                router.button_released(button)

        mgr = ControllerManager(on_button_change=on_button)
        mgr.start()   # non-blocking; starts background poll thread
    """

    def __init__(self, on_button_change: ButtonChangeCallback) -> None:
        self._on_button_change = on_button_change
        self._connected = False
        self._poll_thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        return self._connected

    def start(self) -> None:
        """Start the background polling thread. Non-blocking."""
        self._poll_thread = threading.Thread(
            target=self._run,
            daemon=True,
            name="ControllerPollThread",
        )
        self._poll_thread.start()
        logger.info("ControllerManager: poll thread started")

    # ------------------------------------------------------------------
    # Private: poll loop
    # ------------------------------------------------------------------

    def _run(self) -> None:
        """
        Entry point for the poll thread.

        Initialises pygame with a dummy video driver (no display needed),
        then loops forever processing joystick events.
        """
        # Prevent pygame from creating a window or grabbing audio.
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

        import pygame  # imported here so the dummy env vars are set first

        pygame.init()
        pygame.joystick.init()

        joystick: pygame.joystick.JoystickType | None = None

        logger.info("ControllerManager: pygame initialised, waiting for controller…")

        while True:
            # -- Controller connect / disconnect ---------------------------
            count = pygame.joystick.get_count()
            if count > 0 and joystick is None:
                joystick = pygame.joystick.Joystick(0)
                joystick.init()
                self._connected = True
                logger.info("Controller connected: %s", joystick.get_name())

            elif count == 0 and joystick is not None:
                joystick = None
                self._connected = False
                logger.info("Controller disconnected")

            # -- Event processing -----------------------------------------
            for event in pygame.event.get():
                if joystick is None:
                    continue

                if event.type == pygame.JOYBUTTONDOWN:
                    button = _button_from_index(event.button)
                    if button:
                        self._on_button_change(button, True)

                elif event.type == pygame.JOYBUTTONUP:
                    button = _button_from_index(event.button)
                    if button:
                        self._on_button_change(button, False)

                elif event.type == pygame.JOYHATMOTION:
                    # D-pad arrives as hat events: value is (x, y)
                    button = _button_from_hat(event.value)
                    if button:
                        # Hat gives us direction, not press/release.
                        # Treat (0,0) (centred) as release of all d-pad buttons,
                        # any other value as press of the corresponding button.
                        is_pressed = event.value != (0, 0)
                        self._on_button_change(button, is_pressed)

                elif event.type == pygame.JOYAXISMOTION:
                    # Some firmware versions expose L2/R2 as axes (−1 to +1).
                    button = _trigger_from_axis(event.axis, event.value)
                    if button:
                        is_pressed = event.value >= Controller.TRIGGER_PRESS_THRESHOLD
                        self._on_button_change(button, is_pressed)

            time.sleep(Controller.POLL_INTERVAL_SECONDS)


# ---------------------------------------------------------------------------
# Hardware mapping helpers
#
# These translate raw pygame indices/values → typed GamepadButton enums.
# If your controller feels wrong, run:
#   python -m pocket_study_remote.tools.button_logger
# and update the indices here.
# ---------------------------------------------------------------------------

_BUTTON_INDEX_MAP: dict[int, GamepadButton] = {
    Controller.ButtonIndex.A:      GamepadButton.A,
    Controller.ButtonIndex.B:      GamepadButton.B,
    Controller.ButtonIndex.X:      GamepadButton.X,
    Controller.ButtonIndex.Y:      GamepadButton.Y,
    Controller.ButtonIndex.L1:     GamepadButton.LEFT_SHOULDER,
    Controller.ButtonIndex.R1:     GamepadButton.RIGHT_SHOULDER,
    Controller.ButtonIndex.L2:     GamepadButton.LEFT_TRIGGER,
    Controller.ButtonIndex.R2:     GamepadButton.RIGHT_TRIGGER,
    Controller.ButtonIndex.SELECT: GamepadButton.SELECT,
    Controller.ButtonIndex.START:  GamepadButton.START,
}

_HAT_DIRECTION_MAP: dict[tuple[int, int], GamepadButton] = {
    Controller.HatDirection.UP:    GamepadButton.DPAD_UP,
    Controller.HatDirection.DOWN:  GamepadButton.DPAD_DOWN,
    Controller.HatDirection.LEFT:  GamepadButton.DPAD_LEFT,
    Controller.HatDirection.RIGHT: GamepadButton.DPAD_RIGHT,
}

_TRIGGER_AXIS_MAP: dict[int, GamepadButton] = {
    Controller.AxisIndex.LEFT_TRIGGER:  GamepadButton.LEFT_TRIGGER,
    Controller.AxisIndex.RIGHT_TRIGGER: GamepadButton.RIGHT_TRIGGER,
}


def _button_from_index(index: int) -> GamepadButton | None:
    result = _BUTTON_INDEX_MAP.get(index)
    if result is None:
        logger.debug("Unrecognised button index %d — add to ButtonIndex in constants.py", index)
    return result


def _button_from_hat(value: tuple[int, int]) -> GamepadButton | None:
    if value == (0, 0):
        # Centre position — caller handles as "release all d-pad buttons".
        # Return a sentinel so the caller knows to release the last direction.
        return GamepadButton.DPAD_UP   # will be overridden by is_pressed=False logic
    return _HAT_DIRECTION_MAP.get(value)


def _trigger_from_axis(axis: int, value: float) -> GamepadButton | None:
    return _TRIGGER_AXIS_MAP.get(axis)
