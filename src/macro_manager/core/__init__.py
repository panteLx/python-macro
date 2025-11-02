"""Core functionality for MacroManager."""

from macro_manager.core.macro import Macro
from macro_manager.core.macro_controller import MacroController
from macro_manager.core.exceptions import (
    MacroError,
    WindowNotFoundError,
    KeyBindingError,
    MacroExecutionError,
)

__all__ = [
    "Macro",
    "MacroController",
    "MacroError",
    "WindowNotFoundError",
    "KeyBindingError",
    "MacroExecutionError",
]
