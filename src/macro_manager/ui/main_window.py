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
from macro_manager.macros import (
    get_macro_by_name,
    get_all_macro_names,
    save_recorded_macro,
    delete_recorded_macro,
    is_recorded_macro,
    reload_recorded_macros
)
from macro_manager.ui.key_binding_dialog import KeyBindingDialog
from macro_manager.ui.macro_recording_dialog import MacroRecordingDialog
from macro_manager.ui.stdout_redirector import StdoutRedirector
from macro_manager.ui.theme import COLORS
from macro_manager.utils.window_utils import find_game_window
from macro_manager.utils.auto_updater import get_current_version

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
        self.update_callback = None  # Callback for checking updates

        # Configure window - optimized size with wider log
        self.root.title("MacroManager")
        width = self.config.get("window_width", 1000)
        height = self.config.get("window_height", 820)

        # Center window on screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        self.root.resizable(True, True)
        self.root.minsize(550, 820)

        # Store colors from centralized theme
        self.colors = COLORS

        # Apply modern dark theme
        self._apply_dark_theme()

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

    def _apply_dark_theme(self) -> None:
        """Apply modern dark theme to the application."""
        # Configure root window
        self.root.configure(bg=self.colors['bg_dark'])

        # Configure ttk style
        style = ttk.Style()

        # Use a modern theme as base
        style.theme_use('clam')

        # Configure TFrame
        style.configure('TFrame',
                        background=self.colors['bg_dark'])

        # Configure TLabel
        style.configure('TLabel',
                        background=self.colors['bg_dark'],
                        foreground=self.colors['fg_primary'],
                        font=('Segoe UI', 10))

        # Configure title labels - more compact
        style.configure('Title.TLabel',
                        background=self.colors['bg_dark'],
                        foreground=self.colors['accent'],
                        font=('Segoe UI', 14, 'bold'))

        # Configure section labels
        style.configure('Section.TLabel',
                        background=self.colors['bg_dark'],
                        foreground=self.colors['fg_primary'],
                        font=('Segoe UI', 11, 'bold'))

        # Configure status labels
        style.configure('Status.TLabel',
                        background=self.colors['bg_medium'],
                        foreground=self.colors['success'],
                        font=('Segoe UI', 10, 'bold'))

        # Configure TButton
        style.configure('TButton',
                        background=self.colors['accent'],
                        foreground=self.colors['fg_primary'],
                        borderwidth=0,
                        focuscolor=self.colors['accent_hover'],
                        font=('Segoe UI', 10, 'bold'),
                        padding=(20, 10))
        style.map('TButton',
                  background=[('active', self.colors['accent_hover']),
                              ('pressed', self.colors['accent_hover'])])

        # Configure TCombobox
        style.configure('TCombobox',
                        fieldbackground=self.colors['bg_light'],
                        background=self.colors['bg_light'],
                        foreground=self.colors['fg_primary'],
                        arrowcolor=self.colors['fg_primary'],
                        borderwidth=1,
                        relief='flat')

        # Configure TLabelframe
        style.configure('TLabelframe',
                        background=self.colors['bg_dark'],
                        foreground=self.colors['fg_primary'],
                        borderwidth=1,
                        relief='solid',
                        bordercolor=self.colors['border'])
        style.configure('TLabelframe.Label',
                        background=self.colors['bg_dark'],
                        foreground=self.colors['accent'],
                        font=('Segoe UI', 10, 'bold'))

        # Configure version badge style
        style.configure('Version.TLabel',
                        background=self.colors['accent'],
                        foreground='#ffffff',
                        font=('Segoe UI', 9, 'bold'),
                        padding=(8, 4))

        # Configure Scrollbar
        style.configure('Vertical.TScrollbar',
                        background=self.colors['bg_light'],
                        troughcolor=self.colors['bg_medium'],
                        borderwidth=0,
                        arrowcolor=self.colors['fg_primary'])

    def create_widgets(self) -> None:
        """Create all UI widgets."""
        # Main container with two columns - reduced padding
        main_container = ttk.Frame(self.root, padding="15")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_container.grid_columnconfigure(
            0, weight=1)  # Left column (controls)
        main_container.grid_columnconfigure(1, weight=1)  # Right column (log)
        main_container.grid_rowconfigure(0, weight=1)

        # Left panel - controls
        left_frame = ttk.Frame(main_container)
        left_frame.grid(row=0, column=0, sticky=(
            tk.W, tk.E, tk.N, tk.S), padx=(0, 8))
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_rowconfigure(7, weight=1)  # Footer row

        # Title with version badge - more compact
        title_frame = ttk.Frame(left_frame)
        title_frame.grid(row=0, column=0, columnspan=2, pady=(0, 12))

        title_label = ttk.Label(
            title_frame, text="MacroManager", style='Title.TLabel'
        )
        title_label.pack(side=tk.LEFT, padx=(0, 10))

        # Version badge
        version_badge = tk.Label(
            title_frame,
            text=f"v{get_current_version()}",
            bg=self.colors['accent'],
            fg='#ffffff',
            font=('Segoe UI', 9, 'bold'),
            padx=8,
            pady=4,
            borderwidth=0,
            relief='flat'
        )
        version_badge.pack(side=tk.LEFT)

        # Macro selection - more compact
        ttk.Label(
            left_frame, text="Select Macro:", style='Section.TLabel'
        ).grid(row=1, column=0, sticky=tk.W, pady=(0, 5))

        self.macro_combo = ttk.Combobox(
            left_frame, width=40, font=('Segoe UI', 9))
        self.macro_combo["values"] = get_all_macro_names()
        self.macro_combo.grid(
            row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 8), padx=3
        )
        if self.macro_combo["values"]:
            self.macro_combo.current(0)
        self.macro_combo.bind("<<ComboboxSelected>>", self.update_description)

        # Configure combobox styling
        self.root.option_add(
            '*TCombobox*Listbox.background', self.colors['bg_light'])
        self.root.option_add('*TCombobox*Listbox.foreground',
                             self.colors['fg_primary'])
        self.root.option_add(
            '*TCombobox*Listbox.selectBackground', self.colors['accent'])
        self.root.option_add(
            '*TCombobox*Listbox.selectForeground', self.colors['fg_primary'])

        # Description - more compact
        ttk.Label(
            left_frame, text="Description:", style='Section.TLabel'
        ).grid(row=3, column=0, sticky=tk.W, pady=(8, 5))

        self.description_text = tk.Text(
            left_frame, height=3, wrap=tk.WORD, font=('Segoe UI', 9),
            bg=self.colors['bg_medium'], fg=self.colors['fg_primary'],
            borderwidth=1, relief='solid', highlightthickness=0,
            insertbackground=self.colors['fg_primary'], padx=10, pady=8
        )
        self.description_text.grid(
            row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 8), padx=3
        )
        self.description_text.config(state=tk.DISABLED)

        # Combined Status and Controls frame
        self._create_combined_status_frame(left_frame, row=5)

        # Buttons
        self._create_button_frame(left_frame, row=6)

        # Footer (left side)
        self._create_footer(left_frame, row=7)

        # Right panel - log
        self._create_log_frame(main_container, row=0, column=1)

        # Update description
        self.update_description(None)

    def _create_combined_status_frame(self, parent: ttk.Frame, row: int) -> None:
        """Create a combined status and controls frame for space efficiency."""
        combined_frame = ttk.LabelFrame(
            parent, text="Status & Controls", padding="10")
        combined_frame.grid(row=row, column=0, columnspan=2,
                            sticky=(tk.W, tk.E), pady=(0, 8), padx=3)
        combined_frame.grid_columnconfigure(1, weight=1)

        # Status section - compact 2x2 grid
        status_labels = [
            ("State:", "status", "Idle", self.colors['fg_secondary']),
            ("Window:", "window", "Not detected", self.colors['warning']),
            ("Step:", "step", "--", self.colors['fg_secondary']),
            ("Action:", "action", "--", self.colors['fg_secondary'])
        ]

        for idx, (label_text, attr_name, default_text, fg_color) in enumerate(status_labels):
            row_pos = idx // 2
            col_pos = (idx % 2) * 2

            ttk.Label(combined_frame, text=label_text,
                      font=('Segoe UI', 9)).grid(
                row=row_pos, column=col_pos, sticky=tk.W, padx=(3, 5), pady=3
            )

            label = tk.Label(
                combined_frame, text=default_text,
                font=('Segoe UI', 9, 'bold'),
                bg=self.colors['bg_dark'],
                fg=fg_color
            )
            label.grid(row=row_pos, column=col_pos + 1,
                       sticky=tk.W, padx=(0, 10), pady=3)
            setattr(self, f"{attr_name}_label", label)

        # Separator
        ttk.Separator(combined_frame, orient='horizontal').grid(
            row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=8
        )

        # Loop Controls Section
        ttk.Label(combined_frame, text="Loop Settings:",
                  font=('Segoe UI', 9, 'bold')).grid(
            row=3, column=0, columnspan=4, sticky=tk.W, padx=3, pady=(0, 5)
        )

        # Loop checkbox
        self.loop_var = tk.BooleanVar(value=True)
        self.loop_checkbox = tk.Checkbutton(
            combined_frame,
            text="Enable Looping",
            variable=self.loop_var,
            command=self._on_loop_changed,
            font=('Segoe UI', 9),
            bg=self.colors['bg_dark'],
            fg=self.colors['fg_primary'],
            selectcolor=self.colors['bg_light'],
            activebackground=self.colors['bg_dark'],
            activeforeground=self.colors['fg_primary'],
            cursor='hand2'
        )
        self.loop_checkbox.grid(row=4, column=0, columnspan=2,
                                sticky=tk.W, padx=3, pady=3)

        # Loop count frame - modernized
        loop_count_frame = tk.Frame(combined_frame, bg=self.colors['bg_dark'])
        loop_count_frame.grid(
            row=4, column=2, columnspan=2, sticky=tk.W, padx=3, pady=3)

        ttk.Label(loop_count_frame, text="Repeat:",
                  font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 8))

        # Loop count spinbox - modernized with better styling
        self.loop_count_var = tk.StringVar(value="∞")

        # Create a frame for the spinbox to add border
        spinbox_container = tk.Frame(
            loop_count_frame,
            bg=self.colors['bg_light'],
            highlightthickness=1,
            highlightbackground=self.colors['border'],
            highlightcolor=self.colors['accent']
        )
        spinbox_container.pack(side=tk.LEFT, padx=(0, 8))

        self.loop_count_spinbox = tk.Spinbox(
            spinbox_container,
            from_=1,
            to=9999,
            width=6,
            textvariable=self.loop_count_var,
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['bg_light'],
            fg=self.colors['fg_primary'],
            buttonbackground=self.colors['accent'],
            insertbackground=self.colors['fg_primary'],
            relief='flat',
            borderwidth=0,
            validate='key',
            validatecommand=(self.root.register(
                self._validate_loop_count), '%P')
        )
        self.loop_count_spinbox.pack(padx=2, pady=2)

        # Infinite button - modernized as toggle button
        self.loop_infinite_var = tk.BooleanVar(value=True)
        self.loop_infinite_button = tk.Button(
            loop_count_frame,
            text="∞ Infinite",
            command=self._on_infinite_changed,
            font=('Segoe UI', 9, 'bold'),
            bg=self.colors['accent'],
            fg='#ffffff',
            activebackground=self.colors['accent_hover'],
            activeforeground='#ffffff',
            borderwidth=0,
            relief='flat',
            cursor='hand2',
            padx=12,
            pady=5
        )
        self.loop_infinite_button.pack(side=tk.LEFT)

        # Initialize spinbox state
        self._on_infinite_changed()

        # Separator
        ttk.Separator(combined_frame, orient='horizontal').grid(
            row=5, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=8
        )

        # Key bindings section - compact (only show start/stop) - centered
        bindings = self.config.key_bindings

        # Create a container for centered key bindings
        keys_container = ttk.Frame(combined_frame)
        keys_container.grid(row=6, column=0, columnspan=4,
                            sticky=(tk.W, tk.E), pady=3)
        keys_container.grid_columnconfigure(0, weight=1)
        keys_container.grid_columnconfigure(1, weight=0)
        keys_container.grid_columnconfigure(2, weight=0)
        keys_container.grid_columnconfigure(3, weight=1)

        keys_info = [
            (f"Start: {bindings['start_key'].upper()}",
             self.colors['success']),
            (f"Stop: {bindings['stop_key'].upper()}", self.colors['error'])
        ]

        for idx, (text, color) in enumerate(keys_info):
            col_pos = idx + 1  # Start at column 1 (skip column 0 for spacing)

            label = tk.Label(
                keys_container,
                text=text,
                font=('Segoe UI', 9),
                bg=self.colors['bg_dark'],
                fg=color
            )
            label.grid(row=0, column=col_pos, padx=8, pady=3)

            if idx == 0:
                self.start_key_label = label
            elif idx == 1:
                self.stop_key_label = label

    def _create_button_frame(self, parent: ttk.Frame, row: int) -> None:
        """Create the button control frame with organized layout."""
        button_container = ttk.Frame(parent)
        button_container.grid(row=row, column=0, columnspan=2,
                              pady=(0, 8), sticky=(tk.W, tk.E))
        button_container.grid_columnconfigure(0, weight=1)

        # Primary Controls - Start/Stop (most prominent)
        primary_frame = ttk.LabelFrame(
            button_container, text="Macro Control", padding="10")
        primary_frame.grid(row=0, column=0, sticky=(
            tk.W, tk.E), pady=(0, 8), padx=3)
        primary_frame.grid_columnconfigure((0, 1), weight=1)

        # Start button - larger and more prominent
        self.start_button = tk.Button(
            primary_frame, text="▶  START", command=self.start_macro,
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['success'], fg='#ffffff',
            activebackground='#3da88a', activeforeground='#ffffff',
            borderwidth=0, relief='flat', cursor='hand2',
            pady=10
        )
        self.start_button.grid(row=0, column=0, padx=3, sticky=(tk.W, tk.E))

        # Stop button - larger and more prominent
        self.stop_button = tk.Button(
            primary_frame, text="■  STOP", command=self.stop_macro,
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['error'], fg='#ffffff',
            activebackground='#d66f5e', activeforeground='#ffffff',
            borderwidth=0, relief='flat', cursor='hand2',
            pady=10
        )
        self.stop_button.grid(row=0, column=1, padx=3, sticky=(tk.W, tk.E))

        # Secondary Controls - Macro Management
        secondary_frame = ttk.LabelFrame(
            button_container, text="Macro Management", padding="10")
        secondary_frame.grid(row=1, column=0, sticky=(
            tk.W, tk.E), pady=(0, 8), padx=3)
        secondary_frame.grid_columnconfigure((0, 1), weight=1)

        # Record button
        self.record_button = tk.Button(
            secondary_frame, text="⏺  Record", command=self.record_macro,
            font=('Segoe UI', 9, 'bold'),
            bg=self.colors['warning'], fg='#ffffff',
            activebackground='#b57860', activeforeground='#ffffff',
            borderwidth=0, relief='flat', cursor='hand2',
            pady=8
        )
        self.record_button.grid(row=0, column=0, padx=3, sticky=(tk.W, tk.E))

        # Delete button
        self.delete_button = tk.Button(
            secondary_frame, text="🗑  Delete", command=self.delete_macro,
            font=('Segoe UI', 9, 'bold'),
            bg='#8b4545', fg='#ffffff',
            activebackground='#6f3636', activeforeground='#ffffff',
            borderwidth=0, relief='flat', cursor='hand2',
            pady=8
        )
        self.delete_button.grid(row=0, column=1, padx=3, sticky=(tk.W, tk.E))

        # Tertiary Controls - Settings
        tertiary_frame = ttk.LabelFrame(
            button_container, text="Settings", padding="10")
        tertiary_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=3)
        tertiary_frame.grid_columnconfigure((0, 1), weight=1)

        # Change keys button
        self.change_keys_button = tk.Button(
            tertiary_frame, text="⚙  Keys", command=self.change_keys,
            font=('Segoe UI', 9, 'bold'),
            bg=self.colors['accent'], fg='#ffffff',
            activebackground=self.colors['accent_hover'], activeforeground='#ffffff',
            borderwidth=0, relief='flat', cursor='hand2',
            pady=8
        )
        self.change_keys_button.grid(
            row=1, column=0, padx=3, sticky=(tk.W, tk.E))

        # Check updates button
        self.check_updates_button = tk.Button(
            tertiary_frame, text="🔄  Updates", command=self.check_for_updates,
            font=('Segoe UI', 9, 'bold'),
            bg=self.colors['bg_light'], fg=self.colors['fg_primary'],
            activebackground=self.colors['bg_medium'], activeforeground=self.colors['fg_primary'],
            borderwidth=0, relief='flat', cursor='hand2',
            pady=8
        )
        self.check_updates_button.grid(
            row=1, column=1, padx=3, sticky=(tk.W, tk.E))

        # Update channel selection frame - modernized
        update_channel_frame = tk.Frame(
            tertiary_frame, bg=self.colors['bg_dark'])
        update_channel_frame.grid(
            row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(8, 0), padx=3)
        update_channel_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(update_channel_frame, text="Update Channel:",
                  font=('Segoe UI', 9, 'bold')).grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10))

        # Create a container for channel buttons
        channel_buttons_frame = tk.Frame(
            update_channel_frame, bg=self.colors['bg_dark'])
        channel_buttons_frame.grid(row=0, column=1, sticky=tk.W)

        # Store channel selection
        self.update_channel_var = tk.StringVar(
            value=self.config.get("update_channel", "stable"))

        # Create modern toggle buttons for channels
        self.channel_buttons = {}
        channels = [
            ("stable", "🛡 Stable", "Official releases only"),
            ("beta", "🧪 Beta", "Includes pre-releases")
        ]

        for idx, (channel, label, tooltip) in enumerate(channels):
            btn = tk.Button(
                channel_buttons_frame,
                text=label,
                command=lambda c=channel: self._on_channel_button_clicked(c),
                font=('Segoe UI', 9, 'bold'),
                cursor='hand2',
                relief='flat',
                borderwidth=0,
                padx=12,
                pady=6
            )
            btn.grid(row=0, column=idx, padx=(0, 5))
            self.channel_buttons[channel] = btn

            # Add tooltip on hover
            btn.bind('<Enter>', lambda e,
                     t=tooltip: self._show_channel_tooltip(e, t))
            btn.bind('<Leave>', lambda e: self._hide_channel_tooltip())

        # Update button states
        self._update_channel_button_states()

        # Channel info label with modern styling
        channel_info = tk.Label(
            update_channel_frame,
            text="ⓘ",
            font=('Segoe UI', 11, 'bold'),
            bg=self.colors['bg_dark'],
            fg=self.colors['accent'],
            cursor='hand2'
        )
        channel_info.grid(row=0, column=2, padx=(8, 0))
        channel_info.bind("<Button-1>", lambda e: messagebox.showinfo(
            "Update Channels",
            "🛡 Stable Channel:\n"
            "• Only official stable releases\n"
            "• Recommended for most users\n"
            "• Maximum stability\n\n"
            "🧪 Beta Channel:\n"
            "• Includes pre-releases\n"
            "• Early access to new features\n"
            "• May contain bugs or incomplete features\n"
            "• For testing and feedback",
            parent=self.root
        ))

    def _create_log_frame(self, parent: ttk.Frame, row: int, column: int = 0) -> None:
        """Create the log output frame."""
        self.log_frame = ttk.LabelFrame(parent, text="Log", padding="10")
        self.log_frame.grid(row=row, column=column, sticky=(
            tk.W, tk.E, tk.N, tk.S), padx=(8, 0))
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(0, weight=1)

        self.log_text = tk.Text(
            self.log_frame, width=55, wrap=tk.WORD, font=('Consolas', 8),
            bg=self.colors['bg_medium'], fg=self.colors['fg_primary'],
            borderwidth=0, relief='flat', highlightthickness=0,
            insertbackground=self.colors['fg_primary'], padx=8, pady=8
        )
        self.log_text.grid(row=0, column=0, sticky=(
            tk.W, tk.E, tk.N, tk.S), pady=3, padx=3)

        log_scrollbar = ttk.Scrollbar(
            self.log_frame, orient="vertical", command=self.log_text.yview
        )
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text.configure(yscrollcommand=log_scrollbar.set)

    def _create_footer(self, parent: ttk.Frame, row: int) -> None:
        """Create the footer section."""
        footer_frame = ttk.Frame(parent)
        footer_frame.grid(row=row, column=0, columnspan=2,
                          sticky=(tk.W, tk.E, tk.S), pady=(8, 0))
        footer_frame.grid_columnconfigure(0, weight=1)

        tk.Label(
            footer_frame, text="© 2025 MacroManager by panteLx",
            font=('Segoe UI', 8),
            bg=self.colors['bg_dark'], fg=self.colors['fg_secondary'],
            anchor="center"
        ).grid(row=0, column=0, sticky=(tk.W, tk.E))

    def _validate_loop_count(self, value: str) -> bool:
        """Validate loop count input.

        Args:
            value: Input value to validate.

        Returns:
            True if valid, False otherwise.
        """
        if value == "" or value == "∞":
            return True
        try:
            int_val = int(value)
            return 1 <= int_val <= 9999
        except ValueError:
            return False

    def _on_loop_changed(self) -> None:
        """Handle loop checkbox state change."""
        is_looping = self.loop_var.get()

        # Enable/disable loop count controls
        state = tk.NORMAL if is_looping else tk.DISABLED
        self.loop_count_spinbox.config(state=state)
        self.loop_infinite_button.config(state=state)

    def _on_infinite_changed(self) -> None:
        """Handle infinite loop toggle button state change."""
        is_infinite = self.loop_infinite_var.get()

        # Toggle the state
        self.loop_infinite_var.set(not is_infinite)
        is_infinite = not is_infinite

        if is_infinite:
            self.loop_count_var.set("∞")
            self.loop_count_spinbox.config(
                state=tk.DISABLED)
            # Update button appearance for active state
            self.loop_infinite_button.config(
                bg=self.colors['accent'],
                fg='#ffffff',
                text="∞ Infinite"
            )
        else:
            self.loop_count_var.set("1")
            self.loop_count_spinbox.config(state=tk.NORMAL)
            # Update button appearance for inactive state
            self.loop_infinite_button.config(
                bg=self.colors['bg_light'],
                fg=self.colors['fg_primary'],
                text="∞ Infinite"
            )

    def _on_update_channel_changed(self, event=None) -> None:
        """Handle update channel selection change."""
        channel = self.update_channel_var.get()
        self.config.set("update_channel", channel)
        logger.info(f"Update channel changed to: {channel}")

    def _on_channel_button_clicked(self, channel: str) -> None:
        """Handle channel button click."""
        # If switching to beta, show confirmation dialog
        if channel == "beta" and self.update_channel_var.get() != "beta":
            result = messagebox.askyesno(
                "Switch to Beta Channel?",
                "⚠️ Important Notes About Beta Channel:\n\n"
                "• Beta releases may contain bugs or incomplete features\n"
                "• Updates may be unstable or cause unexpected behavior\n"
                "• Not recommended for critical use cases\n"
                "• You can switch back to Stable channel at any time\n\n"
                "Are you sure you want to switch to the Beta channel?",
                icon='warning',
                parent=self.root
            )

            if not result:
                # User cancelled, don't change channel
                logger.info("User cancelled switch to beta channel")
                return

        # Update the channel
        self.update_channel_var.set(channel)
        self._update_channel_button_states()
        self._on_update_channel_changed()

    def _update_channel_button_states(self) -> None:
        """Update the visual state of channel buttons based on selection."""
        selected = self.update_channel_var.get()

        for channel, btn in self.channel_buttons.items():
            if channel == selected:
                # Selected state - accent color
                btn.config(
                    bg=self.colors['accent'],
                    fg='#ffffff',
                    activebackground=self.colors['accent_hover'],
                    activeforeground='#ffffff'
                )
            else:
                # Unselected state - muted
                btn.config(
                    bg=self.colors['bg_light'],
                    fg=self.colors['fg_secondary'],
                    activebackground=self.colors['bg_medium'],
                    activeforeground=self.colors['fg_primary']
                )

    def _show_channel_tooltip(self, event, text: str) -> None:
        """Show tooltip for channel button."""
        # Create tooltip if it doesn't exist
        if not hasattr(self, '_channel_tooltip'):
            self._channel_tooltip = tk.Label(
                self.root,
                text=text,
                font=('Segoe UI', 8),
                bg=self.colors['bg_medium'],
                fg=self.colors['fg_primary'],
                relief='solid',
                borderwidth=1,
                padx=8,
                pady=4
            )
        else:
            self._channel_tooltip.config(text=text)

        # Position tooltip near cursor
        x = event.widget.winfo_rootx() + event.widget.winfo_width() // 2
        y = event.widget.winfo_rooty() - 30
        self._channel_tooltip.place(x=x, y=y)
        self._channel_tooltip.lift()

    def _hide_channel_tooltip(self) -> None:
        """Hide channel tooltip."""
        if hasattr(self, '_channel_tooltip'):
            self._channel_tooltip.place_forget()

    def _get_loop_settings(self) -> tuple:
        """Get current loop settings from GUI.

        Returns:
            Tuple of (loop: bool, loop_count: int or None)
        """
        loop = self.loop_var.get()

        if not loop:
            return (False, None)

        if self.loop_infinite_var.get():
            return (True, None)

        try:
            count_str = self.loop_count_var.get()
            if count_str == "∞":
                return (True, None)
            loop_count = int(count_str)
            return (True, loop_count if loop_count > 0 else None)
        except (ValueError, AttributeError):
            return (True, None)

    def update_description(self, event) -> None:
        """Update the macro description display."""
        selected_name = self.macro_combo.get()
        selected_macro = get_macro_by_name(selected_name)

        self.description_text.config(state=tk.NORMAL)
        self.description_text.delete(1.0, tk.END)
        if selected_macro:
            self.description_text.insert(tk.END, selected_macro.description)
        self.description_text.config(state=tk.DISABLED)

        # Update loop settings from selected macro if it's a RecordedMacro
        from macro_manager.macros.recorded_macro import RecordedMacro
        if isinstance(selected_macro, RecordedMacro):
            # Set loop checkbox
            self.loop_var.set(selected_macro.loop)

            # Set loop count
            if selected_macro.loop_count is None:
                self.loop_infinite_var.set(True)
                self.loop_count_var.set("∞")
            else:
                self.loop_infinite_var.set(False)
                self.loop_count_var.set(str(selected_macro.loop_count))

            # Update UI state
            self._on_loop_changed()
            self._on_infinite_changed()
        else:
            # Reset to defaults for non-recorded macros
            self.loop_var.set(True)
            self.loop_infinite_var.set(True)
            self.loop_count_var.set("∞")
            self._on_loop_changed()
            self._on_infinite_changed()

    def set_key_bindings(self) -> None:
        """Set up keyboard shortcuts."""
        # Remove old hotkeys first
        keyboard.unhook_all()
        bindings = self.config.key_bindings

        try:
            # Use suppress=False to allow the event to propagate
            # This prevents interference between button clicks and hotkeys
            keyboard.add_hotkey(
                bindings["start_key"], self._hotkey_start_macro, suppress=False)
            keyboard.add_hotkey(
                bindings["stop_key"], self._hotkey_stop_macro, suppress=False)
            logger.info(f"Key bindings set: {bindings}")
        except Exception as e:
            logger.error(f"Failed to set key bindings: {e}")
            messagebox.showwarning(
                "Key Binding Error",
                f"Failed to set key bindings: {e}\n\nPlease try different keys."
            )

    def _hotkey_start_macro(self) -> None:
        """Hotkey handler for starting macro (prevents re-entrancy issues)."""
        # Schedule on main thread to avoid threading issues
        self.root.after(0, self.start_macro)

    def _hotkey_stop_macro(self) -> None:
        """Hotkey handler for stopping macro (prevents re-entrancy issues)."""
        # Schedule on main thread to avoid threading issues
        self.root.after(0, self.stop_macro)

    def update_status(self, current_step: str, total_steps: str, message: str) -> None:
        """Update GUI status labels (called from any thread)."""
        self.root.after(
            0, lambda: self._update_status_labels(
                current_step, total_steps, message)
        )

    def _update_status_labels(self, current_step: str, total_steps: str, message: str) -> None:
        """Update GUI elements (must be called from main thread)."""
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

        # Apply loop settings from GUI to RecordedMacro instances
        from macro_manager.macros.recorded_macro import RecordedMacro
        if isinstance(macro, RecordedMacro):
            loop, loop_count = self._get_loop_settings()
            macro.set_loop(loop, loop_count)

            # Log the settings
            if not loop:
                logger.info("Loop settings: Run once")
            elif loop_count is None:
                logger.info("Loop settings: Infinite loop")
            else:
                logger.info(f"Loop settings: Loop {loop_count} times")

        # Clear log
        self.log_text.delete(1.0, tk.END)

        # Redirect stdout for UI logging
        stdout_redirector = StdoutRedirector(self.log_text, self.update_status)
        sys.stdout = stdout_redirector
        sys.stderr = stdout_redirector

        # Try to find game window
        try:
            self.controller.start_macro(macro, game_window)
            self.status_label.config(text="Running", fg=self.colors['success'])
            self.step_label.config(text="--")
            self.action_label.config(text="Starting...")
            logger.info(f"Started macro: {macro.name}")
        except MacroExecutionError as e:
            messagebox.showerror("Error", str(e))
            logger.error(f"Failed to start macro: {e}")

    def stop_macro(self) -> None:
        """Stop the running macro."""
        self.controller.stop_macro()
        self.status_label.config(text="Stopped", fg=self.colors['error'])
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

        # Always re-register hotkeys after dialog closes, even if cancelled
        # The dialog unhooks all keyboard events, so we need to restore them
        if new_bindings is None:
            # User cancelled, restore old bindings
            self.set_key_bindings()
            return

        # Update configuration
        self.config.update_key_bindings(
            new_bindings["start_key"], new_bindings["stop_key"]
        )

        # Update key bindings
        self.set_key_bindings()

        # Update UI labels
        self.start_key_label.config(
            text=f"Start: {new_bindings['start_key'].upper()}"
        )
        self.stop_key_label.config(
            text=f"Stop: {new_bindings['stop_key'].upper()}"
        )

        messagebox.showinfo("Success", "Key bindings updated successfully!")
        logger.info(f"Key bindings updated: {new_bindings}")

    def set_update_callback(self, callback) -> None:
        """Set the callback function for checking updates.

        Args:
            callback: Function to call when user wants to check for updates
        """
        self.update_callback = callback

    def check_for_updates(self) -> None:
        """Trigger a manual update check."""
        if self.update_callback:
            self.update_callback()
        else:
            messagebox.showinfo(
                "Check for Updates",
                "Update checking is not available at this time."
            )
            logger.warning("Update callback not set")

    def record_macro(self) -> None:
        """Open the macro recording dialog."""
        if self.controller.is_running():
            messagebox.showwarning(
                "Warning",
                "Please stop the running macro before recording a new one!"
            )
            return

        # Show recording dialog
        dialog = MacroRecordingDialog(self.root)
        recorded_macro = dialog.show()

        # Re-register hotkeys after dialog closes (just to be safe)
        self.set_key_bindings()

        if recorded_macro:
            # Save the macro
            success = save_recorded_macro(recorded_macro)

            if success:
                # Refresh macro list
                reload_recorded_macros()
                self.macro_combo["values"] = get_all_macro_names()

                # Select the newly created macro
                for i, name in enumerate(self.macro_combo["values"]):
                    if name == recorded_macro.name:
                        self.macro_combo.current(i)
                        self.update_description(None)
                        break

                messagebox.showinfo(
                    "Success",
                    f"Macro '{recorded_macro.name}' has been saved!\n\n"
                    "You can now select it from the dropdown and run it."
                )
                logger.info(
                    f"Recorded and saved new macro: {recorded_macro.name}")
            else:
                messagebox.showerror(
                    "Error",
                    f"Failed to save macro '{recorded_macro.name}'. Please try again."
                )
                logger.error(
                    f"Failed to save recorded macro: {recorded_macro.name}")

    def delete_macro(self) -> None:
        """Delete the currently selected macro (if it's a recorded macro)."""
        selected_name = self.macro_combo.get()

        if not selected_name:
            messagebox.showwarning(
                "No Macro Selected",
                "Please select a macro to delete."
            )
            return

        # Check if it's a recorded macro
        if not is_recorded_macro(selected_name):
            messagebox.showwarning(
                "Cannot Delete",
                "Only custom recorded macros can be deleted.\n\n"
                "Prebuilt macros are part of the application and cannot be removed."
            )
            return

        # Confirm deletion
        result = messagebox.askyesno(
            "Delete Macro",
            f"Are you sure you want to delete the macro '{selected_name}'?\n\n"
            "This action cannot be undone."
        )

        if result:
            success = delete_recorded_macro(selected_name)

            if success:
                # Refresh macro list
                reload_recorded_macros()
                self.macro_combo["values"] = get_all_macro_names()

                # Select first macro if available
                if self.macro_combo["values"]:
                    self.macro_combo.current(0)
                    self.update_description(None)

                messagebox.showinfo(
                    "Success",
                    f"Macro '{selected_name}' has been deleted."
                )
                logger.info(f"Deleted macro: {selected_name}")
            else:
                messagebox.showerror(
                    "Error",
                    f"Failed to delete macro '{selected_name}'. Please try again."
                )
                logger.error(f"Failed to delete macro: {selected_name}")

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
