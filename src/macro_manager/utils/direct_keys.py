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

# Alphabet keys
DIK_A = 0x1E
DIK_B = 0x30
DIK_C = 0x2E
DIK_D = 0x20
DIK_E = 0x12
DIK_F = 0x21
DIK_G = 0x22
DIK_H = 0x23
DIK_I = 0x17
DIK_J = 0x24
DIK_K = 0x25
DIK_L = 0x26
DIK_M = 0x32
DIK_N = 0x31
DIK_O = 0x18
DIK_P = 0x19
DIK_Q = 0x10
DIK_R = 0x13
DIK_S = 0x1F
DIK_T = 0x14
DIK_U = 0x16
DIK_V = 0x2F
DIK_W = 0x11
DIK_X = 0x2D
DIK_Y = 0x15
DIK_Z = 0x2C

# Number keys
DIK_0 = 0x0B
DIK_1 = 0x02
DIK_2 = 0x03
DIK_3 = 0x04
DIK_4 = 0x05
DIK_5 = 0x06
DIK_6 = 0x07
DIK_7 = 0x08
DIK_8 = 0x09
DIK_9 = 0x0A

# Function keys
DIK_F1 = 0x3B
DIK_F2 = 0x3C
DIK_F3 = 0x3D
DIK_F4 = 0x3E
DIK_F5 = 0x3F
DIK_F6 = 0x40
DIK_F7 = 0x41
DIK_F8 = 0x42
DIK_F9 = 0x43
DIK_F10 = 0x44
DIK_F11 = 0x57
DIK_F12 = 0x58

# Special keys
DIK_SPACE = 0x39
DIK_ESCAPE = 0x01
DIK_RETURN = 0x1C
DIK_ENTER = 0x1C
DIK_TAB = 0x0F
DIK_BACKSPACE = 0x0E
DIK_LSHIFT = 0x2A
DIK_RSHIFT = 0x36
DIK_LCONTROL = 0x1D
DIK_RCONTROL = 0x9D
DIK_LALT = 0x38
DIK_RALT = 0xB8
DIK_CAPSLOCK = 0x3A

# Arrow keys
DIK_UP = 0xC8
DIK_DOWN = 0xD0
DIK_LEFT = 0xCB
DIK_RIGHT = 0xCD

# Numpad keys
DIK_NUMPAD0 = 0x52
DIK_NUMPAD1 = 0x4F
DIK_NUMPAD2 = 0x50
DIK_NUMPAD3 = 0x51
DIK_NUMPAD4 = 0x4B
DIK_NUMPAD5 = 0x4C
DIK_NUMPAD6 = 0x4D
DIK_NUMPAD7 = 0x47
DIK_NUMPAD8 = 0x48
DIK_NUMPAD9 = 0x49
DIK_NUMPADENTER = 0x9C
DIK_ADD = 0x4E
DIK_SUBTRACT = 0x4A
DIK_MULTIPLY = 0x37
DIK_DIVIDE = 0xB5
DIK_DECIMAL = 0x53

# Other common keys
DIK_INSERT = 0xD2
DIK_DELETE = 0xD3
DIK_HOME = 0xC7
DIK_END = 0xCF
DIK_PAGEUP = 0xC9
DIK_PAGEDOWN = 0xD1

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
    ii_.ki = KeyBdInput(0, scan_code, KEYEVENTF_SCANCODE,
                        0, ctypes.pointer(extra))
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
