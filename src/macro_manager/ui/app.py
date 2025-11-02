"""Main GUI application for MacroManager."""

import io
import logging
import sys
import tkinter as tk
from pathlib import Path
from typing import Optional

from macro_manager.core.config import Config
from macro_manager.core.logger import setup_logging
from macro_manager.ui.main_window import MainWindow

logger = logging.getLogger(__name__)


class MacroManagerApp:
    """Main application class for MacroManager."""

    def __init__(self):
        """Initialize the MacroManager application."""
        # Set up configuration
        self.config = Config()

        # Set up logging
        log_dir = Path(__file__).parent.parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        setup_logging(
            log_level=self.config.get("log_level", "INFO"),
            log_file=log_dir / "macro_manager.log",
            console=False,  # Don't log to console to avoid UI interference
        )

        logger.info("Starting MacroManager application")

        # Create main window
        self.root = tk.Tk()
        self.main_window = MainWindow(self.root, self.config)

        # Set up cleanup on close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def run(self) -> None:
        """Run the application main loop."""
        try:
            self.root.mainloop()
        except Exception as e:
            logger.error(f"Application error: {e}", exc_info=True)
            raise

    def on_closing(self) -> None:
        """Handle application closing."""
        logger.info("Closing MacroManager application")
        self.main_window.cleanup()
        self.root.destroy()


def main() -> None:
    """Entry point for the application."""
    try:
        app = MacroManagerApp()
        app.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
