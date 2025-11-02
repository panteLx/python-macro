"""Available macro definitions."""

import logging
from pathlib import Path
from typing import Dict, List, Optional
from macro_manager.core.macro import Macro
from macro_manager.macros.battlefield6 import (
    BF6SiegeCairoMacro,
    BF6LibPeakMacro,
    BF6SpaceBarMacro,
)
from macro_manager.macros.recorded_macro import RecordedMacro
from macro_manager.utils.macro_storage import MacroStorage

logger = logging.getLogger(__name__)

# Registry of prebuilt macros
PREBUILT_MACROS: Dict[str, Macro] = {
    "bf6_lib_peak": BF6LibPeakMacro(),
    "bf6_siege_cairo": BF6SiegeCairoMacro(),
    "bf6_space_bar": BF6SpaceBarMacro(),
}

# Registry for recorded macros (loaded dynamically)
_recorded_macros: Dict[str, RecordedMacro] = {}

# Storage manager
_storage: Optional[MacroStorage] = None


def initialize_macro_storage(config_dir: Path) -> None:
    """Initialize the macro storage system.

    Args:
        config_dir: Path to the config directory.
    """
    global _storage
    storage_dir = config_dir / "recorded_macros"
    _storage = MacroStorage(storage_dir)
    reload_recorded_macros()
    logger.info("Macro storage initialized")


def reload_recorded_macros() -> None:
    """Reload all recorded macros from storage."""
    global _recorded_macros

    if _storage is None:
        logger.warning("Macro storage not initialized")
        return

    _recorded_macros.clear()
    recorded = _storage.load_all_macros()

    for macro in recorded:
        _recorded_macros[macro.name] = macro

    logger.info(f"Loaded {len(_recorded_macros)} recorded macros")


def get_macro_by_name(name: str) -> Optional[Macro]:
    """Get a macro instance by its display name.

    Args:
        name: Display name of the macro.

    Returns:
        Macro instance if found, None otherwise.
    """
    # Check prebuilt macros first
    for macro in PREBUILT_MACROS.values():
        if macro.name == name:
            return macro

    # Check recorded macros
    return _recorded_macros.get(name)


def get_all_macro_names() -> List[str]:
    """Get list of all macro display names.

    Returns:
        List of macro display names (prebuilt first, then recorded).
    """
    prebuilt_names = [macro.name for macro in PREBUILT_MACROS.values()]
    recorded_names = list(_recorded_macros.keys())
    return prebuilt_names + recorded_names


def get_prebuilt_macro_names() -> List[str]:
    """Get list of prebuilt macro names only.

    Returns:
        List of prebuilt macro display names.
    """
    return [macro.name for macro in PREBUILT_MACROS.values()]


def get_recorded_macro_names() -> List[str]:
    """Get list of recorded macro names only.

    Returns:
        List of recorded macro display names.
    """
    return list(_recorded_macros.keys())


def save_recorded_macro(macro: RecordedMacro) -> bool:
    """Save a recorded macro to storage.

    Args:
        macro: The macro to save.

    Returns:
        True if saved successfully, False otherwise.
    """
    if _storage is None:
        logger.error("Macro storage not initialized")
        return False

    success = _storage.save_macro(macro)
    if success:
        _recorded_macros[macro.name] = macro
    return success


def delete_recorded_macro(name: str) -> bool:
    """Delete a recorded macro from storage.

    Args:
        name: Name of the macro to delete.

    Returns:
        True if deleted successfully, False otherwise.
    """
    if _storage is None:
        logger.error("Macro storage not initialized")
        return False

    success = _storage.delete_macro(name)
    if success and name in _recorded_macros:
        del _recorded_macros[name]
    return success


def is_recorded_macro(name: str) -> bool:
    """Check if a macro is a recorded (not prebuilt) macro.

    Args:
        name: Display name of the macro.

    Returns:
        True if it's a recorded macro, False otherwise.
    """
    return name in _recorded_macros
