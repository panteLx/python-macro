"""Custom exceptions for MacroManager."""


class MacroError(Exception):
    """Base exception for all macro-related errors."""

    pass


class WindowNotFoundError(MacroError):
    """Raised when the target game window cannot be found."""

    def __init__(self, message: str = "Game window not found"):
        self.message = message
        super().__init__(self.message)


class KeyBindingError(MacroError):
    """Raised when there's an issue with key bindings."""

    def __init__(self, message: str = "Invalid key binding"):
        self.message = message
        super().__init__(self.message)


class MacroExecutionError(MacroError):
    """Raised when macro execution fails."""

    def __init__(self, message: str = "Macro execution failed"):
        self.message = message
        super().__init__(self.message)


class ConfigurationError(MacroError):
    """Raised when there's an issue with configuration."""

    def __init__(self, message: str = "Configuration error"):
        self.message = message
        super().__init__(self.message)
