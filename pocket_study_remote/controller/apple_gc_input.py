"""
Gamepad input via Apple's GameController framework (macOS).

This does **not** use pygame/SDL for discovery, so it works alongside rumps
without opening an SDL Cocoa window (which aborts when NSApplication already
exists — see ``sdl_bootstrap``).

Polls ``GCExtendedGamepad`` on a background thread at ~60 Hz and emits the
same ``GamepadButton`` events as :class:`ControllerManager`.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Callable

from ..constants import Controller
from ..core.gamepad_button import GamepadButton

logger = logging.getLogger(__name__)

ButtonChangeCallback = Callable[[GamepadButton, bool], None]

_TH = Controller.TRIGGER_PRESS_THRESHOLD


def _objc_prop(obj, name: str):
    if obj is None:
        return None
    a = getattr(obj, name, None)
    if a is None:
        return None
    return a() if callable(a) else a


def _btn_press(inp) -> bool:
    if inp is None:
        return False
    try:
        return bool(inp.isPressed())
    except Exception:
        return False


def _axis(inp) -> float:
    if inp is None:
        return 0.0
    try:
        v = inp.value()
        return float(v) if v is not None else 0.0
    except Exception:
        pass
    try:
        return float(inp.value)
    except Exception:
        return 0.0


class AppleGCControllerInput:
    """
    Same responsibilities as ``ControllerManager`` (pygame), different backend.

    Use on macOS when SDL dummy video reports zero joysticks.
    """

    def __init__(self, on_button_change: ButtonChangeCallback) -> None:
        self._cb = on_button_change
        self._connected = False
        self._last: dict[GamepadButton, bool] = {}
        self._logged_name = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def start(self) -> None:
        threading.Thread(target=self._run, daemon=True, name="AppleGCInput").start()
        logger.info("AppleGCControllerInput: thread started (GameController.framework)")

    def _run(self) -> None:
        from GameController import GCController

        def discovery_done(err) -> None:
            if err is not None:
                logger.debug("GC wireless discovery done: %s", err)

        try:
            GCController.startWirelessControllerDiscoveryWithCompletionHandler_(discovery_done)
        except Exception as e:
            logger.debug("startWirelessControllerDiscovery: %s", e)

        time.sleep(0.25)

        while True:
            try:
                self._poll(GCController)
            except Exception as e:
                logger.debug("GameController poll: %s", e)
            time.sleep(Controller.POLL_INTERVAL_SECONDS)

    def _pick_controller(self, GCController):
        for c in GCController.controllers():
            pad = _objc_prop(c, "extendedGamepad")
            if pad is None:
                pad = _objc_prop(c, "gamepad")
            if pad is not None:
                return c, pad
        return None, None

    def _poll(self, GCController) -> None:
        ctrl, pad = self._pick_controller(GCController)
        was_connected = self._connected
        self._connected = pad is not None

        if not self._connected:
            if was_connected:
                logger.info("GameController disconnected")
            for b, prev in list(self._last.items()):
                if prev:
                    self._cb(b, False)
            self._last.clear()
            self._logged_name = False
            return

        if not self._logged_name:
            self._logged_name = True
            name = _objc_prop(ctrl, "vendorName") or "controller"
            logger.info("GameController connected: %s", name)

        dpad = _objc_prop(pad, "dpad")
        state: dict[GamepadButton, bool] = {
            GamepadButton.A: _btn_press(_objc_prop(pad, "buttonA")),
            GamepadButton.B: _btn_press(_objc_prop(pad, "buttonB")),
            GamepadButton.X: _btn_press(_objc_prop(pad, "buttonX")),
            GamepadButton.Y: _btn_press(_objc_prop(pad, "buttonY")),
            GamepadButton.LEFT_SHOULDER: _btn_press(_objc_prop(pad, "leftShoulder")),
            GamepadButton.RIGHT_SHOULDER: _btn_press(_objc_prop(pad, "rightShoulder")),
            GamepadButton.LEFT_TRIGGER: _axis(_objc_prop(pad, "leftTrigger")) >= _TH,
            GamepadButton.RIGHT_TRIGGER: _axis(_objc_prop(pad, "rightTrigger")) >= _TH,
            GamepadButton.DPAD_UP: _btn_press(_objc_prop(dpad, "up")),
            GamepadButton.DPAD_DOWN: _btn_press(_objc_prop(dpad, "down")),
            GamepadButton.DPAD_LEFT: _btn_press(_objc_prop(dpad, "left")),
            GamepadButton.DPAD_RIGHT: _btn_press(_objc_prop(dpad, "right")),
        }
        state[GamepadButton.START] = _btn_press(_objc_prop(pad, "buttonMenu"))
        state[GamepadButton.SELECT] = _btn_press(_objc_prop(pad, "buttonOptions"))

        for btn, pressed in state.items():
            prev = self._last.get(btn, False)
            if pressed != prev:
                self._cb(btn, pressed)
        self._last = dict(state)
