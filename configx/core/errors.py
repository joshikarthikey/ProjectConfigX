"""
configx.core.errors
Error system for ConfigX.

Developed & Maintained by Aditya Gaur, 2025

"""

class ConfigXError(Exception):
    """Base class for all ConfigX-related errors."""
    pass


# Path-related errors

class ConfigPathError(ConfigXError):
    """Generic path problem."""
    pass

class ConfigPathNotFoundError(ConfigPathError):
    """Raised when a requested path does not exist."""
    def __init__(self, path: str):
        super().__init__(f'Path "{path}" does not exist.')
        self.path = path

class ConfigInvalidPathError(ConfigPathError):
    """Raised when a path is malformed or illegal."""
    def __init__(self, path: str, reason: str = ""):
        msg = f'Invalid path "{path}". {reason}'
        super().__init__(msg)
        self.path = path
        self.reason = reason

class ConfigStrictModeError(ConfigPathError):
    """Raised when strict mode prevents an auto-creation or modification."""
    def __init__(self, path: str):
        super().__init__(f'Cannot create or modify "{path}" in strict mode.')
        self.path = path



# Node structure errors

class ConfigNodeError(ConfigXError):
    """Generic node-related problem."""
    pass

class ConfigNodeStructureError(ConfigNodeError):
    """Raised when attempting illegal modifications to a node's structure."""
    def __init__(self, path: str, detail: str = ""):
        msg = f'Illegal structure at "{path}". {detail}'
        super().__init__(msg)
        self.path = path



# Value/type errors (future)

class ConfigValueError(ConfigXError):
    """Generic value-related errors."""
    pass

class ConfigTypeMismatchError(ConfigValueError):
    """Raised when assigning a value of incompatible type."""
    def __init__(self, path: str, expected: str, actual: str):
        msg = f'Type mismatch at "{path}". Expected {expected}, got {actual}.'
        super().__init__(msg)
        self.path = path
        self.expected = expected
        self.actual = actual



# Import/export errors

class ConfigImportError(ConfigXError):
    """Raised when input data cannot be imported."""
    pass

class ConfigInvalidFormatError(ConfigImportError):
    """Raised when the imported structure is invalid."""
    def __init__(self, detail: str):
        super().__init__(f"Invalid configuration format: {detail}")

class ConfigExportError(ConfigXError):
    """Raised on export failure."""
    pass
