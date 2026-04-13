"""
Controller calibration - maps physical button aliases to logical GamepadButtons.

Stores per-controller mappings so Nintendo/Xbox/generic layouts all work correctly.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from ..core.gamepad_button import GamepadButton

logger = logging.getLogger(__name__)

# Buttons to calibrate in order (logical names)
CALIBRATION_ORDER = [
    GamepadButton.DPAD_UP,
    GamepadButton.DPAD_DOWN,
    GamepadButton.DPAD_LEFT,
    GamepadButton.DPAD_RIGHT,
    GamepadButton.A,
    GamepadButton.B,
    GamepadButton.X,
    GamepadButton.Y,
    GamepadButton.LEFT_SHOULDER,
    GamepadButton.RIGHT_SHOULDER,
    GamepadButton.LEFT_TRIGGER,
    GamepadButton.RIGHT_TRIGGER,
    GamepadButton.START,
    GamepadButton.SELECT,
]


@dataclass
class ControllerMapping:
    """Maps physical button aliases to logical GamepadButtons."""

    controller_name: str
    # Map: physical alias (lowercase normalized) -> logical GamepadButton
    alias_to_button: dict[str, GamepadButton] = field(default_factory=dict)
    is_complete: bool = False

    def get_button(self, alias: str) -> GamepadButton | None:
        """Get logical button for a physical alias (case-insensitive)."""
        normalized = "".join(c.lower() for c in alias if c.isalnum())
        return self.alias_to_button.get(normalized)


class CalibrationStore:
    """Persistent storage for controller mappings."""

    def __init__(self) -> None:
        self._path = Path.home() / ".config" / "pocket-study-remote" / "controller_mappings.json"
        self._cache: dict[str, ControllerMapping] = {}
        self._lock = threading.Lock()
        self._load()

    def _load(self) -> None:
        """Load mappings from disk."""
        if not self._path.exists():
            return
        try:
            with open(self._path, "r") as f:
                data = json.load(f)
            for name, mapping_data in data.items():
                alias_map = {
                    k: GamepadButton[v] for k, v in mapping_data.get("aliases", {}).items()
                }
                self._cache[name] = ControllerMapping(
                    controller_name=name,
                    alias_to_button=alias_map,
                    is_complete=mapping_data.get("is_complete", False),
                )
            logger.info("Loaded %d controller mappings from %s", len(self._cache), self._path)
        except Exception as e:
            logger.warning("Failed to load controller mappings: %s", e)

    def _save(self) -> None:
        """Save mappings to disk."""
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                name: {
                    "aliases": {k: v.name for k, v in mapping.alias_to_button.items()},
                    "is_complete": mapping.is_complete,
                }
                for name, mapping in self._cache.items()
            }
            with open(self._path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning("Failed to save controller mappings: %s", e)

    def get_mapping(self, controller_name: str) -> ControllerMapping | None:
        """Get stored mapping for a controller, or None if not calibrated."""
        with self._lock:
            return self._cache.get(controller_name)

    def needs_calibration(self, controller_name: str) -> bool:
        """Check if controller needs calibration (new or incomplete)."""
        with self._lock:
            mapping = self._cache.get(controller_name)
            return mapping is None or not mapping.is_complete

    def save_mapping(self, mapping: ControllerMapping) -> None:
        """Save a completed mapping."""
        with self._lock:
            self._cache[mapping.controller_name] = mapping
            self._save()

    def clear_mapping(self, controller_name: str) -> None:
        """Clear mapping for a controller (force recalibration)."""
        with self._lock:
            if controller_name in self._cache:
                del self._cache[controller_name]
                self._save()

    def get_all_controller_names(self) -> list[str]:
        """Get list of all calibrated controller names."""
        with self._lock:
            return list(self._cache.keys())


# Global store instance
_store: CalibrationStore | None = None


def get_store() -> CalibrationStore:
    """Get the global calibration store."""
    global _store
    if _store is None:
        _store = CalibrationStore()
    return _store


class CalibrationWizard:
    """
    Interactive calibration using rumps alerts (no tkinter needed).

    Guides user through pressing each button in sequence.
    """

    def __init__(
        self,
        controller_name: str,
        on_complete: Callable[[ControllerMapping], None],
        on_cancel: Callable[[], None],
    ) -> None:
        self.controller_name = controller_name
        self.on_complete = on_complete
        self.on_cancel = on_cancel
        self.mapping = ControllerMapping(controller_name=controller_name)
        self.current_index = 0
        self.detected_aliases: set[str] = set()
        self._active = False
        self._last_press_time = 0.0

    def start(self) -> None:
        """Start the calibration wizard."""
        import rumps

        self._active = True
        self._show_current_prompt()

    def _show_current_prompt(self) -> None:
        """Show prompt for current button using rumps alert."""
        import rumps

        if not self._active or self.current_index >= len(CALIBRATION_ORDER):
            return

        btn = CALIBRATION_ORDER[self.current_index]
        progress = f"{self.current_index + 1}/{len(CALIBRATION_ORDER)}"

        rumps.alert(
            title=f"Controller Calibration ({progress})",
            message=f'Press "{btn.display_name}" on your controller\n\n'
                    f"Then click OK to confirm",
            ok="I pressed it",
            cancel="Cancel",
        )

        # After alert closes, continue or cancel
        # Note: rumps.alert is synchronous, so we check if still active
        if not self._active:
            return

        # Move to next
        self.current_index += 1
        if self.current_index >= len(CALIBRATION_ORDER):
            self._finish()
        else:
            # Schedule next prompt
            import threading
            threading.Timer(0.1, self._show_current_prompt).start()

    def on_button_event(self, alias: str, is_pressed: bool) -> bool:
        """
        Called when a button is pressed during calibration.
        Returns True if this button was consumed (should not propagate).
        """
        if not self._active or not is_pressed:
            return False
        if self.current_index >= len(CALIBRATION_ORDER):
            return False

        # Debounce
        now = time.time()
        if now - self._last_press_time < 0.2:
            return False
        self._last_press_time = now

        normalized = "".join(c.lower() for c in alias if c.isalnum())
        if normalized in self.detected_aliases:
            return True  # Already mapped, consume but don't re-add

        # Map this physical alias to the current logical button
        logical_button = CALIBRATION_ORDER[self.current_index]
        self.mapping.alias_to_button[normalized] = logical_button
        self.detected_aliases.add(normalized)

        logger.info("[Calibration] Mapped %s -> %s", alias, logical_button.name)

        # Advance to next
        self.current_index += 1
        if self.current_index >= len(CALIBRATION_ORDER):
            self._finish()
        return True

    def _finish(self) -> None:
        """Complete calibration."""
        import rumps

        self._active = False
        self.mapping.is_complete = True
        get_store().save_mapping(self.mapping)

        rumps.alert(
            title="Calibration Complete!",
            message=f"Controller '{self.controller_name}' has been calibrated.\n"
                    f"Mapped {len(self.mapping.alias_to_button)} buttons.",
            ok="Great!",
        )
        self.on_complete(self.mapping)

    def cancel(self) -> None:
        """Cancel calibration."""
        self._active = False
        self.on_cancel()
