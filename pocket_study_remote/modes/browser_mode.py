from __future__ import annotations

from ..core.action import Action, keystroke
from ..core.app_mode import AppMode
from ..core.button_combo import ButtonCombo
from ..core.gamepad_button import GamepadButton


class BrowserMode(AppMode):
    """
    Active when any Chromium-family browser is frontmost.

    Covers Comet, Chrome, Arc, Edge, Brave — all share identical keyboard
    shortcuts so one mode handles them all.

    Combo:  A + B = Bookmark page (Cmd+D).
    A alone fires "new tab"; B alone fires "go back".
    When B is pressed while A is held, the combo fires bookmark instead.
    """

    id             = "browser"
    display_name   = "Browser"
    sf_symbol_name = "globe"

    @property
    def button_map(self) -> dict[GamepadButton, Action]:
        return {
            # ── Face buttons ──────────────────────────────────────────
            GamepadButton.A: keystroke(
                "t", ["cmd"],
                id="browser-new-tab",
                name="New Tab",
            ),
            # B alone = back. B while A is held = bookmark (see combo_map).
            GamepadButton.B: keystroke(
                "left_bracket", ["cmd"],
                id="browser-go-back",
                name="Go Back",
            ),
            GamepadButton.X: keystroke(
                "w", ["cmd"],
                id="browser-close-tab",
                name="Close Tab",
            ),
            GamepadButton.Y: keystroke(
                "t", ["cmd", "shift"],
                id="browser-reopen-tab",
                name="Reopen Closed Tab",
            ),

            # ── D-pad ─────────────────────────────────────────────────
            GamepadButton.DPAD_LEFT: keystroke(
                "left_bracket", ["cmd"],
                id="browser-back",
                name="Page Back",
            ),
            GamepadButton.DPAD_RIGHT: keystroke(
                "right_bracket", ["cmd"],
                id="browser-forward",
                name="Page Forward",
            ),
            GamepadButton.DPAD_UP: keystroke(
                "page_up",
                id="browser-scroll-up",
                name="Scroll Up",
            ),
            GamepadButton.DPAD_DOWN: keystroke(
                "page_down",
                id="browser-scroll-down",
                name="Scroll Down",
            ),

            # ── Shoulder buttons (tab cycling) ────────────────────────
            GamepadButton.LEFT_SHOULDER: keystroke(
                "left_bracket", ["cmd", "shift"],
                id="browser-prev-tab",
                name="Previous Tab",
            ),
            GamepadButton.RIGHT_SHOULDER: keystroke(
                "right_bracket", ["cmd", "shift"],
                id="browser-next-tab",
                name="Next Tab",
            ),

            # ── Triggers ─────────────────────────────────────────────
            GamepadButton.LEFT_TRIGGER: keystroke(
                "n", ["cmd"],
                id="browser-new-window",
                name="New Window",
            ),
            # Cmd+Shift+A = tab search in Chrome / Comet / Arc
            GamepadButton.RIGHT_TRIGGER: keystroke(
                "a", ["cmd", "shift"],
                id="browser-tab-search",
                name="Search Tabs",
            ),

            # ── Menu buttons ──────────────────────────────────────────
            GamepadButton.START: keystroke(
                "l", ["cmd"],
                id="browser-focus-address-bar",
                name="Focus Address Bar",
            ),
            # SELECT unassigned in V1
        }

    @property
    def combo_map(self) -> dict[ButtonCombo, Action]:
        return {
            # A + B together = Bookmark (Cmd+D)
            ButtonCombo(GamepadButton.A, GamepadButton.B): keystroke(
                "d", ["cmd"],
                id="browser-bookmark",
                name="Bookmark Page",
            ),
        }
