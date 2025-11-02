"""Stdout redirector for GUI logging."""

import io
import tkinter as tk
from typing import Callable


class StdoutRedirector(io.StringIO):
    """Redirect stdout to a Tkinter Text widget."""

    def __init__(self, text_widget: tk.Text, status_callback: Callable):
        """Initialize the redirector.

        Args:
            text_widget: Tkinter Text widget to write output to.
            status_callback: Callback function for status updates.
        """
        super().__init__()
        self.text_widget = text_widget
        self.status_callback = status_callback

    def write(self, string: str) -> None:
        """Write string to the text widget.

        Args:
            string: String to write.
        """
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)
        self.text_widget.update_idletasks()

        # Parse output for status updates
        if "[Step" in string:
            try:
                step_info = string.split("]")[0].replace("[", "").strip()
                message = string.split("]")[1].strip()
                current_step, total_steps = step_info.replace("Step ", "").split("/")
                self.status_callback(current_step, total_steps, message)
            except Exception:
                pass
        elif "Starting" in string or "Error" in string:
            self.status_callback("--", "--", string.strip())

    def flush(self) -> None:
        """Required for stdout redirection."""
        pass
