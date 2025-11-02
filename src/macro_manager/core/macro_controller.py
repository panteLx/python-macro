"""Controller for managing macro execution."""

import logging
import threading
from typing import Optional, Any

from macro_manager.core.macro import Macro
from macro_manager.core.exceptions import MacroExecutionError

logger = logging.getLogger(__name__)


class MacroController:
    """Manages macro execution and state."""

    def __init__(self):
        """Initialize the macro controller."""
        self.current_macro: Optional[Macro] = None
        self.macro_thread: Optional[threading.Thread] = None
        self.running: threading.Event = threading.Event()
        self.game_window: Optional[Any] = None

    def start_macro(self, macro: Macro, game_window: Any) -> None:
        """Start executing a macro.

        Args:
            macro: The macro to execute.
            game_window: The window handle to send inputs to.

        Raises:
            MacroExecutionError: If macro is already running or fails to start.
        """
        if self.is_running():
            logger.warning("Attempted to start macro while another is running")
            raise MacroExecutionError("A macro is already running")

        self.current_macro = macro
        self.game_window = game_window
        self.running.set()

        self.macro_thread = threading.Thread(
            target=self._run_macro,
            args=(macro, game_window),
            daemon=True,
            name=f"MacroThread-{macro.name}",
        )
        self.macro_thread.start()
        logger.info(f"Started macro: {macro.name}")

    def stop_macro(self) -> None:
        """Stop the currently running macro."""
        if not self.is_running():
            logger.warning("Attempted to stop macro but none is running")
            return

        self.running.clear()
        logger.info(f"Stopping macro: {self.current_macro.name}")

        # Wait for thread to finish (with timeout)
        if self.macro_thread and self.macro_thread.is_alive():
            self.macro_thread.join(timeout=2.0)

        self.current_macro = None
        self.macro_thread = None

    def is_running(self) -> bool:
        """Check if a macro is currently running.

        Returns:
            True if a macro is running, False otherwise.
        """
        return self.macro_thread is not None and self.macro_thread.is_alive()

    def _run_macro(self, macro: Macro, game_window: Any) -> None:
        """Internal method to run the macro.

        Args:
            macro: The macro to execute.
            game_window: The window handle to send inputs to.
        """
        try:
            logger.info(f"Executing macro: {macro.name}")
            macro.run(game_window, self.running)
        except Exception as e:
            logger.error(f"Macro execution failed: {e}", exc_info=True)
            print(f"Error: {e}")
        finally:
            self.running.clear()
            logger.info(f"Macro execution completed: {macro.name}")
