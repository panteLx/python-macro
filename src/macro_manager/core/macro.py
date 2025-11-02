"""Base Macro class with improved architecture."""

import logging
import threading
import time
from abc import ABC, abstractmethod
from typing import Any, Optional

from macro_manager.core.exceptions import MacroExecutionError

logger = logging.getLogger(__name__)


class Macro(ABC):
    """Abstract base class for all macros.

    Attributes:
        name: Display name of the macro.
        description: Detailed description of what the macro does.
    """

    def __init__(self, name: str, description: str):
        """Initialize macro.

        Args:
            name: Display name of the macro.
            description: Detailed description of the macro's functionality.
        """
        self.name = name
        self.description = description
        self._logger = logging.getLogger(f"macro_manager.macros.{name}")

    def update_status(
        self,
        message: str,
        total_steps: Optional[int] = None,
        current_step: Optional[int] = None,
    ) -> None:
        """Update the status message with step information.

        Args:
            message: Status message to display.
            total_steps: Total number of steps in the macro.
            current_step: Current step number.
        """
        if total_steps is not None and current_step is not None:
            step_info = f"[Step {current_step}/{total_steps}] "
            formatted_message = step_info + message
        else:
            formatted_message = message

        self._logger.info(formatted_message)
        print(formatted_message)  # For UI output redirection

    def safe_sleep(
        self,
        duration: float,
        running: threading.Event,
        current_step: Optional[int] = None,
        total_steps: Optional[int] = None,
    ) -> bool:
        """Sleep for duration while checking running state.

        Args:
            duration: Time to sleep in seconds.
            running: Event to check if macro should continue running.
            current_step: Current step number (optional).
            total_steps: Total number of steps (optional).

        Returns:
            True if sleep completed, False if interrupted.
        """
        start_time = time.time()
        self.update_status(
            f"Waiting for {duration:.1f} seconds...", total_steps, current_step
        )

        while time.time() - start_time < duration:
            if not running.is_set():
                self._logger.info("Sleep interrupted - macro stopped")
                return False
            time.sleep(0.1)

        return True

    def press_key(
        self,
        game_window: Any,
        key: str,
        duration: Optional[float],
        running: threading.Event,
        count: int = 1,
        delay: float = 0,
        current_step: Optional[int] = None,
        total_steps: Optional[int] = None,
    ) -> bool:
        """Press a key one or more times.

        Args:
            game_window: Window handle to send inputs to.
            key: Key to press.
            duration: How long to hold the key (None for tap).
            running: Event to check if macro should continue.
            count: Number of times to press the key.
            delay: Delay between multiple presses.
            current_step: Current step number (optional).
            total_steps: Total number of steps (optional).

        Returns:
            True if completed, False if interrupted.

        Raises:
            MacroExecutionError: If key press fails.
        """
        from macro_manager.utils.window_utils import send_key_to_window

        for i in range(count):
            if not running.is_set():
                self._logger.info("Key press interrupted - macro stopped")
                return False

            # Format status message
            if count > 1:
                action_msg = f"Pressing {key.upper()} ({i + 1}/{count})"
            else:
                if duration:
                    action_msg = f"Pressing {key.upper()} for {duration:.2f} seconds"
                else:
                    action_msg = f"Pressing {key.upper()}"

            self.update_status(action_msg, total_steps, current_step)

            try:
                send_key_to_window(game_window, key, duration, running)
            except Exception as e:
                self._logger.error(f"Failed to press key {key}: {e}")
                raise MacroExecutionError(f"Failed to press key {key}: {e}")

            if not running.is_set():
                return False

            self.update_status(f"Released {key.upper()}", total_steps, current_step)

            # Delay between multiple presses
            if delay > 0 and i < count - 1:
                if not self.safe_sleep(delay, running, current_step, total_steps):
                    return False

        return True

    @abstractmethod
    def run(self, game_window: Any, running: threading.Event) -> None:
        """Execute the macro's actions.

        Args:
            game_window: The window handle to send inputs to.
            running: Threading event that controls macro execution.

        Raises:
            MacroExecutionError: If macro execution fails.
        """
        raise NotImplementedError("Each macro must implement run()")

    def __str__(self) -> str:
        """String representation of the macro."""
        return f"{self.name}: {self.description}"

    def __repr__(self) -> str:
        """Developer-friendly representation of the macro."""
        return f"Macro(name='{self.name}')"
