"""Update notification dialog for MacroManager."""

import logging
import tkinter as tk
from tkinter import scrolledtext, messagebox
from typing import Callable, Optional

from macro_manager.ui.theme import COLORS

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

        # Use centralized color scheme
        self.colors = COLORS

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Update Available")
        self.dialog.geometry("550x450")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg=self.colors['bg_dark'])

        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (550 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (450 // 2)
        self.dialog.geometry(f"550x450+{x}+{y}")

        self._create_widgets()

        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_skip)

    def _create_widgets(self):
        """Create dialog widgets."""
        # Header frame
        header_frame = tk.Frame(
            self.dialog, bg=self.colors['accent'], height=90)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        # Title
        title_label = tk.Label(
            header_frame,
            text="🎉 Update Available!",
            font=('Segoe UI', 18, 'bold'),
            bg=self.colors['accent'],
            fg='#ffffff'
        )
        title_label.pack(pady=15)

        # Version info
        version_label = tk.Label(
            header_frame,
            text=f"Version {self.version} is now available",
            font=('Segoe UI', 11),
            bg=self.colors['accent'],
            fg='#ffffff'
        )
        version_label.pack()

        # Content frame
        content_frame = tk.Frame(self.dialog, padx=25,
                                 pady=20, bg=self.colors['bg_dark'])
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Release notes label
        notes_label = tk.Label(
            content_frame,
            text="What's New:",
            font=('Segoe UI', 11, 'bold'),
            bg=self.colors['bg_dark'],
            fg=self.colors['fg_primary']
        )
        notes_label.pack(anchor=tk.W, pady=(0, 8))

        # Release notes text
        notes_text = scrolledtext.ScrolledText(
            content_frame,
            wrap=tk.WORD,
            height=10,
            font=('Segoe UI', 9),
            bg=self.colors['bg_medium'],
            fg=self.colors['fg_primary'],
            relief='flat',
            borderwidth=1,
            insertbackground=self.colors['fg_primary']
        )
        notes_text.pack(fill=tk.BOTH, expand=True)
        notes_text.insert(tk.END, self.release_notes)
        notes_text.config(state=tk.DISABLED)

        # Info label
        info_label = tk.Label(
            content_frame,
            text="⚠ The application will restart after updating.",
            font=('Segoe UI', 9),
            bg=self.colors['bg_dark'],
            fg=self.colors['warning']
        )
        info_label.pack(pady=(12, 5))

        # Button frame
        button_frame = tk.Frame(self.dialog, pady=15,
                                bg=self.colors['bg_dark'])
        button_frame.pack(fill=tk.X)

        # Update button
        update_btn = tk.Button(
            button_frame,
            text="✓ Update Now",
            command=self._on_update,
            bg=self.colors['success'],
            fg='#ffffff',
            activebackground='#3da88a',
            activeforeground='#ffffff',
            font=('Segoe UI', 10, 'bold'),
            width=15,
            cursor='hand2',
            relief='flat',
            borderwidth=0,
            padx=15,
            pady=10
        )
        update_btn.pack(side=tk.LEFT, padx=(25, 10))

        # Skip button
        skip_btn = tk.Button(
            button_frame,
            text="Skip",
            command=self._on_skip,
            bg=self.colors['bg_light'],
            fg=self.colors['fg_primary'],
            activebackground=self.colors['bg_medium'],
            activeforeground=self.colors['fg_primary'],
            font=('Segoe UI', 10),
            width=15,
            cursor='hand2',
            relief='flat',
            borderwidth=0,
            padx=15,
            pady=10
        )
        skip_btn.pack(side=tk.LEFT, padx=(10, 25))

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
    progress_dialog.geometry("500x250")
    progress_dialog.resizable(False, False)
    progress_dialog.transient(parent)
    progress_dialog.grab_set()
    progress_dialog.configure(bg=COLORS['bg_dark'])

    # Center the dialog
    progress_dialog.update_idletasks()
    x = (progress_dialog.winfo_screenwidth() // 2) - (500 // 2)
    y = (progress_dialog.winfo_screenheight() // 2) - (250 // 2)
    progress_dialog.geometry(f"500x250+{x}+{y}")

    # Disable close button
    progress_dialog.protocol("WM_DELETE_WINDOW", lambda: None)

    # Content frame
    content_frame = tk.Frame(progress_dialog, padx=35,
                             pady=35, bg=COLORS['bg_dark'])
    content_frame.pack(fill=tk.BOTH, expand=True)

    # Icon/spinner label
    icon_label = tk.Label(
        content_frame,
        text="⏳",
        font=('Segoe UI', 40),
        bg=COLORS['bg_dark'],
        fg=COLORS['accent']
    )
    icon_label.pack(pady=(0, 15))

    # Status label
    status_label = tk.Label(
        content_frame,
        text="Downloading and installing update...\nPlease wait, this may take a minute.",
        font=('Segoe UI', 10),
        bg=COLORS['bg_dark'],
        fg=COLORS['fg_primary'],
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


def show_update_error(parent: tk.Tk):
    """
    Show error message if update fails.

    Args:
        parent: Parent window
    """
    messagebox.showerror(
        "Update Failed",
        "Failed to install the update.\n\n"
        "Please try again later or download manually from GitHub.",
        parent=parent
    )
