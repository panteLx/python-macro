"""Direct Input key handling using Windows API."""

import ctypes
import time
from typing import Optional

# Windows API function
SendInput = ctypes.windll.user32.SendInput

# C struct type definitions
PUL = ctypes.POINTER(ctypes.c_ulong)


class KeyBdInput(ctypes.Structure):
    """Keyboard input structure for SendInput."""

    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", PUL),
    ]


class HardwareInput(ctypes.Structure):
    """Hardware input structure for SendInput."""

    _fields_ = [
        ("uMsg", ctypes.c_ulong),
        ("wParamL", ctypes.c_short),
        ("wParamH", ctypes.c_ushort),
    ]


class MouseInput(ctypes.Structure):
    """Mouse input structure for SendInput."""

    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", PUL),
    ]


class Input_I(ctypes.Union):
    """Union of input types for SendInput."""

    _fields_ = [("ki", KeyBdInput), ("mi", MouseInput), ("hi", HardwareInput)]


class Input(ctypes.Structure):
    """Input structure for SendInput."""

    _fields_ = [("type", ctypes.c_ulong), ("ii", Input_I)]


# DirectInput Scan Codes
# Reference: http://www.gamespp.com/directx/directInputKeyboardScanCodes.html
DIK_W = 0x11
DIK_S = 0x1F
DIK_SPACE = 0x39

# Input flags
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_KEYUP = 0x0002


def press_key(scan_code: int) -> None:
    """Press a key using DirectInput scan code.

    Args:
        scan_code: DirectInput scan code of the key to press.
    """
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(0, scan_code, KEYEVENTF_SCANCODE, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(1), ii_)
    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))


def release_key(scan_code: int) -> None:
    """Release a key using DirectInput scan code.

    Args:
        scan_code: DirectInput scan code of the key to release.
    """
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(
        0,
        scan_code,
        KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP,
        0,
        ctypes.pointer(extra),
    )
    x = Input(ctypes.c_ulong(1), ii_)
    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))


def hold_key(scan_code: int, duration: float) -> None:
    """Hold a key for a specified duration.

    Args:
        scan_code: DirectInput scan code of the key to hold.
        duration: Time to hold the key in seconds.
    """
    press_key(scan_code)
    time.sleep(duration)
    release_key(scan_code)
