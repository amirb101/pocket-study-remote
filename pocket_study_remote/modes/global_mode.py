from __future__ import annotations

from ..constants import BundleID, Volume
from ..core.action import (
    Action,
    adjust_volume,
    apple_script,
    keystroke,
    open_app,
    screenshot,
    switch_space,
    toggle_mute,
)
from ..core.app_mode import AppMode
from ..core.gamepad_button import GamepadButton
from ..executors.applescript_executor import AppleScriptExecutor


class GlobalMode(AppMode):
    """
    Fallback mode — active whenever no specific app is matched.

    Provides universally useful controls: music playback, volume,
    system navigation, and quick app launchers.  Every action here
    should feel natural to press without looking at the screen.
    """

    id             = "global"
    display_name   = "Global"
    sf_symbol_name = "gamecontroller"

    @property
    def button_map(self) -> dict[GamepadButton, Action]:
        return {
            # ── Face buttons ──────────────────────────────────────────
            GamepadButton.A: apple_script(
                AppleScriptExecutor.Spotify.PLAYPAUSE,
                id="global-play-pause",
                name="Play / Pause",
            ),
            GamepadButton.B: toggle_mute(
                id="global-toggle-mute",
                name="Toggle Mute",
            ),
            GamepadButton.X: screenshot(
                region=True,
                id="global-screenshot-region",
                name="Screenshot (Region)",
            ),
            GamepadButton.Y: screenshot(
                region=False,
                id="global-screenshot-full",
                name="Screenshot (Full Screen)",
            ),

            # ── D-pad ─────────────────────────────────────────────────
            GamepadButton.DPAD_UP: adjust_volume(
                Volume.STEP_SIZE,
                id="global-volume-up",
                name="Volume Up",
            ),
            GamepadButton.DPAD_DOWN: adjust_volume(
                -Volume.STEP_SIZE,
                id="global-volume-down",
                name="Volume Down",
            ),
            GamepadButton.DPAD_LEFT: apple_script(
                AppleScriptExecutor.Spotify.PREVIOUS_TRACK,
                id="global-previous-track",
                name="Previous Track",
            ),
            GamepadButton.DPAD_RIGHT: apple_script(
                AppleScriptExecutor.Spotify.NEXT_TRACK,
                id="global-next-track",
                name="Next Track",
            ),

            # ── Shoulder buttons ──────────────────────────────────────
            GamepadButton.LEFT_SHOULDER: switch_space(
                "left",
                id="global-space-left",
                name="Switch Space Left",
            ),
            GamepadButton.RIGHT_SHOULDER: switch_space(
                "right",
                id="global-space-right",
                name="Switch Space Right",
            ),

            # ── Triggers ─────────────────────────────────────────────
            GamepadButton.LEFT_TRIGGER: keystroke(
                "up_arrow", ["ctrl"],
                id="global-mission-control",
                name="Mission Control",
            ),
            # RIGHT_TRIGGER intentionally unassigned in V1

            # ── Menu buttons ──────────────────────────────────────────
            GamepadButton.START: open_app(
                BundleID.OBSIDIAN,
                id="global-open-obsidian",
                name="Open Obsidian",
            ),
            GamepadButton.SELECT: open_app(
                BundleID.SPOTIFY,
                id="global-open-spotify",
                name="Open Spotify",
            ),
        }
