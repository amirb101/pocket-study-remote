from __future__ import annotations

from ..constants import BundleID, Spotify
from ..core.action import Action, apple_script, keystroke, open_app
from ..core.configurable_mode import ConfigurableMode
from ..executors.applescript_executor import AppleScriptExecutor


class SpotifyMode(ConfigurableMode):
    """
    Active when Spotify is the frontmost application.

    All playback actions use Spotify's AppleScript dictionary — fully
    reliable and background-safe.

    Buttons are configurable via Edit Keybindings.
    """

    id             = "spotify"
    display_name   = "Spotify"
    sf_symbol_name = "music.note"

    def _create_action_from_id(self, action_id: str) -> Action | None:
        """Create action from ID."""
        action_map = {
            "play_pause": apple_script(
                AppleScriptExecutor.Spotify.PLAYPAUSE,
                id="spotify-play-pause",
                name="Play / Pause",
            ),
            "next_track": apple_script(
                AppleScriptExecutor.Spotify.NEXT_TRACK,
                id="spotify-next-track",
                name="Next Track",
            ),
            "prev_track": apple_script(
                AppleScriptExecutor.Spotify.PREVIOUS_TRACK,
                id="spotify-previous-track",
                name="Previous Track",
            ),
            "volume_up": apple_script(
                AppleScriptExecutor.Spotify.adjust_volume(Spotify.VOLUME_STEP),
                id="spotify-volume-up",
                name="Volume Up",
            ),
            "volume_down": apple_script(
                AppleScriptExecutor.Spotify.adjust_volume(-Spotify.VOLUME_STEP),
                id="spotify-volume-down",
                name="Volume Down",
            ),
            "seek_forward": apple_script(
                AppleScriptExecutor.Spotify.seek_relative(Spotify.SEEK_STEP_SECONDS),
                id="spotify-seek-forward",
                name="Seek Forward",
            ),
            "seek_backward": apple_script(
                AppleScriptExecutor.Spotify.seek_relative(-Spotify.SEEK_STEP_SECONDS),
                id="spotify-seek-backward",
                name="Seek Backward",
            ),
            "shuffle": apple_script(
                AppleScriptExecutor.Spotify.TOGGLE_SHUFFLE,
                id="spotify-toggle-shuffle",
                name="Toggle Shuffle",
            ),
            "like": keystroke(
                "s", ["cmd"],
                id="spotify-save-track",
                name="Save Track to Library",
            ),
            "focus": open_app(
                BundleID.SPOTIFY,
                id="spotify-focus",
                name="Focus Spotify",
            ),
        }
        return action_map.get(action_id)
