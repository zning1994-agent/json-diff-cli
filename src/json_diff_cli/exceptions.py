"""Custom exceptions for json-diff-cli."""


class JsonDiffError(Exception):
    """Base exception for json-diff-cli."""
    pass


class FileReadError(JsonDiffError):
    """Raised when a JSON file cannot be read."""
    pass


class InvalidJsonError(JsonDiffError):
    """Raised when a file does not contain valid JSON."""
    pass


class ComparisonError(JsonDiffError):
    """Raised when JSON comparison fails."""
    pass


class OutputFormatError(JsonDiffError):
    """Raised when output formatting fails."""
    pass
