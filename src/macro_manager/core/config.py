"""Configuration management for MacroManager."""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

from macro_manager.core.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class Config:
    """Manages application configuration."""

    DEFAULT_CONFIG = {
        "start_key": "f1",
        "stop_key": "f2",
        "log_level": "INFO",
        "window_width": 1000,
        "window_height": 800,
    }

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize configuration manager.

        Args:
            config_dir: Directory to store configuration files.
                       Defaults to ./config in the project root.
        """
        if config_dir is None:
            # Default to config directory in project root
            # Use absolute path based on this file's location to work when run as admin
            self.config_dir = Path(__file__).resolve(
            ).parent.parent.parent.parent / "config"
        else:
            self.config_dir = Path(config_dir).resolve()

        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "macro_config.json"
        self._config: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded_config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    self._config = {**self.DEFAULT_CONFIG, **loaded_config}
                    logger.info(
                        f"Configuration loaded from {self.config_file}")
            else:
                logger.info("No configuration file found, using defaults")
                self._config = self.DEFAULT_CONFIG.copy()
                self.save()  # Save default configuration
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse configuration file: {e}")
            raise ConfigurationError(
                f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise ConfigurationError(f"Failed to load configuration: {e}")

    def save(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise ConfigurationError(f"Failed to save configuration: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key to retrieve.
            default: Default value if key doesn't exist.

        Returns:
            Configuration value or default.
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any, save: bool = True) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key to set.
            value: Value to set.
            save: Whether to immediately save to file.
        """
        self._config[key] = value
        if save:
            self.save()

    def update(self, updates: Dict[str, Any], save: bool = True) -> None:
        """Update multiple configuration values.

        Args:
            updates: Dictionary of key-value pairs to update.
            save: Whether to immediately save to file.
        """
        self._config.update(updates)
        if save:
            self.save()

    @property
    def key_bindings(self) -> Dict[str, str]:
        """Get current key bindings.

        Returns:
            Dictionary containing start_key and stop_key.
        """
        return {
            "start_key": self.get("start_key", "f1"),
            "stop_key": self.get("stop_key", "f2"),
        }

    def update_key_bindings(self, start_key: str, stop_key: str) -> None:
        """Update key bindings.

        Args:
            start_key: New start macro key.
            stop_key: New stop macro key.
        """
        self.update({"start_key": start_key, "stop_key": stop_key}, save=True)
