"""Custom exceptions for json-diff-cli."""


class JsonDiffError(Exception):
    """Base exception for json-diff-cli."""
    pass


class FileReadError(JsonDiffError):
    """Raised when a file cannot be read."""
    pass


class InvalidJsonError(JsonDiffError):
    """Raised when a file contains invalid JSON."""
    pass


class OutputFormatError(JsonDiffError):
    """Raised when output format is invalid."""
    pass
