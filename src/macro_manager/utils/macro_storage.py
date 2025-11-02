"""Storage utilities for saving and loading recorded macros."""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from macro_manager.macros.recorded_macro import RecordedMacro

logger = logging.getLogger(__name__)


class MacroStorage:
    """Handles saving and loading of recorded macros."""

    def __init__(self, storage_dir: Path):
        """Initialize macro storage.

        Args:
            storage_dir: Directory where macros will be stored.
        """
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Macro storage initialized at: {self.storage_dir}")

    def save_macro(self, macro: RecordedMacro) -> bool:
        """Save a recorded macro to disk.

        Args:
            macro: The macro to save.

        Returns:
            True if saved successfully, False otherwise.
        """
        try:
            # Create safe filename from macro name
            safe_name = self._make_safe_filename(macro.name)
            file_path = self.storage_dir / f"{safe_name}.json"

            # Convert macro to dictionary
            macro_data = macro.to_dict()

            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(macro_data, f, indent=2)

            logger.info(f"Saved macro '{macro.name}' to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save macro '{macro.name}': {e}")
            return False

    def load_macro(self, filename: str) -> Optional[RecordedMacro]:
        """Load a recorded macro from disk.

        Args:
            filename: Name of the file to load (without path).

        Returns:
            RecordedMacro instance if loaded successfully, None otherwise.
        """
        try:
            file_path = self.storage_dir / filename

            if not file_path.exists():
                logger.error(f"Macro file not found: {file_path}")
                return None

            # Load from file
            with open(file_path, 'r', encoding='utf-8') as f:
                macro_data = json.load(f)

            # Create macro from data
            macro = RecordedMacro.from_dict(macro_data)

            logger.info(f"Loaded macro '{macro.name}' from {file_path}")
            return macro

        except Exception as e:
            logger.error(f"Failed to load macro from '{filename}': {e}")
            return None

    def load_all_macros(self) -> List[RecordedMacro]:
        """Load all recorded macros from storage.

        Returns:
            List of RecordedMacro instances.
        """
        macros = []

        try:
            # Find all .json files in storage directory
            for file_path in self.storage_dir.glob("*.json"):
                macro = self.load_macro(file_path.name)
                if macro:
                    macros.append(macro)

            logger.info(f"Loaded {len(macros)} recorded macros from storage")

        except Exception as e:
            logger.error(f"Failed to load macros: {e}")

        return macros

    def delete_macro(self, macro_name: str) -> bool:
        """Delete a recorded macro from storage.

        Args:
            macro_name: Name of the macro to delete.

        Returns:
            True if deleted successfully, False otherwise.
        """
        try:
            safe_name = self._make_safe_filename(macro_name)
            file_path = self.storage_dir / f"{safe_name}.json"

            if not file_path.exists():
                logger.warning(
                    f"Macro file not found for deletion: {file_path}")
                return False

            file_path.unlink()
            logger.info(f"Deleted macro '{macro_name}' from {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete macro '{macro_name}': {e}")
            return False

    def macro_exists(self, macro_name: str) -> bool:
        """Check if a macro with the given name exists.

        Args:
            macro_name: Name of the macro to check.

        Returns:
            True if macro exists, False otherwise.
        """
        safe_name = self._make_safe_filename(macro_name)
        file_path = self.storage_dir / f"{safe_name}.json"
        return file_path.exists()

    def get_all_macro_names(self) -> List[str]:
        """Get names of all stored macros.

        Returns:
            List of macro names.
        """
        names = []

        try:
            for file_path in self.storage_dir.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        names.append(data.get("name", file_path.stem))
                except Exception as e:
                    logger.warning(
                        f"Could not read macro name from {file_path}: {e}")

        except Exception as e:
            logger.error(f"Failed to get macro names: {e}")

        return names

    @staticmethod
    def _make_safe_filename(name: str) -> str:
        """Convert a macro name to a safe filename.

        Args:
            name: The macro name.

        Returns:
            Safe filename string.
        """
        # Replace invalid characters with underscores
        safe = "".join(c if c.isalnum() or c in (
            ' ', '-', '_') else '_' for c in name)
        # Replace spaces with underscores and collapse multiple underscores
        safe = "_".join(safe.split())
        return safe.lower()
