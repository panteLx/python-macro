"""Update notification dialog for MacroManager."""

import logging
import tkinter as tk
from tkinter import scrolledtext, messagebox
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class UpdateDialog:
    """Dialog for notifying users about available updates."""

    def __init__(self, parent: tk.Tk, version: str, release_notes: str,
                 on_update: Callable, on_skip: Callable):
        """
        Initialize the update dialog.

        Args:
            parent: Parent window
            version: New version available
            release_notes: Release notes for the new version
            on_update: Callback when user confirms update
            on_skip: Callback when user skips update
        """
        self.parent = parent
        self.version = version
        self.release_notes = release_notes
        self.on_update = on_update
        self.on_skip = on_skip
        self.result = False

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Update Available")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"500x400+{x}+{y}")

        self._create_widgets()

        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_skip)

    def _create_widgets(self):
        """Create dialog widgets."""
        # Header frame
        header_frame = tk.Frame(self.dialog, bg="#4CAF50", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        # Title
        title_label = tk.Label(
            header_frame,
            text="🎉 Update Available!",
            font=("Arial", 16, "bold"),
            bg="#4CAF50",
            fg="white"
        )
        title_label.pack(pady=10)

        # Version info
        version_label = tk.Label(
            header_frame,
            text=f"Version {self.version} is now available",
            font=("Arial", 10),
            bg="#4CAF50",
            fg="white"
        )
        version_label.pack()

        # Content frame
        content_frame = tk.Frame(self.dialog, padx=20, pady=10)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Release notes label
        notes_label = tk.Label(
            content_frame,
            text="What's New:",
            font=("Arial", 10, "bold")
        )
        notes_label.pack(anchor=tk.W, pady=(0, 5))

        # Release notes text
        notes_text = scrolledtext.ScrolledText(
            content_frame,
            wrap=tk.WORD,
            height=10,
            font=("Arial", 9),
            relief=tk.SOLID,
            borderwidth=1
        )
        notes_text.pack(fill=tk.BOTH, expand=True)
        notes_text.insert(tk.END, self.release_notes)
        notes_text.config(state=tk.DISABLED)

        # Info label
        info_label = tk.Label(
            content_frame,
            text="The application will restart after updating.",
            font=("Arial", 8),
            fg="gray"
        )
        info_label.pack(pady=(10, 5))

        # Button frame
        button_frame = tk.Frame(self.dialog, pady=10)
        button_frame.pack(fill=tk.X)

        # Update button
        update_btn = tk.Button(
            button_frame,
            text="Update Now",
            command=self._on_update,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
            width=15,
            cursor="hand2",
            relief=tk.FLAT,
            padx=10,
            pady=5
        )
        update_btn.pack(side=tk.LEFT, padx=(20, 10))

        # Skip button
        skip_btn = tk.Button(
            button_frame,
            text="Skip",
            command=self._on_skip,
            bg="#f0f0f0",
            font=("Arial", 10),
            width=15,
            cursor="hand2",
            relief=tk.FLAT,
            padx=10,
            pady=5
        )
        skip_btn.pack(side=tk.LEFT, padx=(10, 20))

        # Bind hover effects
        update_btn.bind("<Enter>", lambda e: update_btn.config(bg="#45a049"))
        update_btn.bind("<Leave>", lambda e: update_btn.config(bg="#4CAF50"))
        skip_btn.bind("<Enter>", lambda e: skip_btn.config(bg="#e0e0e0"))
        skip_btn.bind("<Leave>", lambda e: skip_btn.config(bg="#f0f0f0"))

    def _on_update(self):
        """Handle update button click."""
        self.result = True
        self.dialog.destroy()
        self.on_update()

    def _on_skip(self):
        """Handle skip button click."""
        self.result = False
        self.dialog.destroy()
        self.on_skip()

    def show(self):
        """Show the dialog and wait for user response."""
        self.dialog.wait_window()
        return self.result


def show_update_progress(parent: tk.Tk) -> tk.Toplevel:
    """
    Show a progress dialog during update installation.

    Args:
        parent: Parent window

    Returns:
        Progress dialog window
    """
    progress_dialog = tk.Toplevel(parent)
    progress_dialog.title("Installing Update")
    progress_dialog.geometry("400x150")
    progress_dialog.resizable(False, False)
    progress_dialog.transient(parent)
    progress_dialog.grab_set()

    # Center the dialog
    progress_dialog.update_idletasks()
    x = (progress_dialog.winfo_screenwidth() // 2) - (400 // 2)
    y = (progress_dialog.winfo_screenheight() // 2) - (150 // 2)
    progress_dialog.geometry(f"400x150+{x}+{y}")

    # Disable close button
    progress_dialog.protocol("WM_DELETE_WINDOW", lambda: None)

    # Content frame
    content_frame = tk.Frame(progress_dialog, padx=30, pady=30)
    content_frame.pack(fill=tk.BOTH, expand=True)

    # Icon/spinner label
    icon_label = tk.Label(
        content_frame,
        text="⏳",
        font=("Arial", 32)
    )
    icon_label.pack(pady=(0, 10))

    # Status label
    status_label = tk.Label(
        content_frame,
        text="Downloading and installing update...\nPlease wait, this may take a minute.",
        font=("Arial", 10),
        justify=tk.CENTER
    )
    status_label.pack()

    progress_dialog.update()

    return progress_dialog


def show_update_success(parent: tk.Tk):
    """
    Show success message after update installation.

    Args:
        parent: Parent window
    """
    messagebox.showinfo(
        "Update Successful",
        "The update has been installed successfully!\n\n"
        "The application will now restart.",
        parent=parent
    )


def show_update_error(parent: tk.Tk, error_msg: str = ""):
    """
    Show error message if update fails.

    Args:
        parent: Parent window
        error_msg: Optional error message
    """
    message = "Failed to install the update."
    if error_msg:
        message += f"\n\nError: {error_msg}"
    message += "\n\nPlease try again later or download manually from GitHub."

    messagebox.showerror(
        "Update Failed",
        message,
        parent=parent
    )
