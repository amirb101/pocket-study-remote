"""
Gamepad input via Apple's GameController framework (macOS).

This does **not** use pygame/SDL for discovery, so it works alongside rumps
without opening an SDL Cocoa window (which aborts when NSApplication already
exists — see ``sdl_bootstrap``).

Polls on the **main run loop** (``NSTimer``) so ``GCController`` sees devices
the same way a normal AppKit app does. Sets ``shouldMonitorBackgroundEvents``
so input keeps flowing when the menu bar app is not the key app (macOS 11.3+).

Emits the same ``GamepadButton`` events as :class:`ControllerManager`.
"""

from __future__ import annotations

import logging
import time
from typing import Callable

from Foundation import NSTimer

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

    Uses GameController on the main thread; enable background monitoring so
    the pad works while you use other apps.
    """

    def __init__(self, on_button_change: ButtonChangeCallback) -> None:
        self._cb = on_button_change
        self._connected = False
        self._last: dict[GamepadButton, bool] = {}
        self._logged_name = False
        self._timer: NSTimer | None = None
        self._last_empty_log = 0.0

    @property
    def is_connected(self) -> bool:
        return self._connected

    def start(self) -> None:
        """Schedule polling on the main run loop (call from AppKit main thread)."""
        from GameController import GCController

        try:
            GCController.setShouldMonitorBackgroundEvents_(True)
        except Exception as e:
            logger.debug("setShouldMonitorBackgroundEvents: %s", e)

        def discovery_done(err) -> None:
            if err is not None:
                logger.debug("GC wireless discovery completion: %s", err)

        try:
            GCController.startWirelessControllerDiscoveryWithCompletionHandler_(discovery_done)
        except Exception as e:
            logger.debug("startWirelessControllerDiscovery: %s", e)

        def stop_discovery(_timer) -> None:
            try:
                GCController.stopWirelessControllerDiscovery()
            except Exception as e:
                logger.debug("stopWirelessControllerDiscovery: %s", e)

        try:
            NSTimer.scheduledTimerWithTimeInterval_repeats_block_(
                8.0,
                False,
                stop_discovery,
            )
        except Exception as e:
            logger.debug("schedule stopWirelessControllerDiscovery: %s", e)

        self._GCController = GCController
        try:
            self._poll(GCController)
        except Exception as e:
            logger.debug("GameController initial poll: %s", e)

        def tick(_timer) -> None:
            try:
                self._poll(GCController)
            except Exception as e:
                logger.debug("GameController poll: %s", e)

        self._timer = NSTimer.scheduledTimerWithTimeInterval_repeats_block_(
            Controller.POLL_INTERVAL_SECONDS,
            True,
            tick,
        )
        logger.info(
            "AppleGCControllerInput: main-runloop timer started (~%.0f Hz, background GC input on)",
            1.0 / Controller.POLL_INTERVAL_SECONDS,
        )

    def _pick_controller(self, GCController):
        for c in GCController.controllers():
            pad = _objc_prop(c, "extendedGamepad")
            if pad is not None:
                return c, pad, "extended"
            pad = _objc_prop(c, "gamepad")
            if pad is not None:
                return c, pad, "extended"
            pad = _objc_prop(c, "microGamepad")
            if pad is not None:
                return c, pad, "micro"
        return None, None, None

    def _poll(self, GCController) -> None:
        ctrl, pad, kind = self._pick_controller(GCController)
        n = len(GCController.controllers())
        if n == 0:
            now = time.monotonic()
            if now - self._last_empty_log >= 45.0:
                self._last_empty_log = now
                logger.info(
                    "GameController: no devices yet (pair in Bluetooth; if already paired, "
                    "toggle Bluetooth off/on or disconnect/reconnect the controller once). "
                    "8BitDo: try **X** or **Switch** mode if **D** does not show up here."
                )

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
            logger.info("GameController connected: %s (profile=%s)", name, kind)

        if kind == "micro":
            self._poll_micro(pad)
        else:
            self._poll_extended(pad)

    def _poll_micro(self, pad) -> None:
        dpad = _objc_prop(pad, "dpad")
        state: dict[GamepadButton, bool] = {
            GamepadButton.A: _btn_press(_objc_prop(pad, "buttonA")),
            GamepadButton.B: False,
            GamepadButton.X: _btn_press(_objc_prop(pad, "buttonX")),
            GamepadButton.Y: False,
            GamepadButton.LEFT_SHOULDER: False,
            GamepadButton.RIGHT_SHOULDER: False,
            GamepadButton.LEFT_TRIGGER: False,
            GamepadButton.RIGHT_TRIGGER: False,
            GamepadButton.DPAD_UP: _btn_press(_objc_prop(dpad, "up")),
            GamepadButton.DPAD_DOWN: _btn_press(_objc_prop(dpad, "down")),
            GamepadButton.DPAD_LEFT: _btn_press(_objc_prop(dpad, "left")),
            GamepadButton.DPAD_RIGHT: _btn_press(_objc_prop(dpad, "right")),
            GamepadButton.START: _btn_press(_objc_prop(pad, "buttonMenu")),
            GamepadButton.SELECT: False,
        }
        self._emit_changes(state)

    def _poll_extended(self, pad) -> None:
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
            GamepadButton.START: _btn_press(_objc_prop(pad, "buttonMenu")),
            GamepadButton.SELECT: _btn_press(_objc_prop(pad, "buttonOptions")),
        }
        self._emit_changes(state)

    def _emit_changes(self, state: dict[GamepadButton, bool]) -> None:
        for btn, pressed in state.items():
            prev = self._last.get(btn, False)
            if pressed != prev:
                self._cb(btn, pressed)
        self._last = dict(state)
