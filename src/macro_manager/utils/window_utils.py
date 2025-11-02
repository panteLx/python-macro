"""Utility functions for window management."""

import logging
import time
from typing import Optional, List

import win32gui

from macro_manager.core.exceptions import WindowNotFoundError

logger = logging.getLogger(__name__)


def find_game_window(window_titles: Optional[List[str]] = None) -> Optional[int]:
    """Find a game window by title.

    Args:
        window_titles: List of possible window title substrings to search for.
                      Defaults to ["battlefield", "bf2042"].

    Returns:
        Window handle (hwnd) if found, None otherwise.

    Raises:
        WindowNotFoundError: If the window cannot be found.
    """
    if window_titles is None:
        window_titles = ["battlefield", "bf2042"]

    def callback(hwnd: int, windows: List[int]) -> bool:
        """Callback function for window enumeration."""
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd).lower()
            if any(game_title.lower() in title for game_title in window_titles):
                windows.append(hwnd)
        return True

    windows: List[int] = []
    win32gui.EnumWindows(callback, windows)

    if windows:
        hwnd = windows[0]
        title = win32gui.GetWindowText(hwnd)
        logger.info(f"Found game window: {title} (hwnd: {hwnd})")
        return hwnd

    logger.warning(f"Game window not found. Searched for: {window_titles}")
    return None


def focus_game_window(hwnd: int) -> Optional[int]:
    """Focus the game window.

    Args:
        hwnd: Window handle to focus.

    Returns:
        Previously focused window handle, or None if focus failed.

    Raises:
        WindowNotFoundError: If the window is invalid.
    """
    if not hwnd or not win32gui.IsWindow(hwnd):
        raise WindowNotFoundError(f"Invalid window handle: {hwnd}")

    previous_window = win32gui.GetForegroundWindow()

    if previous_window != hwnd:
        try:
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.1)
            logger.debug(f"Focused window: {hwnd}")
        except Exception as e:
            logger.error(f"Failed to focus window: {e}")
            return None

    return previous_window


def restore_window_focus(hwnd: int) -> None:
    """Restore focus to a specific window.

    Args:
        hwnd: Window handle to restore focus to.
    """
    if hwnd and win32gui.IsWindow(hwnd):
        try:
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.1)
            logger.debug(f"Restored focus to window: {hwnd}")
        except Exception as e:
            logger.error(f"Failed to restore window focus: {e}")


def send_key_to_window(
    hwnd: int,
    key: str,
    duration: Optional[float] = None,
    running: Optional[object] = None,
) -> None:
    """Send a key press to a specific window.

    Args:
        hwnd: Window handle to send the key to.
        key: Key to press ('w', 's', 'space').
        duration: How long to hold the key (None for tap).
        running: Optional threading.Event to check if macro should continue.

    Raises:
        WindowNotFoundError: If the window is invalid.
        ValueError: If the key is not supported.
    """
    from macro_manager.utils.direct_keys import DIK_W, DIK_S, DIK_SPACE
    from macro_manager.utils.direct_keys import press_key, release_key

    if not hwnd or not win32gui.IsWindow(hwnd):
        raise WindowNotFoundError(f"Invalid window handle: {hwnd}")

    # Map keys to DirectInput scan codes
    key_map = {"w": DIK_W, "s": DIK_S, "space": DIK_SPACE}

    scan_code = key_map.get(key.lower())
    if not scan_code:
        raise ValueError(
            f"Unsupported key: {key}. Supported keys: {list(key_map.keys())}")

    # Ensure game window is focused
    if win32gui.GetForegroundWindow() != hwnd:
        focus_game_window(hwnd)

    # Send input
    if duration:
        press_key(scan_code)
        start_time = time.time()
        while time.time() - start_time < duration:
            if running and not running.is_set():
                release_key(scan_code)
                return
            time.sleep(0.1)
        release_key(scan_code)
    else:
        press_key(scan_code)
        time.sleep(0.1)
        release_key(scan_code)

    if running and not running.is_set():
        return

    time.sleep(0.1)
