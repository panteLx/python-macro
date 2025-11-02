"""Dialog for recording custom macros."""

import logging
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Optional, Dict, Any, List
from pynput import keyboard

from macro_manager.core.macro_recorder import MacroRecorder
from macro_manager.macros.recorded_macro import RecordedMacro
from macro_manager.macros import get_all_macro_names
from macro_manager.ui.theme import COLORS

logger = logging.getLogger(__name__)


class MacroRecordingDialog:
    """Dialog window for recording a new macro."""

    def __init__(self, parent: tk.Tk):
        """Initialize the recording dialog.

        Args:
            parent: Parent window.
        """
        self.parent = parent
        self.recorder = MacroRecorder()
        self.recorded_macro: Optional[RecordedMacro] = None
        self.f9_listener: Optional[keyboard.Listener] = None

        # Use centralized color scheme
        self.colors = COLORS

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Record New Macro")
        self.dialog.geometry("600x500")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Use centralized color scheme
        self.colors = COLORS
        self.dialog.configure(bg=self.colors['bg_dark'])

        self._create_widgets()
        self._start_f9_listener()

        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - \
            (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - \
            (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def _create_widgets(self) -> None:
        """Create dialog widgets."""
        main_frame = tk.Frame(
            self.dialog, bg=self.colors['bg_dark'], padx=30, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title = tk.Label(
            main_frame,
            text="Record Custom Macro",
            font=('Segoe UI', 16, 'bold'),
            bg=self.colors['bg_dark'],
            fg=self.colors['accent']
        )
        title.pack(pady=(0, 20))

        # Instructions
        instructions = tk.Label(
            main_frame,
            text=(
                "1. Click 'Start Recording' or press F9 to begin\n"
                "2. Press the keys you want to record\n"
                "3. Press ESC to stop recording\n"
                "4. Review your recorded actions\n"
                "5. Save your macro with a unique name"
            ),
            font=('Segoe UI', 10),
            bg=self.colors['bg_dark'],
            fg=self.colors['fg_secondary'],
            justify=tk.LEFT
        )
        instructions.pack(pady=(0, 20))

        # Status label
        self.status_label = tk.Label(
            main_frame,
            text="Ready to record",
            font=('Segoe UI', 11, 'bold'),
            bg=self.colors['bg_dark'],
            fg=self.colors['success']
        )
        self.status_label.pack(pady=(0, 15))

        # Actions display
        actions_frame = tk.LabelFrame(
            main_frame,
            text="Recorded Actions",
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['bg_dark'],
            fg=self.colors['accent'],
            padx=10,
            pady=10
        )
        actions_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        self.actions_text = tk.Text(
            actions_frame,
            height=10,
            wrap=tk.WORD,
            font=('Consolas', 9),
            bg=self.colors['bg_medium'],
            fg=self.colors['fg_primary'],
            borderwidth=0,
            relief='flat',
            state=tk.DISABLED
        )
        self.actions_text.pack(fill=tk.BOTH, expand=True)

        # Button frame
        button_frame = tk.Frame(main_frame, bg=self.colors['bg_dark'])
        button_frame.pack(fill=tk.X)

        # Record button
        self.record_button = tk.Button(
            button_frame,
            text="▶ Start Recording",
            command=self._toggle_recording,
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['success'],
            fg='#ffffff',
            activebackground='#3da88a',
            activeforeground='#ffffff',
            borderwidth=0,
            relief='flat',
            cursor='hand2',
            padx=20,
            pady=10
        )
        self.record_button.pack(side=tk.LEFT, padx=5)

        # Save button
        self.save_button = tk.Button(
            button_frame,
            text="💾 Save Macro",
            command=self._save_macro,
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['accent'],
            fg='#ffffff',
            activebackground='#005a9e',
            activeforeground='#ffffff',
            borderwidth=0,
            relief='flat',
            cursor='hand2',
            padx=20,
            pady=10,
            state=tk.DISABLED
        )
        self.save_button.pack(side=tk.LEFT, padx=5)

        # Cancel button
        cancel_button = tk.Button(
            button_frame,
            text="✖ Cancel",
            command=self._cancel,
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['error'],
            fg='#ffffff',
            activebackground='#d66f5e',
            activeforeground='#ffffff',
            borderwidth=0,
            relief='flat',
            cursor='hand2',
            padx=20,
            pady=10
        )
        cancel_button.pack(side=tk.RIGHT, padx=5)

    def _start_f9_listener(self) -> None:
        """Start a global F9 key listener to trigger recording."""
        def on_press(key):
            try:
                # Get key name
                if hasattr(key, 'name'):
                    key_name = key.name.lower()
                else:
                    return

                # Check if F9 is pressed and we're not already recording
                if key_name == 'f9' and not self.recorder.is_recording():
                    # Trigger recording from UI thread
                    self.dialog.after(0, self._toggle_recording)
            except Exception as e:
                logger.error(f"Error in F9 listener: {e}")

        # Start the listener
        self.f9_listener = keyboard.Listener(on_press=on_press)
        self.f9_listener.start()
        logger.info("F9 global listener started")

    def _stop_f9_listener(self) -> None:
        """Stop the F9 global listener."""
        if self.f9_listener:
            self.f9_listener.stop()
            self.f9_listener = None
            logger.info("F9 global listener stopped")

    def _toggle_recording(self) -> None:
        """Toggle recording on/off."""
        if self.recorder.is_recording():
            # Stop recording
            actions = self.recorder.stop_recording()
            self._update_actions_display(actions)
            self.status_label.config(
                text=f"Recording stopped - {len(actions)} actions captured",
                fg=self.colors['fg_secondary']
            )
            self.record_button.config(
                text="▶ Start Recording", bg=self.colors['success'])
            self.save_button.config(
                state=tk.NORMAL if actions else tk.DISABLED)
        else:
            # Start recording immediately
            self.recorder.start_recording()
            self.status_label.config(
                text="Recording... Press ESC to stop",
                fg=self.colors['error']
            )
            self.record_button.config(
                text="■ Recording...", bg=self.colors['error'])
            self.save_button.config(state=tk.DISABLED)

            # Start a timer to check if recording stopped (by ESC key)
            self._check_recording_status()

    def _check_recording_status(self) -> None:
        """Check if recording has stopped (by ESC key)."""
        if self.recorder.is_recording():
            # Still recording, check again soon
            self.dialog.after(100, self._check_recording_status)
        else:
            # Recording stopped by ESC key
            actions = self.recorder.get_actions()
            self._update_actions_display(actions)
            self.status_label.config(
                text=f"Recording stopped - {len(actions)} actions captured",
                fg=self.colors['fg_secondary']
            )
            self.record_button.config(
                text="▶ Start Recording", bg=self.colors['success'])
            self.save_button.config(
                state=tk.NORMAL if actions else tk.DISABLED)

    def _update_actions_display(self, actions: List[Dict[str, Any]]) -> None:
        """Update the actions display text.

        Args:
            actions: List of recorded actions.
        """
        self.actions_text.config(state=tk.NORMAL)
        self.actions_text.delete(1.0, tk.END)

        if not actions:
            self.actions_text.insert(tk.END, "No actions recorded yet.")
        else:
            for i, action in enumerate(actions, 1):
                action_type = action.get("type")
                if action_type == "keypress":
                    text = f"{i}. Press key: {action['key'].upper()}\n"
                elif action_type == "keyhold":
                    text = f"{i}. Hold key: {action['key'].upper()} for {action['duration']:.2f}s\n"
                elif action_type == "sleep":
                    text = f"{i}. Wait: {action['delay']:.2f}s\n"
                else:
                    text = f"{i}. Unknown action\n"

                self.actions_text.insert(tk.END, text)

        self.actions_text.config(state=tk.DISABLED)

    def _save_macro(self) -> None:
        """Save the recorded macro."""
        actions = self.recorder.get_actions()

        if not actions:
            messagebox.showwarning(
                "No Actions",
                "Please record some actions before saving.",
                parent=self.dialog
            )
            return

        # Show custom save dialog
        save_dialog = MacroSaveDialog(self.dialog, self.colors)
        result = save_dialog.show()

        if not result:
            return

        name, description, loop = result

        # Create the recorded macro
        self.recorded_macro = RecordedMacro(name, description, actions)
        self.recorded_macro.set_loop(loop)

        # Stop the F9 listener before closing
        self._stop_f9_listener()

        # Don't show success message here - it will be shown in main_window after saving
        self.dialog.destroy()

    def _cancel(self) -> None:
        """Cancel and close the dialog."""
        if self.recorder.is_recording():
            self.recorder.stop_recording()

        self._stop_f9_listener()
        self.recorded_macro = None
        self.dialog.destroy()

    def show(self) -> Optional[RecordedMacro]:
        """Show the dialog and return the recorded macro.

        Returns:
            RecordedMacro if one was created, None otherwise.
        """
        self.dialog.wait_window()
        return self.recorded_macro


class MacroSaveDialog:
    """Dialog for inputting macro name, description, and loop settings."""

    def __init__(self, parent, colors):
        """Initialize the save dialog.

        Args:
            parent: Parent window.
            colors: Color scheme dictionary (unused, kept for compatibility).
        """
        self.parent = parent
        self.colors = COLORS
        self.result = None

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Save Macro")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg=self.colors['bg_dark'])

        self._create_widgets()

        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - \
            (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - \
            (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def _create_widgets(self) -> None:
        """Create dialog widgets."""
        main_frame = tk.Frame(
            self.dialog, bg=self.colors['bg_dark'], padx=30, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title = tk.Label(
            main_frame,
            text="Save Macro",
            font=('Segoe UI', 16, 'bold'),
            bg=self.colors['bg_dark'],
            fg=self.colors['accent']
        )
        title.pack(pady=(0, 20))

        # Name input
        name_label = tk.Label(
            main_frame,
            text="Macro Name:",
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['bg_dark'],
            fg=self.colors['fg_primary']
        )
        name_label.pack(anchor=tk.W, pady=(0, 5))

        self.name_entry = tk.Entry(
            main_frame,
            font=('Segoe UI', 11),
            bg=self.colors['bg_medium'],
            fg=self.colors['fg_primary'],
            insertbackground=self.colors['fg_primary'],
            relief='flat',
            borderwidth=2
        )
        self.name_entry.pack(fill=tk.X, pady=(0, 15))
        self.name_entry.focus()

        # Description input
        desc_label = tk.Label(
            main_frame,
            text="Description (optional):",
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['bg_dark'],
            fg=self.colors['fg_primary']
        )
        desc_label.pack(anchor=tk.W, pady=(0, 5))

        self.desc_text = tk.Text(
            main_frame,
            height=5,
            font=('Segoe UI', 10),
            bg=self.colors['bg_medium'],
            fg=self.colors['fg_primary'],
            insertbackground=self.colors['fg_primary'],
            relief='flat',
            borderwidth=2,
            wrap=tk.WORD
        )
        self.desc_text.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Loop checkbox
        self.loop_var = tk.BooleanVar(value=False)
        loop_check = tk.Checkbutton(
            main_frame,
            text="Loop this macro continuously",
            variable=self.loop_var,
            font=('Segoe UI', 10),
            bg=self.colors['bg_dark'],
            fg=self.colors['fg_primary'],
            selectcolor=self.colors['bg_medium'],
            activebackground=self.colors['bg_dark'],
            activeforeground=self.colors['fg_primary']
        )
        loop_check.pack(anchor=tk.W, pady=(0, 20))

        # Buttons
        button_frame = tk.Frame(main_frame, bg=self.colors['bg_dark'])
        button_frame.pack(fill=tk.X)

        save_button = tk.Button(
            button_frame,
            text="💾 Save",
            command=self._save,
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['success'],
            fg='#ffffff',
            activebackground='#3da88a',
            activeforeground='#ffffff',
            borderwidth=0,
            relief='flat',
            cursor='hand2',
            padx=20,
            pady=10
        )
        save_button.pack(side=tk.LEFT, padx=5)

        cancel_button = tk.Button(
            button_frame,
            text="✖ Cancel",
            command=self._cancel,
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['error'],
            fg='#ffffff',
            activebackground='#d66f5e',
            activeforeground='#ffffff',
            borderwidth=0,
            relief='flat',
            cursor='hand2',
            padx=20,
            pady=10
        )
        cancel_button.pack(side=tk.RIGHT, padx=5)

        # Bind Enter key to save
        self.dialog.bind('<Return>', lambda e: self._save())
        self.dialog.bind('<Escape>', lambda e: self._cancel())

    def _save(self) -> None:
        """Save and close the dialog."""
        name = self.name_entry.get().strip()

        if not name:
            messagebox.showwarning(
                "Missing Name",
                "Please enter a name for your macro.",
                parent=self.dialog
            )
            self.name_entry.focus()
            return

        # Check if macro name already exists
        existing_macros = get_all_macro_names()
        if name in existing_macros:
            messagebox.showerror(
                "Duplicate Name",
                f"A macro named '{name}' already exists.\nPlease choose a different name.",
                parent=self.dialog
            )
            self.name_entry.focus()
            self.name_entry.select_range(0, tk.END)
            return

        description = self.desc_text.get("1.0", tk.END).strip()
        if not description:
            description = "Custom recorded macro"

        loop = self.loop_var.get()

        self.result = (name, description, loop)
        self.dialog.destroy()

    def _cancel(self) -> None:
        """Cancel and close the dialog."""
        self.result = None
        self.dialog.destroy()

    def show(self):
        """Show the dialog and return the result.

        Returns:
            Tuple of (name, description, loop) or None if cancelled.
        """
        self.dialog.wait_window()
        return self.result
