"""Dialog for changing key bindings."""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional

import keyboard


class KeyBindingDialog:
    """Dialog for configuring key bindings."""

    def __init__(self, parent: tk.Tk, current_bindings: Dict[str, str]):
        """Initialize the key binding dialog.

        Args:
            parent: Parent window.
            current_bindings: Current key binding configuration.
        """
        self.result: Optional[Dict[str, str]] = None
        self.current_key: Optional[str] = None
        self.capturing = False

        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Change Key Bindings")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title
        ttk.Label(
            main_frame,
            text="Configure Key Bindings",
            font=("Helvetica", 14, "bold"),
        ).grid(row=0, column=0, columnspan=2, pady=(0, 15))

        # Instructions
        ttk.Label(
            main_frame,
            text="Click the button and press the key you want to assign.\n"
            "Avoid using ESC or system keys.",
            font=("Helvetica", 10),
            justify=tk.CENTER,
        ).grid(row=1, column=0, columnspan=2, pady=(0, 20))

        # Start key section
        self._create_key_section(
            main_frame, "Start Macro Key", "start", current_bindings["start_key"], row=2
        )

        # Stop key section
        self._create_key_section(
            main_frame, "Stop Macro Key", "stop", current_bindings["stop_key"], row=3
        )

        # Status label
        self.status_label = ttk.Label(
            main_frame,
            text="",
            font=("Helvetica", 10, "italic"),
            foreground="blue",
        )
        self.status_label.grid(row=4, column=0, columnspan=2, pady=15)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=(15, 0))

        self.save_button = ttk.Button(
            button_frame, text="Save Changes", command=self.save_changes, state="disabled"
        )
        self.save_button.grid(row=0, column=0, padx=10)

        ttk.Button(button_frame, text="Cancel", command=self.cancel).grid(
            row=0, column=1, padx=10
        )

        # Store new bindings
        self.new_bindings = current_bindings.copy()

        # Center dialog
        self.dialog.update_idletasks()
        width = self.dialog.winfo_reqwidth()
        height = self.dialog.winfo_reqheight()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")

    def _create_key_section(
        self, parent: ttk.Frame, title: str, key_type: str, current_key: str, row: int
    ) -> None:
        """Create a key configuration section."""
        frame = ttk.LabelFrame(parent, text=title, padding="15")
        frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=8)

        ttk.Label(frame, text="Current:", font=("Helvetica", 10)).grid(
            row=0, column=0, sticky=tk.W, padx=5
        )

        # Store label references
        if key_type == "start":
            self.start_current_label = ttk.Label(
                frame, text=current_key.upper(), font=("Helvetica", 10, "bold")
            )
            self.start_current_label.grid(row=0, column=1, sticky=tk.W, padx=5)

            self.start_button = ttk.Button(
                frame, text="Set New Key", command=lambda: self.capture_key("start")
            )
            self.start_button.grid(row=0, column=2, padx=10)

            self.start_new_label = ttk.Label(
                frame, text="", font=("Helvetica", 10, "bold"), foreground="green"
            )
            self.start_new_label.grid(row=0, column=3, sticky=tk.W, padx=5)
        else:
            self.stop_current_label = ttk.Label(
                frame, text=current_key.upper(), font=("Helvetica", 10, "bold")
            )
            self.stop_current_label.grid(row=0, column=1, sticky=tk.W, padx=5)

            self.stop_button = ttk.Button(
                frame, text="Set New Key", command=lambda: self.capture_key("stop")
            )
            self.stop_button.grid(row=0, column=2, padx=10)

            self.stop_new_label = ttk.Label(
                frame, text="", font=("Helvetica", 10, "bold"), foreground="green"
            )
            self.stop_new_label.grid(row=0, column=3, sticky=tk.W, padx=5)

    def capture_key(self, key_type: str) -> None:
        """Start capturing a key press.

        Args:
            key_type: Type of key to capture ('start' or 'stop').
        """
        if self.capturing:
            return

        self.capturing = True
        self.current_key = key_type

        if key_type == "start":
            self.start_button.config(state="disabled")
            self.status_label.config(
                text="Press a key for START macro...", foreground="blue"
            )
        else:
            self.stop_button.config(state="disabled")
            self.status_label.config(
                text="Press a key for STOP macro...", foreground="blue"
            )

        keyboard.on_press(self.on_key_press, suppress=True)

    def on_key_press(self, event) -> None:
        """Handle key press event.

        Args:
            event: Keyboard event.
        """
        if not self.capturing:
            return

        key_name = event.name

        # Ignore ESC
        if key_name in ["esc", "escape"]:
            self.status_label.config(
                text="ESC is not allowed. Please choose another key.",
                foreground="red",
            )
            self.capturing = False
            keyboard.unhook_all()
            self.start_button.config(state="normal")
            self.stop_button.config(state="normal")
            return

        # Update binding
        self.new_bindings[f"{self.current_key}_key"] = key_name

        # Update label
        if self.current_key == "start":
            self.start_new_label.config(text=f"→ {key_name.upper()}")
            self.start_button.config(state="normal")
        else:
            self.stop_new_label.config(text=f"→ {key_name.upper()}")
            self.stop_button.config(state="normal")

        self.status_label.config(
            text=f"Key '{key_name.upper()}' assigned successfully!",
            foreground="green",
        )

        # Enable save button
        self.save_button.config(state="normal")

        # Stop capturing
        self.capturing = False
        keyboard.unhook_all()

    def save_changes(self) -> None:
        """Save the new key bindings."""
        keyboard.unhook_all()
        self.result = self.new_bindings
        self.dialog.destroy()

    def cancel(self) -> None:
        """Cancel without saving."""
        keyboard.unhook_all()
        self.result = None
        self.dialog.destroy()

    def show(self) -> Optional[Dict[str, str]]:
        """Show the dialog and return the result.

        Returns:
            New key bindings if saved, None if cancelled.
        """
        self.dialog.wait_window()
        return self.result
