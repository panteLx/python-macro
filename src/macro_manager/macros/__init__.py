"""Available macro definitions."""

import logging
from pathlib import Path
from typing import Dict, List, Optional
from macro_manager.core.macro import Macro
from macro_manager.macros.recorded_macro import RecordedMacro
from macro_manager.utils.macro_storage import MacroStorage

logger = logging.getLogger(__name__)

# Registry for all macros (loaded dynamically from JSON files)
_all_macros: Dict[str, RecordedMacro] = {}

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
    """Reload all macros from storage (includes both prebuilt and user-recorded)."""
    global _all_macros

    if _storage is None:
        logger.warning("Macro storage not initialized")
        return

    _all_macros.clear()
    all_loaded = _storage.load_all_macros()

    for macro in all_loaded:
        _all_macros[macro.name] = macro

    logger.info(f"Loaded {len(_all_macros)} macros")


def get_macro_by_name(name: str) -> Optional[Macro]:
    """Get a macro instance by its display name.

    Args:
        name: Display name of the macro.

    Returns:
        Macro instance if found, None otherwise.
    """
    return _all_macros.get(name)


def get_all_macro_names() -> List[str]:
    """Get list of all macro display names.

    Returns:
        List of macro display names.
    """
    return list(_all_macros.keys())


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
        _all_macros[macro.name] = macro
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
    if success and name in _all_macros:
        del _all_macros[name]
    return success


def is_recorded_macro(name: str) -> bool:
    """Check if a macro is a user-recorded macro (all macros are now JSON-based).

    Args:
        name: Display name of the macro.

    Returns:
        True if it's a macro that can be deleted, False otherwise.
    """
    # All macros are now stored as JSON, so check if it exists
    return name in _all_macros
