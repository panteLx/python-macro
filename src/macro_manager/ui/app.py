"""Main GUI application for MacroManager."""

import io
import logging
import os
import sys
import tkinter as tk
from pathlib import Path
from typing import Optional

from macro_manager.core.config import Config
from macro_manager.core.logger import setup_logging
from macro_manager.ui.main_window import MainWindow
from macro_manager.ui.update_dialog import (
    UpdateDialog,
    show_update_progress,
    show_update_success,
    show_update_error
)
from macro_manager.utils.auto_updater import (
    check_for_updates,
    download_and_install_update,
    cleanup_backups
)

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

        # Create root window (initially hidden)
        self.root = tk.Tk()
        self.root.withdraw()  # Hide until update check is complete

        # Check for updates before showing main window
        self._check_for_updates()

        # Show main window
        self.root.deiconify()
        self.main_window = MainWindow(self.root, self.config)

        # Set up cleanup on close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _check_for_updates(self):
        """Check for updates and prompt user if available."""
        try:
            update_info = check_for_updates()

            if update_info is None:
                # No update available or check failed
                return

            version, download_url, release_notes = update_info

            # Show update dialog
            def on_update():
                """Handle user confirming update."""
                # Show progress dialog
                progress_dialog = show_update_progress(self.root)

                # Download and install update
                success = download_and_install_update(download_url, version)

                # Close progress dialog
                progress_dialog.destroy()

                if success:
                    # Clean up old backups
                    cleanup_backups()

                    # Show success message
                    show_update_success(self.root)

                    # Restart the application
                    self._restart_application()
                else:
                    show_update_error(self.root)

            def on_skip():
                """Handle user skipping update."""
                logger.info("User skipped update")

            # Create and show update dialog
            dialog = UpdateDialog(
                self.root,
                version,
                release_notes,
                on_update,
                on_skip
            )
            dialog.show()

        except Exception as e:
            logger.error(f"Error during update check: {e}", exc_info=True)

    def _restart_application(self):
        """Restart the application."""
        try:
            logger.info("Restarting application...")

            # Get the path to the Python executable and script
            python = sys.executable
            script = sys.argv[0]

            # Close the current application
            self.root.destroy()

            # Restart using the batch file if on Windows
            if sys.platform == "win32":
                batch_file = Path(
                    __file__).parent.parent.parent.parent / "start_macromanager.bat"
                if batch_file.exists():
                    os.startfile(str(batch_file))
                else:
                    os.execl(python, python, script, *sys.argv[1:])
            else:
                os.execl(python, python, script, *sys.argv[1:])

        except Exception as e:
            logger.error(f"Failed to restart application: {e}", exc_info=True)
            sys.exit(0)

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
