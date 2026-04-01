"""Custom exceptions for json-diff-cli."""


class JsonDiffError(Exception):
    """Base exception for json-diff-cli."""
    pass


class FileReadError(JsonDiffError):
    """Raised when a file cannot be read."""
    pass


class InvalidJsonError(JsonDiffError):
    """Raised when JSON content is invalid."""
    pass


class ComparisonError(JsonDiffError):
    """Raised when comparison fails."""
    pass


class OutputFormatError(JsonDiffError):
    """Raised when output formatting fails."""
    pass
