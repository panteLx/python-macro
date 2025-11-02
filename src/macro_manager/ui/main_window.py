"""Main window for the MacroManager GUI."""

import io
import logging
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

import keyboard
import win32gui

from macro_manager.core.config import Config
from macro_manager.core.macro_controller import MacroController
from macro_manager.core.exceptions import WindowNotFoundError, MacroExecutionError
from macro_manager.macros import get_macro_by_name, get_all_macro_names
from macro_manager.ui.key_binding_dialog import KeyBindingDialog
from macro_manager.ui.stdout_redirector import StdoutRedirector
from macro_manager.utils.window_utils import find_game_window

logger = logging.getLogger(__name__)


class MainWindow:
    """Main application window for MacroManager."""

    def __init__(self, root: tk.Tk, config: Config):
        """Initialize the main window.

        Args:
            root: Root Tkinter window.
            config: Application configuration.
        """
        self.root = root
        self.config = config
        self.controller = MacroController()

        # Configure window
        self.root.title("MacroManager")
        width = self.config.get("window_width", 700)
        height = self.config.get("window_height", 900)
        self.root.geometry(f"{width}x{height}")
        self.root.resizable(True, True)
        self.root.minsize(500, 600)

        # Configure grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Create UI
        self.create_widgets()
        self.set_key_bindings()

        # Check for first-time setup (if config doesn't exist or is still default)
        if not self.config.config_file.exists() or self.is_first_run():
            self.root.after(500, self.first_time_setup)

        logger.info("Main window initialized")

    def create_widgets(self) -> None:
        """Create all UI widgets."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(8, weight=1)

        # Title
        title_label = ttk.Label(
            main_frame, text="MacroManager", font=("Helvetica", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Macro selection
        ttk.Label(
            main_frame, text="Select Macro:", font=("Helvetica", 10, "bold")
        ).grid(row=1, column=0, sticky=tk.W, pady=5)

        self.macro_combo = ttk.Combobox(main_frame, width=50, font=("Helvetica", 10))
        self.macro_combo["values"] = get_all_macro_names()
        self.macro_combo.grid(
            row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=5
        )
        if self.macro_combo["values"]:
            self.macro_combo.current(0)
        self.macro_combo.bind("<<ComboboxSelected>>", self.update_description)

        # Description
        ttk.Label(
            main_frame, text="Description:", font=("Helvetica", 10, "bold")
        ).grid(row=3, column=0, sticky=tk.W, pady=5)

        self.description_text = tk.Text(
            main_frame, height=6, wrap=tk.WORD, font=("Helvetica", 10)
        )
        self.description_text.grid(
            row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=5
        )
        self.description_text.config(state=tk.DISABLED)

        # Status frame
        self._create_status_frame(main_frame, row=5)

        # Key bindings frame
        self._create_keys_frame(main_frame, row=6)

        # Buttons
        self._create_button_frame(main_frame, row=7)

        # Log frame
        self._create_log_frame(main_frame, row=8)

        # Footer
        self._create_footer(main_frame, row=9)

        # Update description
        self.update_description(None)

    def _create_status_frame(self, parent: ttk.Frame, row: int) -> None:
        """Create the status display frame."""
        status_frame = ttk.LabelFrame(parent, text="Status", padding="10")
        status_frame.grid(row=row, column=0, columnspan=2,
                          sticky=(tk.W, tk.E), pady=10, padx=5)
        status_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(status_frame, text="Current State:", font=("Helvetica", 10)).grid(
            row=0, column=0, sticky=tk.W, padx=5
        )
        self.status_label = ttk.Label(
            status_frame, text="Idle", font=("Helvetica", 10, "bold")
        )
        self.status_label.grid(row=0, column=1, sticky=tk.W, padx=5)

        ttk.Label(status_frame, text="Game Window:", font=("Helvetica", 10)).grid(
            row=1, column=0, sticky=tk.W, padx=5
        )
        self.window_label = ttk.Label(
            status_frame, text="Not detected", font=("Helvetica", 10)
        )
        self.window_label.grid(row=1, column=1, sticky=tk.W, padx=5)

        ttk.Label(status_frame, text="Current Step:", font=("Helvetica", 10)).grid(
            row=2, column=0, sticky=tk.W, padx=5
        )
        self.step_label = ttk.Label(status_frame, text="--", font=("Helvetica", 10))
        self.step_label.grid(row=2, column=1, sticky=tk.W, padx=5)

        ttk.Label(status_frame, text="Action:", font=("Helvetica", 10)).grid(
            row=3, column=0, sticky=tk.W, padx=5
        )
        self.action_label = ttk.Label(status_frame, text="--", font=("Helvetica", 10))
        self.action_label.grid(row=3, column=1, sticky=tk.W, padx=5)

    def _create_keys_frame(self, parent: ttk.Frame, row: int) -> None:
        """Create the key bindings display frame."""
        keys_frame = ttk.LabelFrame(parent, text="Controls", padding="10")
        keys_frame.grid(row=row, column=0, columnspan=2,
                        sticky=(tk.W, tk.E), pady=10, padx=5)
        keys_frame.grid_columnconfigure(0, weight=1)

        bindings = self.config.key_bindings
        key_style = {"font": ("Helvetica", 10)}

        self.start_key_label = ttk.Label(
            keys_frame, text=f"Start Macro: {bindings['start_key'].upper()}", **key_style
        )
        self.start_key_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)

        self.stop_key_label = ttk.Label(
            keys_frame, text=f"Stop Macro: {bindings['stop_key'].upper()}", **key_style
        )
        self.stop_key_label.grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)

        ttk.Label(keys_frame, text="Change Keys: F12", **key_style).grid(
            row=2, column=0, sticky=tk.W, padx=5, pady=2
        )

    def _create_button_frame(self, parent: ttk.Frame, row: int) -> None:
        """Create the button control frame."""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=row, column=0, columnspan=2, pady=10)
        button_frame.grid_columnconfigure((0, 1, 2), weight=1)

        button_style = {"width": 15}

        ttk.Button(
            button_frame, text="Start", command=self.start_macro, **button_style
        ).grid(row=0, column=0, padx=10)

        ttk.Button(
            button_frame, text="Stop", command=self.stop_macro, **button_style
        ).grid(row=0, column=1, padx=10)

        ttk.Button(
            button_frame, text="Change Keys", command=self.change_keys, **button_style
        ).grid(row=0, column=2, padx=10)

    def _create_log_frame(self, parent: ttk.Frame, row: int) -> None:
        """Create the log output frame."""
        self.log_frame = ttk.LabelFrame(parent, text="Log", padding="10")
        self.log_frame.grid(row=row, column=0, columnspan=2, sticky=(
            tk.W, tk.E, tk.N, tk.S), pady=10, padx=5)
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(0, weight=1)

        self.log_text = tk.Text(
            self.log_frame, height=12, wrap=tk.WORD, font=("Helvetica", 10)
        )
        self.log_text.grid(row=0, column=0, sticky=(
            tk.W, tk.E, tk.N, tk.S), pady=5, padx=5)

        log_scrollbar = ttk.Scrollbar(
            self.log_frame, orient="vertical", command=self.log_text.yview
        )
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text.configure(yscrollcommand=log_scrollbar.set)

    def _create_footer(self, parent: ttk.Frame, row: int) -> None:
        """Create the footer section."""
        footer_frame = ttk.Frame(parent)
        footer_frame.grid(row=row, column=0, columnspan=2,
                          sticky=(tk.W, tk.E), pady=(10, 0))
        footer_frame.grid_columnconfigure(0, weight=1)

        ttk.Label(
            footer_frame, text="Developed by panteLx", font=("Helvetica", 9), anchor="center"
        ).grid(row=0, column=0, sticky=(tk.W, tk.E))

        ttk.Label(
            footer_frame,
            text="© 2025 MacroManager - MIT License",
            font=("Helvetica", 8),
            anchor="center",
        ).grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(2, 0))

    def update_description(self, event) -> None:
        """Update the macro description display."""
        selected_name = self.macro_combo.get()
        selected_macro = get_macro_by_name(selected_name)

        self.description_text.config(state=tk.NORMAL)
        self.description_text.delete(1.0, tk.END)
        if selected_macro:
            self.description_text.insert(tk.END, selected_macro.description)
        self.description_text.config(state=tk.DISABLED)

    def set_key_bindings(self) -> None:
        """Set up keyboard shortcuts."""
        keyboard.unhook_all()
        bindings = self.config.key_bindings

        keyboard.on_press_key(bindings["start_key"], lambda _: self.start_macro())
        keyboard.on_press_key(bindings["stop_key"], lambda _: self.stop_macro())
        keyboard.on_press_key("f12", lambda _: self.change_keys())

        logger.info(f"Key bindings set: {bindings}")

    def update_status(self, current_step: str, total_steps: str, message: str) -> None:
        """Update GUI status labels."""
        self.root.after(
            0, lambda: self._update_gui_status(current_step, total_steps, message)
        )

    def _update_gui_status(self, current_step: str, total_steps: str, message: str) -> None:
        """Update GUI elements (called from main thread)."""
        if current_step != "--":
            self.step_label.config(text=f"{current_step}/{total_steps}")
        self.action_label.config(text=message)

    def start_macro(self) -> None:
        """Start the selected macro."""
        if self.controller.is_running():
            logger.warning("Macro already running")
            return

        # Find game window
        game_window = find_game_window()
        if not game_window:
            messagebox.showerror(
                "Error",
                "Game window not found! Please make sure Battlefield is running.",
            )
            self.window_label.config(text="Not detected")
            logger.error("Game window not found")
            return

        window_title = win32gui.GetWindowText(game_window)
        self.window_label.config(text=window_title)
        logger.info(f"Found game window: {window_title}")

        # Get selected macro
        selected_name = self.macro_combo.get()
        macro = get_macro_by_name(selected_name)

        if not macro:
            messagebox.showerror("Error", "Please select a macro first!")
            logger.error("No macro selected")
            return

        # Clear log
        self.log_text.delete(1.0, tk.END)

        # Redirect stdout for UI logging
        stdout_redirector = StdoutRedirector(self.log_text, self.update_status)
        sys.stdout = stdout_redirector
        sys.stderr = stdout_redirector

        # Start macro
        try:
            self.controller.start_macro(macro, game_window)
            self.status_label.config(text="Running")
            self.step_label.config(text="--")
            self.action_label.config(text="Starting...")
            logger.info(f"Started macro: {macro.name}")
        except MacroExecutionError as e:
            messagebox.showerror("Error", str(e))
            logger.error(f"Failed to start macro: {e}")

    def stop_macro(self) -> None:
        """Stop the running macro."""
        self.controller.stop_macro()
        self.status_label.config(text="Stopped")
        self.step_label.config(text="--")
        self.action_label.config(text="Stopped")
        logger.info("Macro stopped")

    def change_keys(self) -> None:
        """Open key binding configuration dialog."""
        if self.controller.is_running():
            messagebox.showwarning(
                "Warning", "Please stop the macro before changing keys!"
            )
            return

        dialog = KeyBindingDialog(self.root, self.config.key_bindings)
        new_bindings = dialog.show()

        if new_bindings is None:
            return

        # Update configuration
        self.config.update_key_bindings(
            new_bindings["start_key"], new_bindings["stop_key"]
        )

        # Update key bindings
        self.set_key_bindings()

        # Update UI labels
        self.start_key_label.config(
            text=f"Start Macro: {new_bindings['start_key'].upper()}"
        )
        self.stop_key_label.config(
            text=f"Stop Macro: {new_bindings['stop_key'].upper()}"
        )

        messagebox.showinfo("Success", "Key bindings updated successfully!")
        logger.info(f"Key bindings updated: {new_bindings}")

    def is_first_run(self) -> bool:
        """Check if this is the first run by seeing if config has been customized."""
        try:
            # Check if a marker file exists
            marker_file = self.config.config_dir / ".setup_complete"
            return not marker_file.exists()
        except Exception:
            return False

    def first_time_setup(self) -> None:
        """Show welcome message on first run."""
        result = messagebox.askyesno(
            "Welcome to MacroManager!",
            "This is your first time running MacroManager.\n\n"
            "Default key bindings:\n"
            "• Start Macro: F1\n"
            "• Stop Macro: F2\n\n"
            "Would you like to configure custom key bindings now?\n"
            "(You can change them later using the 'Change Keys' button)",
        )

        # Mark setup as complete
        try:
            marker_file = self.config.config_dir / ".setup_complete"
            marker_file.touch()
        except Exception as e:
            logger.warning(f"Could not create setup marker: {e}")

        if result:
            self.change_keys()

    def cleanup(self) -> None:
        """Clean up resources before closing."""
        if self.controller.is_running():
            self.stop_macro()

        # Restore stdout/stderr
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

        logger.info("Main window cleanup completed")
