"""Recorded macro implementation for playback of user-defined macros."""

import logging
import threading
from typing import Any, List, Dict

from macro_manager.core.macro import Macro
from macro_manager.core.exceptions import MacroExecutionError

logger = logging.getLogger(__name__)


class RecordedMacro(Macro):
    """A macro created from recorded user actions."""

    def __init__(self, name: str, description: str, actions: List[Dict[str, Any]]):
        """Initialize a recorded macro.

        Args:
            name: Display name of the macro.
            description: Description of what the macro does.
            actions: List of recorded actions to replay.
                Each action is a dict with:
                - type: "keypress", "keyhold", or "sleep"
                - key: key name (for keypress/keyhold)
                - duration: hold duration in seconds (for keyhold)
                - delay: wait time in seconds (for sleep)
        """
        super().__init__(name, description)
        self.actions = actions
        self.loop = True  # Whether to loop the macro
        self.loop_count = None  # None for infinite, integer for specific count

    def set_loop(self, loop: bool, loop_count: int = None) -> None:
        """Set whether the macro should loop and how many times.

        Args:
            loop: True to loop, False to run once.
            loop_count: Number of times to loop (None for infinite, integer for specific count).
        """
        self.loop = loop
        if loop and loop_count is not None and loop_count > 0:
            self.loop_count = loop_count
        else:
            self.loop_count = None

    def run(self, game_window: Any, running: threading.Event) -> None:
        """Execute the recorded macro actions.

        Args:
            game_window: The window handle to send inputs to.
            running: Threading event that controls macro execution.

        Raises:
            MacroExecutionError: If macro execution fails.
        """
        total_steps = len(self.actions)

        # Determine max iterations
        if not self.loop:
            max_iterations = 1
        elif self.loop_count is not None and self.loop_count > 0:
            max_iterations = self.loop_count
        else:
            max_iterations = None  # Infinite

        # Run once or loop
        iteration = 0
        while running.is_set():
            iteration += 1

            # Check if we've reached the max iterations
            if max_iterations is not None and iteration > max_iterations:
                self.update_status(
                    f"Completed {max_iterations} loop(s)!", total_steps, total_steps)
                return

            # Status message
            if self.loop and max_iterations is None:
                self.update_status(
                    f"Starting recorded macro (Loop {iteration})...", total_steps, 0)
            elif self.loop and max_iterations is not None:
                self.update_status(
                    f"Starting recorded macro (Loop {iteration}/{max_iterations})...", total_steps, 0)
            else:
                self.update_status(
                    "Starting recorded macro...", total_steps, 0)

            try:
                for step, action in enumerate(self.actions, start=1):
                    if not running.is_set():
                        return

                    action_type = action.get("type")

                    if action_type == "keypress":
                        # Quick key tap
                        key = action.get("key")
                        if not self.press_key(
                            game_window, key, None, running,
                            current_step=step, total_steps=total_steps
                        ):
                            return

                    elif action_type == "keyhold":
                        # Hold key for duration
                        key = action.get("key")
                        duration = action.get("duration", 0.1)
                        if not self.press_key(
                            game_window, key, duration, running,
                            current_step=step, total_steps=total_steps
                        ):
                            return

                    elif action_type == "sleep":
                        # Wait/delay
                        delay = action.get("delay", 1.0)
                        if not self.safe_sleep(delay, running, current_step=step, total_steps=total_steps):
                            return

                    else:
                        logger.warning(f"Unknown action type: {action_type}")

                # If not looping, exit after one execution
                if not self.loop:
                    self.update_status(
                        "Recorded macro completed!", total_steps, total_steps)
                    return

            except Exception as e:
                logger.error(f"Error in RecordedMacro: {e}", exc_info=True)
                raise MacroExecutionError(f"Recorded macro failed: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert macro to dictionary for saving.

        Returns:
            Dictionary representation of the macro.
        """
        return {
            "name": self.name,
            "description": self.description,
            "actions": self.actions,
            "loop": self.loop,
            "loop_count": self.loop_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecordedMacro":
        """Create a RecordedMacro from dictionary data.

        Args:
            data: Dictionary containing macro data.

        Returns:
            RecordedMacro instance.
        """
        macro = cls(
            name=data["name"],
            description=data.get("description", "Custom recorded macro"),
            actions=data["actions"]
        )
        loop = data.get("loop", True)
        loop_count = data.get("loop_count", None)
        macro.set_loop(loop, loop_count)
        return macro
