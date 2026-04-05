from __future__ import annotations

from ..constants import BundleID, Spotify
from ..core.action import Action, apple_script, keystroke, open_app
from ..core.app_mode import AppMode
from ..core.gamepad_button import GamepadButton
from ..executors.applescript_executor import AppleScriptExecutor


class SpotifyMode(AppMode):
    """
    Active when Spotify is the frontmost application.

    All playback actions use Spotify's AppleScript dictionary — fully
    reliable and background-safe (works even when Spotify is not frontmost,
    but this mode only activates when it is).

    Note on Save/Like: Spotify's scripting dictionary does not expose a
    first-class "save track" verb.  We use Cmd+S (Spotify's own shortcut
    for saving to library) instead.
    """

    id             = "spotify"
    display_name   = "Spotify"
    sf_symbol_name = "music.note"

    @property
    def button_map(self) -> dict[GamepadButton, Action]:
        return {
            # ── Face buttons ──────────────────────────────────────────
            GamepadButton.A: apple_script(
                AppleScriptExecutor.Spotify.PLAYPAUSE,
                id="spotify-play-pause",
                name="Play / Pause",
            ),
            # Cmd+S = Spotify's native keyboard shortcut for Save to Library.
            GamepadButton.B: keystroke(
                "s", ["cmd"],
                id="spotify-save-track",
                name="Save Track to Library",
            ),
            GamepadButton.X: apple_script(
                AppleScriptExecutor.Spotify.TOGGLE_SHUFFLE,
                id="spotify-toggle-shuffle",
                name="Toggle Shuffle",
            ),
            GamepadButton.Y: apple_script(
                AppleScriptExecutor.Spotify.TOGGLE_REPEAT,
                id="spotify-toggle-repeat",
                name="Toggle Repeat",
            ),

            # ── D-pad ─────────────────────────────────────────────────
            GamepadButton.DPAD_UP: apple_script(
                AppleScriptExecutor.Spotify.adjust_volume(Spotify.VOLUME_STEP),
                id="spotify-volume-up",
                name="Volume Up",
            ),
            GamepadButton.DPAD_DOWN: apple_script(
                AppleScriptExecutor.Spotify.adjust_volume(-Spotify.VOLUME_STEP),
                id="spotify-volume-down",
                name="Volume Down",
            ),
            GamepadButton.DPAD_LEFT: apple_script(
                AppleScriptExecutor.Spotify.PREVIOUS_TRACK,
                id="spotify-previous-track",
                name="Previous Track",
            ),
            GamepadButton.DPAD_RIGHT: apple_script(
                AppleScriptExecutor.Spotify.NEXT_TRACK,
                id="spotify-next-track",
                name="Next Track",
            ),

            # ── Shoulder buttons (seek) ───────────────────────────────
            GamepadButton.LEFT_SHOULDER: apple_script(
                AppleScriptExecutor.Spotify.seek_relative(-Spotify.SEEK_STEP_SECONDS),
                id="spotify-seek-back",
                name="Seek Back 15s",
            ),
            GamepadButton.RIGHT_SHOULDER: apple_script(
                AppleScriptExecutor.Spotify.seek_relative(Spotify.SEEK_STEP_SECONDS),
                id="spotify-seek-forward",
                name="Seek Forward 15s",
            ),

            # ── Menu buttons ──────────────────────────────────────────
            GamepadButton.START: open_app(
                BundleID.SPOTIFY,
                id="spotify-focus",
                name="Focus Spotify",
            ),
            # SELECT unassigned in V1
        }
