"""Battlefield 6 macro implementations."""

import logging
import time
import threading
from typing import Any

from macro_manager.core.macro import Macro
from macro_manager.core.exceptions import MacroExecutionError

logger = logging.getLogger(__name__)


class BF6SiegeCairoMacro(Macro):
    """Siege of Cairo AFK Macro for Battlefield 6."""

    def __init__(self):
        """Initialize Siege of Cairo macro."""
        super().__init__(
            name="Battlefield 6 Siege of Cairo AFK",
            description=(
                "Siege of Cairo AFK Macro for Battlefield 6 that automates "
                "capturing objectives. Portal Code: YVNDS - "
                "Tutorial: https://youtu.be/LH_Gj87xodI?si=GJvNM4reqZoQxJ7f&t=161"
            ),
        )

    def run(self, game_window: Any, running: threading.Event) -> None:
        """Execute the Siege of Cairo macro cycle.

        Args:
            game_window: The window handle to send inputs to.
            running: Threading event that controls macro execution.

        Raises:
            MacroExecutionError: If macro execution fails.
        """
        total_steps = 12

        while running.is_set():
            try:
                self.update_status("Starting Siege of Cairo cycle...", total_steps, 0)

                # Forward sequence (Step 1-2)
                if not self.press_key(
                    game_window, "w", 15.70, running, current_step=1, total_steps=total_steps
                ):
                    return
                if not self.safe_sleep(120, running, current_step=2, total_steps=total_steps):
                    return

                # First space press and sleep (Step 3-4)
                if not self.press_key(
                    game_window, "space", None, running, current_step=3, total_steps=total_steps
                ):
                    return
                if not self.safe_sleep(120, running, current_step=4, total_steps=total_steps):
                    return

                # Second space press and sleep (Step 5-6)
                if not self.press_key(
                    game_window, "space", None, running, current_step=5, total_steps=total_steps
                ):
                    return
                if not self.safe_sleep(30, running, current_step=6, total_steps=total_steps):
                    return

                # Backward sequence (Step 7-8)
                if not self.press_key(
                    game_window, "s", 16.11, running, current_step=7, total_steps=total_steps
                ):
                    return
                if not self.safe_sleep(120, running, current_step=8, total_steps=total_steps):
                    return

                # First space press and sleep (Step 9-10)
                if not self.press_key(
                    game_window, "space", None, running, current_step=9, total_steps=total_steps
                ):
                    return
                if not self.safe_sleep(120, running, current_step=10, total_steps=total_steps):
                    return

                # Second space press and sleep (Step 11-12)
                if not self.press_key(
                    game_window, "space", None, running, current_step=11, total_steps=total_steps
                ):
                    return
                if not self.safe_sleep(30, running, current_step=12, total_steps=total_steps):
                    return

            except Exception as e:
                logger.error(f"Error in BF6SiegeCairoMacro: {e}", exc_info=True)
                raise MacroExecutionError(f"Siege of Cairo macro failed: {e}")


class BF6LibPeakMacro(Macro):
    """Liberation Peak AFK Macro for Battlefield 6."""

    def __init__(self):
        """Initialize Liberation Peak macro."""
        super().__init__(
            name="Battlefield 6 Liberation Peak AFK",
            description=(
                "Liberation Peak AFK Macro for Battlefield 6 that automates "
                "capturing objectives. Portal Code: YWVXU - "
                "Tutorial: https://youtu.be/TTv9BSTzFTg?si=fdGpfcFno4Y9w3cI&t=61"
            ),
        )

    def run(self, game_window: Any, running: threading.Event) -> None:
        """Execute the Liberation Peak macro cycle.

        Args:
            game_window: The window handle to send inputs to.
            running: Threading event that controls macro execution.

        Raises:
            MacroExecutionError: If macro execution fails.
        """
        total_steps = 4

        while running.is_set():
            try:
                self.update_status("Starting Liberation Peak cycle...", total_steps, 0)

                # Forward sequence (Step 1)
                if not self.press_key(
                    game_window, "w", 7, running, current_step=1, total_steps=total_steps
                ):
                    return

                # Press space 4 times with delays (Step 2)
                if not self.press_key(
                    game_window,
                    "space",
                    None,
                    running,
                    count=4,
                    delay=30,
                    current_step=2,
                    total_steps=total_steps,
                ):
                    return

                # Backward sequence (Step 3)
                if not self.press_key(
                    game_window, "s", 7, running, current_step=3, total_steps=total_steps
                ):
                    return

                # Press space 4 more times with delays (Step 4)
                if not self.press_key(
                    game_window,
                    "space",
                    None,
                    running,
                    count=4,
                    delay=30,
                    current_step=4,
                    total_steps=total_steps,
                ):
                    return

            except Exception as e:
                logger.error(f"Error in BF6LibPeakMacro: {e}", exc_info=True)
                raise MacroExecutionError(f"Liberation Peak macro failed: {e}")


class BF6SpaceBarMacro(Macro):
    """Space Bar AFK Macro for Battlefield 6."""

    def __init__(self):
        """Initialize Space Bar macro."""
        super().__init__(
            name="Battlefield 6 Space Bar AFK",
            description="Space Bar AFK Macro for Battlefield 6. Portal Code: YRV4A",
        )

    def run(self, game_window: Any, running: threading.Event) -> None:
        """Execute the Space Bar macro cycle.

        Args:
            game_window: The window handle to send inputs to.
            running: Threading event that controls macro execution.

        Raises:
            MacroExecutionError: If macro execution fails.
        """
        total_steps = 1

        while running.is_set():
            try:
                self.update_status("Starting Space Bar cycle...", total_steps, 0)

                # Press space repeatedly with delays
                if not self.press_key(
                    game_window,
                    "space",
                    None,
                    running,
                    count=120,
                    delay=30,
                    current_step=1,
                    total_steps=total_steps,
                ):
                    return

            except Exception as e:
                logger.error(f"Error in BF6SpaceBarMacro: {e}", exc_info=True)
                raise MacroExecutionError(f"Space Bar macro failed: {e}")
