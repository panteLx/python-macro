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
        self.key_hook = None  # Store the keyboard hook handle

        # Color scheme (matching main window)
        self.colors = {
            'bg_dark': '#1e1e1e',
            'bg_medium': '#2d2d2d',
            'bg_light': '#3e3e3e',
            'fg_primary': '#ffffff',
            'fg_secondary': '#b0b0b0',
            'accent': '#007acc',
            'accent_hover': '#005a9e',
            'success': '#4ec9b0',
            'warning': '#ce9178',
            'error': '#f48771',
            'border': '#555555'
        }

        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Change Key Bindings")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg=self.colors['bg_dark'])

        # Apply dark theme
        self._apply_dark_theme()

        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="25")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title
        tk.Label(
            main_frame,
            text="⚙ Configure Key Bindings",
            font=('Segoe UI', 14, 'bold'),
            bg=self.colors['bg_dark'],
            fg=self.colors['accent']
        ).grid(row=0, column=0, columnspan=2, pady=(0, 15))

        # Instructions
        tk.Label(
            main_frame,
            text="Click the button and press the key you want to assign.\n"
            "Avoid using ESC or system keys.",
            font=('Segoe UI', 10),
            bg=self.colors['bg_dark'],
            fg=self.colors['fg_secondary'],
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
        self.status_label = tk.Label(
            main_frame,
            text="",
            font=('Segoe UI', 10, 'italic'),
            bg=self.colors['bg_dark'],
            fg=self.colors['accent'],
        )
        self.status_label.grid(row=4, column=0, columnspan=2, pady=15)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=(15, 0))

        self.save_button = tk.Button(
            button_frame, text="✓ Save Changes", command=self.save_changes,
            state="disabled", font=('Segoe UI', 10, 'bold'),
            bg=self.colors['success'], fg='#ffffff',
            activebackground='#3da88a', activeforeground='#ffffff',
            borderwidth=0, relief='flat', cursor='hand2',
            padx=20, pady=10
        )
        self.save_button.grid(row=0, column=0, padx=10)

        cancel_button = tk.Button(
            button_frame, text="✕ Cancel", command=self.cancel,
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['bg_light'], fg=self.colors['fg_primary'],
            activebackground=self.colors['bg_medium'], activeforeground=self.colors['fg_primary'],
            borderwidth=0, relief='flat', cursor='hand2',
            padx=20, pady=10
        )
        cancel_button.grid(row=0, column=1, padx=10)

        # Store new bindings
        self.new_bindings = current_bindings.copy()

        # Center dialog
        self.dialog.update_idletasks()
        width = self.dialog.winfo_reqwidth()
        height = self.dialog.winfo_reqheight()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")

    def _apply_dark_theme(self) -> None:
        """Apply dark theme to dialog widgets."""
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('Dialog.TFrame',
                        background=self.colors['bg_dark'])
        style.configure('Dialog.TLabel',
                        background=self.colors['bg_dark'],
                        foreground=self.colors['fg_primary'],
                        font=('Segoe UI', 10))
        style.configure('Dialog.TLabelframe',
                        background=self.colors['bg_dark'],
                        foreground=self.colors['fg_primary'],
                        borderwidth=1,
                        relief='solid',
                        bordercolor=self.colors['border'])
        style.configure('Dialog.TLabelframe.Label',
                        background=self.colors['bg_dark'],
                        foreground=self.colors['accent'],
                        font=('Segoe UI', 10, 'bold'))

    def _create_key_section(
        self, parent: ttk.Frame, title: str, key_type: str, current_key: str, row: int
    ) -> None:
        """Create a key configuration section."""
        frame = ttk.LabelFrame(
            parent, text=title, padding="15", style='Dialog.TLabelframe')
        frame.grid(row=row, column=0, columnspan=2,
                   sticky=(tk.W, tk.E), pady=8)

        tk.Label(
            frame, text="Current:", font=('Segoe UI', 10),
            bg=self.colors['bg_dark'], fg=self.colors['fg_secondary']
        ).grid(row=0, column=0, sticky=tk.W, padx=5)

        # Store label references
        if key_type == "start":
            self.start_current_label = tk.Label(
                frame, text=current_key.upper(), font=('Segoe UI', 10, 'bold'),
                bg=self.colors['bg_dark'], fg=self.colors['success']
            )
            self.start_current_label.grid(row=0, column=1, sticky=tk.W, padx=5)

            self.start_button = tk.Button(
                frame, text="Set New Key", command=lambda: self.capture_key("start"),
                font=('Segoe UI', 9, 'bold'),
                bg=self.colors['accent'], fg='#ffffff',
                activebackground=self.colors['accent_hover'], activeforeground='#ffffff',
                borderwidth=0, relief='flat', cursor='hand2',
                padx=15, pady=8
            )
            self.start_button.grid(row=0, column=2, padx=10)

            self.start_new_label = tk.Label(
                frame, text="", font=('Segoe UI', 10, 'bold'),
                bg=self.colors['bg_dark'], fg=self.colors['success']
            )
            self.start_new_label.grid(row=0, column=3, sticky=tk.W, padx=5)
        else:
            self.stop_current_label = tk.Label(
                frame, text=current_key.upper(), font=('Segoe UI', 10, 'bold'),
                bg=self.colors['bg_dark'], fg=self.colors['error']
            )
            self.stop_current_label.grid(row=0, column=1, sticky=tk.W, padx=5)

            self.stop_button = tk.Button(
                frame, text="Set New Key", command=lambda: self.capture_key("stop"),
                font=('Segoe UI', 9, 'bold'),
                bg=self.colors['accent'], fg='#ffffff',
                activebackground=self.colors['accent_hover'], activeforeground='#ffffff',
                borderwidth=0, relief='flat', cursor='hand2',
                padx=15, pady=8
            )
            self.stop_button.grid(row=0, column=2, padx=10)

            self.stop_new_label = tk.Label(
                frame, text="", font=('Segoe UI', 10, 'bold'),
                bg=self.colors['bg_dark'], fg=self.colors['error']
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
                text="⌨ Press a key for START macro...", fg=self.colors['accent']
            )
        else:
            self.stop_button.config(state="disabled")
            self.status_label.config(
                text="⌨ Press a key for STOP macro...", fg=self.colors['accent']
            )

        # Use on_press and store the hook handle for later removal
        self.key_hook = keyboard.on_press(self.on_key_press, suppress=True)

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
                text="⚠ ESC is not allowed. Please choose another key.",
                fg=self.colors['error']
            )
            self.capturing = False
            # Unhook using the stored hook handle
            if self.key_hook:
                keyboard.unhook(self.key_hook)
                self.key_hook = None
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
            text=f"✓ Key '{key_name.upper()}' assigned successfully!",
            fg=self.colors['success']
        )

        # Enable save button
        self.save_button.config(state="normal")

        # Stop capturing
        self.capturing = False
        # Unhook using the stored hook handle
        if self.key_hook:
            keyboard.unhook(self.key_hook)
            self.key_hook = None

    def save_changes(self) -> None:
        """Save the new key bindings."""
        # Clean up any remaining keyboard hooks from this dialog
        if self.key_hook:
            keyboard.unhook(self.key_hook)
            self.key_hook = None
        self.result = self.new_bindings
        self.dialog.destroy()

    def cancel(self) -> None:
        """Cancel without saving."""
        # Clean up any remaining keyboard hooks from this dialog
        if self.key_hook:
            keyboard.unhook(self.key_hook)
            self.key_hook = None
        self.result = None
        self.dialog.destroy()

    def show(self) -> Optional[Dict[str, str]]:
        """Show the dialog and return the result.

        Returns:
            New key bindings if saved, None if cancelled.
        """
        self.dialog.wait_window()
        return self.result
