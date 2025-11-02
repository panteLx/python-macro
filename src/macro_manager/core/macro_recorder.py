"""Macro recorder for capturing user keyboard actions."""

import logging
import time
from typing import List, Dict, Any, Optional
from pynput import keyboard
import threading

logger = logging.getLogger(__name__)


class MacroRecorder:
    """Records keyboard actions for creating custom macros."""

    def __init__(self):
        """Initialize the macro recorder."""
        self.actions: List[Dict[str, Any]] = []
        self.recording = False
        self.listener: Optional[keyboard.Listener] = None
        self.start_time: float = 0
        self.last_action_time: float = 0
        # Track when keys were pressed
        self.pressed_keys: Dict[str, float] = {}
        self.stop_key = "esc"  # Key to stop recording
        self.start_key = "f9"  # Key to start recording (when waiting)
        # Key to ignore on next release
        self.ignore_next_release: Optional[str] = None

    def start_recording(self) -> None:
        """Start recording keyboard actions."""
        if self.recording:
            logger.warning("Already recording")
            return

        self.actions = []
        self.recording = True
        self.start_time = time.time()
        self.last_action_time = self.start_time
        self.pressed_keys = {}

        logger.info("Started recording macro")
        print(
            f"Recording started! Press {self.stop_key.upper()} to stop recording.")

        # Start keyboard listener
        self.listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.listener.start()

    def stop_recording(self) -> List[Dict[str, Any]]:
        """Stop recording and return the recorded actions.

        Returns:
            List of recorded actions.
        """
        if not self.recording:
            logger.warning("Not currently recording")
            return []

        self.recording = False

        # Add final delay if there were any actions recorded
        if len(self.actions) > 0:
            current_time = time.time()
            final_delay = current_time - self.last_action_time

            # Add delay if significant (more than 0.1 seconds)
            if final_delay > 0.1:
                self.actions.append({
                    "type": "sleep",
                    "delay": round(final_delay, 2)
                })
                logger.debug(f"Added final delay: {final_delay:.2f}s")

        if self.listener:
            self.listener.stop()
            self.listener = None

        logger.info(f"Stopped recording. Captured {len(self.actions)} actions")
        print(f"Recording stopped! Captured {len(self.actions)} actions.")

        return self.actions

    def _on_key_press(self, key) -> None:
        """Handle key press event.

        Args:
            key: The key that was pressed.
        """
        if not self.recording:
            return

        try:
            # Get key name
            if hasattr(key, 'char') and key.char:
                key_name = key.char.lower()
            elif hasattr(key, 'name'):
                key_name = key.name.lower()
            else:
                key_name = str(key).replace("Key.", "").lower()

            # Ignore all function keys (F1-F12)
            if key_name.startswith('f') and len(key_name) <= 3:
                # Check if it's a function key (f1, f2, ..., f12)
                try:
                    f_num = int(key_name[1:])
                    if 1 <= f_num <= 12:
                        logger.debug(f"Ignoring function key: {key_name}")
                        return
                except ValueError:
                    pass  # Not a function key

            # Check if this is the stop key
            if key_name == self.stop_key:
                # Don't record the stop key, just stop recording
                threading.Thread(target=self.stop_recording,
                                 daemon=True).start()
                return

            # Track when this key was pressed (only if not already pressed to avoid key repeat issues)
            if key_name not in self.pressed_keys:
                self.pressed_keys[key_name] = time.time()
                logger.debug(f"Key pressed: {key_name}")
            else:
                logger.debug(f"Key repeat ignored: {key_name}")

        except Exception as e:
            logger.error(f"Error in key press handler: {e}")

    def _on_key_release(self, key) -> None:
        """Handle key release event.

        Args:
            key: The key that was released.
        """
        if not self.recording:
            return

        try:
            # Get key name
            if hasattr(key, 'char') and key.char:
                key_name = key.char.lower()
            elif hasattr(key, 'name'):
                key_name = key.name.lower()
            else:
                key_name = str(key).replace("Key.", "").lower()

            # Ignore all function keys (F1-F12)
            if key_name.startswith('f') and len(key_name) <= 3:
                # Check if it's a function key (f1, f2, ..., f12)
                try:
                    f_num = int(key_name[1:])
                    if 1 <= f_num <= 12:
                        logger.debug(
                            f"Ignoring function key release: {key_name}")
                        # Remove from pressed_keys if present
                        if key_name in self.pressed_keys:
                            del self.pressed_keys[key_name]
                        return
                except ValueError:
                    pass  # Not a function key

            # Ignore the stop key
            if key_name == self.stop_key:
                return

            current_time = time.time()

            # Calculate delay since last action
            delay_since_last = current_time - self.last_action_time

            # Add delay if significant (more than 0.1 seconds)
            if delay_since_last > 0.1 and len(self.actions) > 0:
                self.actions.append({
                    "type": "sleep",
                    "delay": round(delay_since_last, 2)
                })
                logger.debug(f"Added delay: {delay_since_last:.2f}s")

            # Check if we tracked when this key was pressed
            if key_name in self.pressed_keys:
                press_time = self.pressed_keys[key_name]
                hold_duration = current_time - press_time

                # If held for a significant time, record as keyhold, otherwise keypress
                if hold_duration > 0.2:
                    self.actions.append({
                        "type": "keyhold",
                        "key": key_name,
                        "duration": round(hold_duration, 2)
                    })
                    logger.debug(
                        f"Key held: {key_name} for {hold_duration:.2f}s")
                else:
                    self.actions.append({
                        "type": "keypress",
                        "key": key_name
                    })
                    logger.debug(f"Key tapped: {key_name}")

                # Remove from tracking
                del self.pressed_keys[key_name]
            else:
                # Fallback: just record as keypress
                self.actions.append({
                    "type": "keypress",
                    "key": key_name
                })
                logger.debug(f"Key tapped (fallback): {key_name}")

            # Update last action time
            self.last_action_time = current_time

        except Exception as e:
            logger.error(f"Error in key release handler: {e}")

    def is_recording(self) -> bool:
        """Check if currently recording.

        Returns:
            True if recording, False otherwise.
        """
        return self.recording

    def get_actions(self) -> List[Dict[str, Any]]:
        """Get the current list of recorded actions.

        Returns:
            List of recorded actions.
        """
        return self.actions.copy()

    def clear_actions(self) -> None:
        """Clear all recorded actions."""
        self.actions = []
        logger.info("Cleared recorded actions")

    def wait_for_start_key(self, on_start_callback) -> None:
        """Wait for the start key to be pressed, then begin recording.

        Args:
            on_start_callback: Function to call when recording starts.
        """
        def on_press(key):
            try:
                # Get key name
                if hasattr(key, 'char') and key.char:
                    key_name = key.char.lower()
                elif hasattr(key, 'name'):
                    key_name = key.name.lower()
                else:
                    key_name = str(key).replace("Key.", "").lower()

                # Check if this is the start key
                if key_name == self.start_key:
                    # Stop the waiting listener
                    if self.listener:
                        self.listener.stop()
                        self.listener = None

                    # Mark this key to be ignored on release
                    self.ignore_next_release = self.start_key

                    # Start recording
                    self.start_recording()

                    # Call the callback
                    if on_start_callback:
                        on_start_callback()

                    return False  # Stop listener
            except Exception as e:
                logger.error(f"Error in start key handler: {e}")

        # Start a listener just for the start key
        self.listener = keyboard.Listener(on_press=on_press)
        self.listener.start()
        logger.info(
            f"Waiting for {self.start_key.upper()} to start recording...")
        print(f"Press {self.start_key.upper()} to start recording...")
