"""
AppMode subclass that reads keybindings from configuration.

This allows users to customize button mappings via the GUI editor.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .app_mode import AppMode
from .action import Action, keystroke
from .button_combo import ButtonCombo
from .gamepad_button import GamepadButton

if TYPE_CHECKING:
    from ..config.keybind_config import ModeConfig


class ConfigurableMode(AppMode):
    """
    A mode that reads its button mappings from the keybinding configuration.

    Subclasses define their available actions, and the actual button mappings
    are loaded from the user's config file.
    """

    @property
    def config_mode_id(self) -> str:
        """The mode ID in the configuration file."""
        return self.id

    def _get_mode_config(self) -> ModeConfig | None:
        """Get the configuration for this mode."""
        from ..config.keybind_config import get_config
        return get_config().get_mode(self.config_mode_id)

    def _action_to_keystroke(self, action_id: str) -> Action:
        """Convert an action ID to an Action. Override in subclasses."""
        # Default: just press a key (subclasses should override)
        return keystroke("a", id=action_id, name=action_id)

    @property
    def button_map(self) -> dict[GamepadButton, Action]:
        """Build button map from configuration."""
        result: dict[GamepadButton, Action] = {}
        mode_config = self._get_mode_config()
        if not mode_config:
            return result

        for mapping in mode_config.mappings:
            # Only handle simple presses in button_map
            if mapping.input_type.value != "simple":
                continue
            if not mapping.button:
                continue

            action = mode_config.get_action_by_id(mapping.action_id)
            if not action:
                continue

            # Convert to keystroke action
            keystroke_action = self._create_action_from_id(mapping.action_id)
            if keystroke_action:
                result[mapping.button] = keystroke_action

        return result

    @property
    def combo_map(self) -> dict[ButtonCombo, Action]:
        """Build combo map from configuration."""
        result: dict[ButtonCombo, Action] = {}
        mode_config = self._get_mode_config()
        if not mode_config:
            return result

        for mapping in mode_config.mappings:
            # Only handle combos
            if mapping.input_type.value != "combo":
                continue
            if not mapping.primary_button or not mapping.held_buttons:
                continue

            action = mode_config.get_action_by_id(mapping.action_id)
            if not action:
                continue

            # Create combo
            combo = ButtonCombo(mapping.primary_button, *mapping.held_buttons)
            keystroke_action = self._create_action_from_id(mapping.action_id)
            if keystroke_action:
                result[combo] = keystroke_action

        return result

    def _create_action_from_id(self, action_id: str) -> Action | None:
        """
        Create an Action from an action ID.
        Subclasses should override this to provide the actual keystrokes.
        """
        raise NotImplementedError("Subclasses must implement _create_action_from_id")
