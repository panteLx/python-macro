"""Main GUI application for MacroManager."""

import io
import logging
import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from typing import Optional

from macro_manager.core.config import Config
from macro_manager.core.logger import setup_logging
from macro_manager.ui.main_window import MainWindow
from macro_manager.macros import initialize_macro_storage
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
from macro_manager.utils.macro_sync import sync_prebuilt_macros

logger = logging.getLogger(__name__)


class MacroManagerApp:
    """Main application class for MacroManager."""

    def __init__(self):
        """Initialize the MacroManager application."""
        # Set up configuration
        self.config = Config()

        # Set up logging
        # logs directory is now in the base directory (parent of src)
        # Use absolute path to work when run as admin
        log_dir = Path(__file__).resolve().parent.parent.parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        setup_logging(
            log_level=self.config.get("log_level", "INFO"),
            log_file=log_dir / "macro_manager.log",
            console=False,  # Don't log to console to avoid UI interference
        )

        logger.info("Starting MacroManager application")

        # Sync prebuilt macros from GitHub (before initializing storage)
        macros_dir = self.config.config_dir / "recorded_macros"
        sync_prebuilt_macros(macros_dir)

        # Initialize macro storage
        initialize_macro_storage(self.config.config_dir)

        # Create root window
        self.root = tk.Tk()
        self.root.title("MacroManager")

        # Store update info to check after window is ready
        self.pending_update = None

        # Configure root window geometry (small, off-screen initially)
        self.root.geometry("1x1+0+0")
        self.root.attributes('-alpha', 0.0)  # Make invisible

        # Check for updates (non-blocking)
        update_channel = self.config.get("update_channel", "stable")
        self.pending_update = check_for_updates(channel=update_channel)

        # Restore window visibility and create main window
        self.root.attributes('-alpha', 1.0)
        self.main_window = MainWindow(self.root, self.config)

        # Set the update callback for manual update checks
        self.main_window.set_update_callback(self.manual_update_check)

        # Set up cleanup on close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Schedule update check dialog after main loop starts
        if self.pending_update is not None:
            self.root.after(100, self._show_update_dialog)

    def _show_update_dialog(self):
        """Show the update dialog after main window is ready."""
        try:
            if self.pending_update is None:
                return

            version, download_url, release_notes = self.pending_update

            # Show update dialog
            def on_update():
                """Handle user confirming update."""
                # Show progress dialog
                progress_dialog = show_update_progress(self.root)

                # Process pending events to show the progress dialog
                self.root.update()

                # Download and install update (this runs synchronously)
                try:
                    success = download_and_install_update(
                        download_url, version)
                except Exception as e:
                    logger.error(
                        f"Update installation failed: {e}", exc_info=True)
                    success = False

                # Close progress dialog
                try:
                    progress_dialog.destroy()
                except:
                    pass

                if success:
                    # Clean up old backups
                    cleanup_backups()

                    # Show success message
                    show_update_success(self.root)

                    # Close the application
                    self._close_application()
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
            logger.error(f"Error showing update dialog: {e}", exc_info=True)

    def manual_update_check(self):
        """Manually check for updates when user clicks the button."""
        try:
            logger.info("Manual update check triggered")

            # Get update channel from config
            update_channel = self.config.get("update_channel", "stable")

            # Check for updates
            update_info = check_for_updates(channel=update_channel)

            if update_info is None:
                # No updates available
                messagebox.showinfo(
                    "No Updates",
                    "You are running the latest version!",
                    parent=self.root
                )
                return

            # Update available, show dialog
            version, download_url, release_notes = update_info

            def on_update():
                """Handle user confirming update."""
                # Show progress dialog
                progress_dialog = show_update_progress(self.root)

                # Process pending events to show the progress dialog
                self.root.update()

                # Download and install update (this runs synchronously)
                try:
                    success = download_and_install_update(
                        download_url, version)
                except Exception as e:
                    logger.error(
                        f"Update installation failed: {e}", exc_info=True)
                    success = False

                # Close progress dialog
                try:
                    progress_dialog.destroy()
                except:
                    pass

                if success:
                    # Clean up old backups
                    cleanup_backups()

                    # Show success message
                    show_update_success(self.root)

                    # Close the application
                    self._close_application()
                else:
                    show_update_error(self.root)

            def on_skip():
                """Handle user skipping update."""
                logger.info("User skipped manual update")

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
            logger.error(
                f"Error during manual update check: {e}", exc_info=True)
            messagebox.showerror(
                "Error",
                "Failed to check for updates. Please try again later.",
                parent=self.root
            )

    def _close_application(self):
        """Close the application after update."""
        try:
            logger.info("Closing application after update...")

            # Cleanup main window
            self.main_window.cleanup()

            # Destroy root window
            self.root.destroy()

            # Exit the application
            sys.exit(0)

        except Exception as e:
            logger.error(f"Error closing application: {e}", exc_info=True)
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
