"""MacroManager - A professional macro automation tool for games.

This package provides a framework for creating and running game macros
with a user-friendly GUI interface.
"""

__version__ = "2.0.0"
__author__ = "panteLx"
__license__ = "MIT"

from macro_manager.core.macro import Macro
from macro_manager.core.macro_controller import MacroController

__all__ = ["Macro", "MacroController", "__version__"]
