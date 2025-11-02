"""Available macro definitions."""

from typing import Dict
from macro_manager.core.macro import Macro
from macro_manager.macros.battlefield6 import (
    BF6SiegeCairoMacro,
    BF6LibPeakMacro,
    BF6SpaceBarMacro,
)

# Registry of all available macros
AVAILABLE_MACROS: Dict[str, Macro] = {
    "bf6_lib_peak": BF6LibPeakMacro(),
    "bf6_siege_cairo": BF6SiegeCairoMacro(),
    "bf6_space_bar": BF6SpaceBarMacro(),
}


def get_macro_by_name(name: str) -> Macro:
    """Get a macro instance by its display name.

    Args:
        name: Display name of the macro.

    Returns:
        Macro instance if found, None otherwise.
    """
    for macro in AVAILABLE_MACROS.values():
        if macro.name == name:
            return macro
    return None


def get_all_macro_names() -> list:
    """Get list of all macro display names.

    Returns:
        List of macro display names.
    """
    return [macro.name for macro in AVAILABLE_MACROS.values()]
