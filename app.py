import time
import sys
import io
from threading import Thread, Event
import keyboard
import win32gui
from os import system
import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
from window_utils import find_game_window
from macros import AVAILABLE_MACROS


class StdoutRedirector(io.StringIO):
    def __init__(self, text_widget, status_callback):
        super().__init__()
        self.text_widget = text_widget
        self.status_callback = status_callback

    def write(self, string):
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)
        self.text_widget.update_idletasks()  # Force update of the text widget

        # Parse the output for status updates
        if "[Step" in string:
            try:
                # Extract step info and message
                step_info = string.split("]")[0].replace("[", "").strip()
                message = string.split("]")[1].strip()
                current_step, total_steps = step_info.replace(
                    "Step ", "").split("/")
                self.status_callback(current_step, total_steps, message)
            except:
                pass  # If parsing fails, just ignore
        elif "Starting" in string or "Error" in string:
            self.status_callback("--", "--", string.strip())

    def flush(self):
        pass  # Required for stdout redirection


class KeyBindingDialog:
    """Dialog for changing key bindings with a GUI wizard"""

    def __init__(self, parent, current_bindings):
        self.result = None
        self.current_key = None
        self.capturing = False

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Change Key Bindings")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Create main frame with padding
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title
        title_label = ttk.Label(main_frame, text="Configure Key Bindings",
                                font=('Helvetica', 14, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 15))

        # Instructions
        instructions = ttk.Label(main_frame,
                                 text="Click the button and press the key you want to assign.\nAvoid using ESC or system keys.",
                                 font=('Helvetica', 10),
                                 justify=tk.CENTER)
        instructions.grid(row=1, column=0, columnspan=2, pady=(0, 20))

        # Start key section
        start_frame = ttk.LabelFrame(
            main_frame, text="Start Macro Key", padding="15")
        start_frame.grid(row=2, column=0, columnspan=2,
                         sticky=(tk.W, tk.E), pady=8)

        ttk.Label(start_frame, text="Current:", font=('Helvetica', 10)).grid(
            row=0, column=0, sticky=tk.W, padx=5)
        self.start_current_label = ttk.Label(start_frame, text=current_bindings['start_key'].upper(),
                                             font=('Helvetica', 10, 'bold'))
        self.start_current_label.grid(row=0, column=1, sticky=tk.W, padx=5)

        self.start_button = ttk.Button(start_frame, text="Set New Key",
                                       command=lambda: self.capture_key('start'))
        self.start_button.grid(row=0, column=2, padx=10)

        self.start_new_label = ttk.Label(start_frame, text="",
                                         font=('Helvetica', 10, 'bold'),
                                         foreground='green')
        self.start_new_label.grid(row=0, column=3, sticky=tk.W, padx=5)

        # Stop key section
        stop_frame = ttk.LabelFrame(
            main_frame, text="Stop Macro Key", padding="15")
        stop_frame.grid(row=3, column=0, columnspan=2,
                        sticky=(tk.W, tk.E), pady=8)

        ttk.Label(stop_frame, text="Current:", font=('Helvetica', 10)
                  ).grid(row=0, column=0, sticky=tk.W, padx=5)
        self.stop_current_label = ttk.Label(stop_frame, text=current_bindings['stop_key'].upper(),
                                            font=('Helvetica', 10, 'bold'))
        self.stop_current_label.grid(row=0, column=1, sticky=tk.W, padx=5)

        self.stop_button = ttk.Button(stop_frame, text="Set New Key",
                                      command=lambda: self.capture_key('stop'))
        self.stop_button.grid(row=0, column=2, padx=10)

        self.stop_new_label = ttk.Label(stop_frame, text="",
                                        font=('Helvetica', 10, 'bold'),
                                        foreground='green')
        self.stop_new_label.grid(row=0, column=3, sticky=tk.W, padx=5)

        # Status label
        self.status_label = ttk.Label(main_frame, text="",
                                      font=('Helvetica', 10, 'italic'),
                                      foreground='blue')
        self.status_label.grid(row=4, column=0, columnspan=2, pady=15)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=(15, 0))

        self.save_button = ttk.Button(button_frame, text="Save Changes",
                                      command=self.save_changes, state='disabled')
        self.save_button.grid(row=0, column=0, padx=10)

        ttk.Button(button_frame, text="Cancel",
                   command=self.cancel).grid(row=0, column=1, padx=10)

        # Store new bindings
        self.new_bindings = current_bindings.copy()

        # Update geometry after all widgets are created and center the dialog
        self.dialog.update_idletasks()
        width = self.dialog.winfo_reqwidth()
        height = self.dialog.winfo_reqheight()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")

    def capture_key(self, key_type):
        """Start capturing a key press"""
        if self.capturing:
            return

        self.capturing = True
        self.current_key = key_type

        if key_type == 'start':
            self.start_button.config(state='disabled')
            self.status_label.config(
                text="Press a key for START macro...", foreground='blue')
        else:
            self.stop_button.config(state='disabled')
            self.status_label.config(
                text="Press a key for STOP macro...", foreground='blue')

        # Start listening for key press
        keyboard.on_press(self.on_key_press, suppress=True)

    def on_key_press(self, event):
        """Handle key press event"""
        if not self.capturing:
            return

        key_name = event.name

        # Ignore certain keys
        if key_name in ['esc', 'escape']:
            self.status_label.config(text="ESC is not allowed. Please choose another key.",
                                     foreground='red')
            self.capturing = False
            keyboard.unhook_all()
            self.start_button.config(state='normal')
            self.stop_button.config(state='normal')
            return

        # Update the binding
        self.new_bindings[f'{self.current_key}_key'] = key_name

        # Update the label
        if self.current_key == 'start':
            self.start_new_label.config(text=f"→ {key_name.upper()}")
            self.start_button.config(state='normal')
        else:
            self.stop_new_label.config(text=f"→ {key_name.upper()}")
            self.stop_button.config(state='normal')

        self.status_label.config(text=f"Key '{key_name.upper()}' assigned successfully!",
                                 foreground='green')

        # Enable save button
        self.save_button.config(state='normal')

        # Stop capturing
        self.capturing = False
        keyboard.unhook_all()

    def save_changes(self):
        """Save the new key bindings"""
        keyboard.unhook_all()  # Clean up any active hooks
        self.result = self.new_bindings
        self.dialog.destroy()

    def cancel(self):
        """Cancel without saving"""
        keyboard.unhook_all()  # Clean up any active hooks
        self.result = None
        self.dialog.destroy()

    def show(self):
        """Show the dialog and return the result"""
        self.dialog.wait_window()
        return self.result


class MacroUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MacroManager")
        self.root.geometry("700x900")  # Larger window to show log properly

        # Configure root window to be resizable
        self.root.resizable(True, True)
        self.root.minsize(500, 600)

        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Initialize variables
        self.macro_thread = None
        self.running = Event()
        self.game_window = None
        self.current_macro = None

        # Load key bindings
        self.load_key_bindings()

        # Create UI elements
        self.create_widgets()

        # Set key bindings
        self.set_key_bindings()

        # Set up cleanup on window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_key_bindings(self):
        config_file = 'macro_config.json'
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                self.key_bindings = json.load(f)
        else:
            # First-time setup with default bindings
            self.key_bindings = {'start_key': 'f1', 'stop_key': 'f2'}
            with open(config_file, 'w') as f:
                json.dump(self.key_bindings, f)
            # Will prompt user to configure after UI is created
            self.root.after(500, self.first_time_setup)

    def first_time_setup(self):
        """Show welcome message and key binding wizard on first run"""
        result = messagebox.askyesno(
            "Welcome to MacroManager!",
            "This is your first time running MacroManager.\n\n"
            "Default key bindings:\n"
            "• Start Macro: F1\n"
            "• Stop Macro: F2\n\n"
            "Would you like to configure custom key bindings now?\n"
            "(You can change them later using the 'Change Keys' button)"
        )

        if result:
            self.change_keys()

    def create_widgets(self):
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure main frame grid
        main_frame.grid_columnconfigure(0, weight=1)

        # Create title
        title_label = ttk.Label(
            main_frame, text="MacroManager", font=('Helvetica', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Macro selection
        ttk.Label(main_frame, text="Select Macro:", font=(
            'Helvetica', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.macro_combo = ttk.Combobox(
            main_frame, width=50, font=('Helvetica', 10))
        self.macro_combo['values'] = [
            macro.name for macro in AVAILABLE_MACROS.values()]
        self.macro_combo.grid(row=2, column=0, columnspan=2,
                              sticky=(tk.W, tk.E), pady=5, padx=5)
        if self.macro_combo['values']:
            self.macro_combo.current(0)

        # Description
        ttk.Label(main_frame, text="Description:", font=(
            'Helvetica', 10, 'bold')).grid(row=3, column=0, sticky=tk.W, pady=5)
        self.description_text = tk.Text(
            main_frame, height=6, wrap=tk.WORD, font=('Helvetica', 10))
        self.description_text.grid(
            row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=5)
        self.description_text.config(state=tk.DISABLED)

        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.grid(row=5, column=0, columnspan=2,
                          sticky=(tk.W, tk.E), pady=10, padx=5)
        status_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(status_frame, text="Current State:", font=(
            'Helvetica', 10)).grid(row=0, column=0, sticky=tk.W, padx=5)
        self.status_label = ttk.Label(
            status_frame, text="Idle", font=('Helvetica', 10, 'bold'))
        self.status_label.grid(row=0, column=1, sticky=tk.W, padx=5)

        ttk.Label(status_frame, text="Game Window:", font=(
            'Helvetica', 10)).grid(row=1, column=0, sticky=tk.W, padx=5)
        self.window_label = ttk.Label(
            status_frame, text="Not detected", font=('Helvetica', 10))
        self.window_label.grid(row=1, column=1, sticky=tk.W, padx=5)

        ttk.Label(status_frame, text="Current Step:", font=(
            'Helvetica', 10)).grid(row=2, column=0, sticky=tk.W, padx=5)
        self.step_label = ttk.Label(
            status_frame, text="--", font=('Helvetica', 10))
        self.step_label.grid(row=2, column=1, sticky=tk.W, padx=5)

        ttk.Label(status_frame, text="Action:", font=('Helvetica', 10)).grid(
            row=3, column=0, sticky=tk.W, padx=5)
        self.action_label = ttk.Label(
            status_frame, text="--", font=('Helvetica', 10))
        self.action_label.grid(row=3, column=1, sticky=tk.W, padx=5)

        # Key bindings
        keys_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        keys_frame.grid(row=6, column=0, columnspan=2,
                        sticky=(tk.W, tk.E), pady=10, padx=5)
        keys_frame.grid_columnconfigure(0, weight=1)

        # Add key binding labels with proper padding
        key_style = {'font': ('Helvetica', 10)}
        ttk.Label(keys_frame, text=f"Start Macro: {self.key_bindings['start_key']}", **key_style).grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(keys_frame, text=f"Stop Macro: {self.key_bindings['stop_key']}", **key_style).grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(keys_frame, text="Change Keys: f12", **
                  key_style).grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=10)
        button_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Style the buttons
        button_style = {'width': 15}
        start_btn = ttk.Button(button_frame, text="Start",
                               command=self.start_macro, **button_style)
        stop_btn = ttk.Button(button_frame, text="Stop",
                              command=self.stop_macro, **button_style)
        change_btn = ttk.Button(
            button_frame, text="Change Keys", command=self.change_keys, **button_style)

        start_btn.grid(row=0, column=0, padx=10)
        stop_btn.grid(row=0, column=1, padx=10)
        change_btn.grid(row=0, column=2, padx=10)

        # Create a text widget for log output
        self.log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        self.log_frame.grid(row=8, column=0, columnspan=2,
                            sticky=(tk.W, tk.E), pady=10, padx=5)
        self.log_frame.grid_columnconfigure(0, weight=1)

        # Larger log area so it's visible by default
        self.log_text = tk.Text(self.log_frame, height=12,
                                wrap=tk.WORD, font=('Helvetica', 10))
        self.log_text.grid(row=0, column=0, sticky=(
            tk.W, tk.E, tk.N, tk.S), pady=5, padx=5)

        # Add scrollbar to log
        log_scrollbar = ttk.Scrollbar(
            self.log_frame, orient="vertical", command=self.log_text.yview)
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text.configure(yscrollcommand=log_scrollbar.set)

        # Make log frame expand with window
        self.log_frame.grid_rowconfigure(0, weight=1)

        # Style the buttons
        button_style = {'width': 15}
        start_btn = ttk.Button(button_frame, text="Start",
                               command=self.start_macro, **button_style)
        stop_btn = ttk.Button(button_frame, text="Stop",
                              command=self.stop_macro, **button_style)
        change_btn = ttk.Button(
            button_frame, text="Change Keys", command=self.change_keys, **button_style)

        # Add padding and layout
        start_btn.grid(row=0, column=0, padx=10)
        stop_btn.grid(row=0, column=1, padx=10)
        change_btn.grid(row=0, column=2, padx=10)

        # Add footer
        footer_frame = ttk.Frame(main_frame)
        footer_frame.grid(row=9, column=0, columnspan=2,
                          sticky=(tk.W, tk.E), pady=(10, 0))
        footer_frame.grid_columnconfigure(0, weight=1)

        # Developer credit
        dev_label = ttk.Label(
            footer_frame, text="Developed by panteLx", font=('Helvetica', 9))
        dev_label.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # Copyright notice
        copyright_label = ttk.Label(
            footer_frame, text="© 2025 MacroManager - MIT License", font=('Helvetica', 8))
        copyright_label.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(2, 0))

        # Configure text alignment to center for both labels
        dev_label.configure(anchor="center")
        copyright_label.configure(anchor="center")

        # Configure main frame to expand log area
        main_frame.grid_rowconfigure(8, weight=1)  # Make log expand vertically

        # Bind macro selection change
        self.macro_combo.bind('<<ComboboxSelected>>', self.update_description)
        self.update_description(None)

    def update_description(self, event):
        selected_name = self.macro_combo.get()
        selected_macro = next(
            (m for m in AVAILABLE_MACROS.values() if m.name == selected_name), None)

        self.description_text.config(state=tk.NORMAL)
        self.description_text.delete(1.0, tk.END)
        if selected_macro:
            self.description_text.insert(tk.END, selected_macro.description)
        self.description_text.config(state=tk.DISABLED)

    def set_key_bindings(self):
        # Clear all existing hooks first
        keyboard.unhook_all()

        # Set up new key bindings
        keyboard.on_press_key(
            self.key_bindings['start_key'], lambda _: self.start_macro())
        keyboard.on_press_key(
            self.key_bindings['stop_key'], lambda _: self.stop_macro())
        keyboard.on_press_key('f12', lambda _: self.change_keys())

    def update_status(self, current_step, total_steps, message):
        """Update the GUI status labels with macro progress"""
        self.root.after(0, lambda: self._update_gui_status(
            current_step, total_steps, message))

    def _update_gui_status(self, current_step, total_steps, message):
        """Update GUI elements (called from main thread)"""
        if current_step != "--":
            self.step_label.config(text=f"{current_step}/{total_steps}")
        self.action_label.config(text=message)

    def start_macro(self):
        if self.macro_thread and self.macro_thread.is_alive():
            return

        if not self.game_window:
            self.game_window = find_game_window()
            if not self.game_window:
                messagebox.showerror(
                    "Error", "Game window not found! Please make sure Battlefield is running.")
                self.window_label.config(text="Not detected")
                return
            else:
                window_title = win32gui.GetWindowText(self.game_window)
                self.window_label.config(text=window_title)

        selected_name = self.macro_combo.get()
        self.current_macro = next(
            (m for m in AVAILABLE_MACROS.values() if m.name == selected_name), None)

        if not self.current_macro:
            messagebox.showerror("Error", "Please select a macro first!")
            return

        # Clear the log
        self.log_text.delete(1.0, tk.END)

        # Set up stdout and stderr redirection so logs go only to the GUI
        stdout_redirector = StdoutRedirector(self.log_text, self.update_status)
        sys.stdout = stdout_redirector
        sys.stderr = stdout_redirector

        self.running.set()
        self.macro_thread = Thread(
            target=self.current_macro.run, args=(self.game_window, self.running))
        self.macro_thread.daemon = True
        self.macro_thread.start()
        self.status_label.config(text="Running")
        self.step_label.config(text="--")
        self.action_label.config(text="Starting...")

    def stop_macro(self):
        self.running.clear()
        self.status_label.config(text="Stopped")
        self.step_label.config(text="--")
        self.action_label.config(text="Stopped")
        if not self.game_window or not win32gui.IsWindow(self.game_window):
            self.game_window = None
            self.window_label.config(text="Not detected")
        # Don't restore stdout/stderr immediately - let the macro thread finish
        # Restoration will happen when starting a new macro or on app close

    def change_keys(self):
        if self.running.is_set():
            messagebox.showwarning(
                "Warning", "Please stop the macro before changing keys!")
            return

        # Show the key binding dialog
        dialog = KeyBindingDialog(self.root, self.key_bindings)
        new_bindings = dialog.show()

        # If user cancelled, do nothing
        if new_bindings is None:
            return

        # Remove old bindings
        keyboard.unhook_all()

        # Update bindings
        self.key_bindings = new_bindings
        with open('macro_config.json', 'w') as f:
            json.dump(self.key_bindings, f)

        # Set new bindings
        self.set_key_bindings()

        # Update UI to show new bindings
        self.create_widgets()

        # Show success message
        messagebox.showinfo("Success", "Key bindings updated successfully!")

    def on_closing(self):
        """Handle application closing - stop macro and restore stdout/stderr"""
        if self.running.is_set():
            self.stop_macro()
        # Restore stdout and stderr
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        self.root.destroy()


def main():
    root = tk.Tk()
    app = MacroUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
