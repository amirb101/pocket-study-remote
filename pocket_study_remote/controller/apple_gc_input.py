"""
Gamepad input via Apple's GameController framework (macOS).

This does **not** use pygame/SDL for discovery, so it works alongside rumps
without opening an SDL Cocoa window (which aborts when NSApplication already
exists — see ``sdl_bootstrap``).

Polls on the **main run loop** via ``NSTimer`` in **NSRunLoopCommonModes** so
ticks still fire while the status-item menu is tracking the mouse (default
mode timers often do not).

Uses ``extendedGamepad`` / ``gamepad`` / ``microGamepad`` when present; many
Bluetooth pads (DualSense, some 8BitDo modes) only expose **physicalInputProfile**
— we map aliases from ``allButtons`` / ``allAxes`` / ``allDpads`` to
``GamepadButton``.

``shouldMonitorBackgroundEvents`` keeps input flowing when other apps are key.
"""

from __future__ import annotations

import logging
import time
from typing import Callable

from Foundation import NSRunLoop, NSRunLoopCommonModes, NSTimer

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


def _norm_alias(s: str) -> str:
    return "".join(c.lower() for c in s if c.isalnum())


def _physical_alias_to_face_or_menu(n: str) -> GamepadButton | None:
    """Map GCPhysicalInputProfile button primaryAlias / localizedName → enum."""
    # D-pad (often separate digital elements)
    if "dpadup" in n or n == "up" and "dpad" in n:
        return GamepadButton.DPAD_UP
    if "dpaddown" in n or (n == "down" and "dpad" in n):
        return GamepadButton.DPAD_DOWN
    if "dpadleft" in n:
        return GamepadButton.DPAD_LEFT
    if "dpadright" in n:
        return GamepadButton.DPAD_RIGHT
    # Shoulders (before generic "left"/"right")
    if "leftshoulder" in n or "l1" == n or n.endswith("l1button"):
        return GamepadButton.LEFT_SHOULDER
    if "rightshoulder" in n or "r1" == n or n.endswith("r1button"):
        return GamepadButton.RIGHT_SHOULDER
    # Face — Xbox names
    if "buttona" in n or n == "a" or "buttoncross" in n or "cross" == n or "crossbutton" in n:
        return GamepadButton.A
    if "buttonb" in n or n == "b" or "buttoncircle" in n or "circle" == n or "circlebutton" in n:
        return GamepadButton.B
    if "buttonx" in n or n == "x" or "buttonsquare" in n or "square" == n or "squarebutton" in n:
        return GamepadButton.X
    if "buttony" in n or n == "y" or "buttontriangle" in n or "triangle" == n or "trianglebutton" in n:
        return GamepadButton.Y
    # Menu cluster
    if "buttonmenu" in n or "menu" in n or "start" in n or "home" in n or "logo" in n:
        return GamepadButton.START
    if "buttonoptions" in n or "options" in n or "select" in n or "share" in n or "view" in n or "back" in n:
        return GamepadButton.SELECT
    # Some pads expose L2/R2 as digital "button" elements
    if "lefttrigger" in n or "l2" in n or "lt" == n or "leftz" in n:
        return GamepadButton.LEFT_TRIGGER
    if "righttrigger" in n or "r2" in n or "rt" == n or "rightz" in n:
        return GamepadButton.RIGHT_TRIGGER
    return None


def _physical_alias_axis_to_trigger(n: str) -> GamepadButton | None:
    if "lefttrigger" in n or "l2" in n or n in ("lt", "ltaxis", "leftz"):
        return GamepadButton.LEFT_TRIGGER
    if "righttrigger" in n or "r2" in n or n in ("rt", "rtaxis", "rightz"):
        return GamepadButton.RIGHT_TRIGGER
    if "z" in n and "left" in n and "right" not in n:
        return GamepadButton.LEFT_TRIGGER
    if "z" in n and "right" in n:
        return GamepadButton.RIGHT_TRIGGER
    return None


def _physical_profile_has_inputs(pip) -> bool:
    if pip is None:
        return False
    try:
        b = pip.allButtons()
        if b is not None and b.count() > 0:
            return True
    except Exception:
        pass
    try:
        e = pip.allElements()
        if e is not None and e.count() > 0:
            return True
    except Exception:
        pass
    return False


def _schedule_timer_common_modes(interval: float, repeats: bool, block) -> NSTimer:
    """Like scheduledTimer… but runs during event tracking (status bar menus, drags)."""
    t = NSTimer.timerWithTimeInterval_repeats_block_(interval, repeats, block)
    NSRunLoop.currentRunLoop().addTimer_forMode_(t, NSRunLoopCommonModes)
    return t


class AppleGCControllerInput:
    """
    Same responsibilities as ``ControllerManager`` (pygame), different backend.
    """

    def __init__(self, on_button_change: ButtonChangeCallback) -> None:
        self._cb = on_button_change
        self._connected = False
        self._last: dict[GamepadButton, bool] = {}
        self._logged_name = False
        self._timer: NSTimer | None = None
        self._last_empty_log = 0.0
        self._last_rediscover = 0.0
        self._logged_profile_gap = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def start(self) -> None:
        """Schedule polling on the main run loop (call from AppKit main thread)."""
        logger.info("AppleGCControllerInput.start() entered")
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
            _schedule_timer_common_modes(8.0, False, stop_discovery)
        except Exception as e:
            logger.debug("schedule stopWirelessControllerDiscovery: %s", e)

        self._GCController = GCController
        try:
            self._poll(GCController)
        except Exception as e:
            logger.warning("GameController initial poll failed: %s", e)

        def tick(_timer) -> None:
            try:
                self._poll(GCController)
            except Exception as e:
                logger.warning("GameController poll failed: %s", e)

        self._timer = _schedule_timer_common_modes(
            Controller.POLL_INTERVAL_SECONDS,
            True,
            tick,
        )
        logger.info(
            "AppleGCControllerInput: timer on common run-loop modes (~%.0f Hz); "
            "physicalInputProfile fallback enabled",
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
            pip = _objc_prop(c, "physicalInputProfile")
            if _physical_profile_has_inputs(pip):
                return c, pip, "physical"
        return None, None, None

    def _poll(self, GCController) -> None:
        ctrls = GCController.controllers()
        n = len(ctrls)
        ctrl, pad, kind = self._pick_controller(GCController)

        now = time.monotonic()
        if n == 0:
            if now - self._last_empty_log >= 30.0:
                self._last_empty_log = now
                logger.warning(
                    "GameController: 0 devices. Open **System Settings → Game Controllers** — if the "
                    "pad is not listed, macOS does not expose it to GameController (try **X** or **S** "
                    "mode on 8BitDo, or disconnect/reconnect). This app cannot see pure D-input HID "
                    "pads through Apple’s API."
                )
            if now - self._last_rediscover >= 45.0:
                self._last_rediscover = now
                try:
                    GCController.startWirelessControllerDiscoveryWithCompletionHandler_(
                        lambda err: None,
                    )
                except Exception:
                    pass

        if n > 0 and pad is None and not self._logged_profile_gap:
            self._logged_profile_gap = True
            for c in ctrls:
                vn = _objc_prop(c, "vendorName")
                logger.warning(
                    "GameController sees a device (%r) but no extended/gamepad/micro profile and "
                    "no physicalInputProfile buttons — macOS may not support this device for GC.",
                    vn,
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
            if n == 0:
                self._logged_profile_gap = False
            return

        if not self._logged_name:
            self._logged_name = True
            name = _objc_prop(ctrl, "vendorName") or "controller"
            logger.info("GameController connected: %s (profile=%s)", name, kind)

        if kind == "micro":
            self._poll_micro(pad)
        elif kind == "physical":
            self._poll_physical(pad)
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

    def _poll_physical(self, pip) -> None:
        state: dict[GamepadButton, bool] = {b: False for b in GamepadButton}
        try:
            buttons = pip.allButtons()
            if buttons is not None:
                for i in range(buttons.count()):
                    el = buttons.objectAtIndex_(i)
                    alias = str(
                        _objc_prop(el, "primaryAlias")
                        or _objc_prop(el, "localizedName")
                        or _objc_prop(el, "unmappedLocalizedName")
                        or "",
                    )
                    n = _norm_alias(alias)
                    gpb = _physical_alias_to_face_or_menu(n)
                    if gpb is None:
                        continue
                    if gpb in (GamepadButton.LEFT_TRIGGER, GamepadButton.RIGHT_TRIGGER):
                        if _btn_press(el) or _axis(el) >= _TH:
                            state[gpb] = True
                    elif _btn_press(el):
                        state[gpb] = True
        except Exception as e:
            logger.debug("physical allButtons: %s", e)

        try:
            axes = pip.allAxes()
            if axes is not None:
                for i in range(axes.count()):
                    el = axes.objectAtIndex_(i)
                    alias = str(
                        _objc_prop(el, "primaryAlias")
                        or _objc_prop(el, "localizedName")
                        or "",
                    )
                    gpb = _physical_alias_axis_to_trigger(_norm_alias(alias))
                    if gpb is not None and _axis(el) >= _TH:
                        state[gpb] = True
        except Exception as e:
            logger.debug("physical allAxes: %s", e)

        try:
            dpads = pip.allDpads()
            if dpads is not None:
                for i in range(dpads.count()):
                    dpad = dpads.objectAtIndex_(i)
                    state[GamepadButton.DPAD_UP] |= _btn_press(_objc_prop(dpad, "up"))
                    state[GamepadButton.DPAD_DOWN] |= _btn_press(_objc_prop(dpad, "down"))
                    state[GamepadButton.DPAD_LEFT] |= _btn_press(_objc_prop(dpad, "left"))
                    state[GamepadButton.DPAD_RIGHT] |= _btn_press(_objc_prop(dpad, "right"))
        except Exception as e:
            logger.debug("physical allDpads: %s", e)

        self._emit_changes(state)

    def _emit_changes(self, state: dict[GamepadButton, bool]) -> None:
        for btn, pressed in state.items():
            prev = self._last.get(btn, False)
            if pressed != prev:
                self._cb(btn, pressed)
        self._last = dict(state)
