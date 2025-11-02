import time
import win32gui
from direct_keys import DIK_W, DIK_S, DIK_SPACE, hold_key, press_key, release_key


def find_game_window():
    def callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd).lower()
            # Add more possible window titles if needed
            if any(x in title for x in ["battlefield", "bf2042"]):
                windows.append(hwnd)
        return True

    windows = []
    win32gui.EnumWindows(callback, windows)
    return windows[0] if windows else None


def focus_game_window(hwnd):
    """Focus the game window and return the previously focused window"""
    if not hwnd or not win32gui.IsWindow(hwnd):
        return None

    # Store the current focused window
    previous_window = win32gui.GetForegroundWindow()

    # Only focus if we're not already focused
    if previous_window != hwnd:
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.1)  # Small delay to ensure focus is set

    return previous_window


def restore_window_focus(hwnd):
    """Restore focus to a specific window"""
    if hwnd and win32gui.IsWindow(hwnd):
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.1)  # Small delay to ensure focus is restored


def send_key_to_window(hwnd, key, duration=None, running=None):
    if not hwnd or not win32gui.IsWindow(hwnd):
        return

    # Map keys to DirectInput scan codes
    key_map = {
        'w': DIK_W,
        's': DIK_S,
        'space': DIK_SPACE
    }

    scan_code = key_map.get(key.lower())
    if not scan_code:
        return

    # Make sure game window is focused
    if win32gui.GetForegroundWindow() != hwnd:
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.1)  # Small delay to ensure focus is set

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
    time.sleep(0.1)  # Small delay between key presses
