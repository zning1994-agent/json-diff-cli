"""
Custom exceptions for json-diff-cli.
"""


class JsonDiffError(Exception):
    """Base exception for json-diff-cli errors."""
    
    def __init__(self, message: str, details: str = None):
        self.message = message
        self.details = details
        super().__init__(self.message)
    
    def __str__(self):
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class InvalidJsonError(JsonDiffError):
    """Raised when JSON parsing fails."""
    
    def __init__(self, file_path: str, details: str = None):
        super().__init__(
            message=f"Invalid JSON in file: {file_path}",
            details=details
        )


class FileAccessError(JsonDiffError):
    """Raised when file cannot be read or accessed."""
    
    def __init__(self, file_path: str, details: str = None):
        super().__init__(
            message=f"Cannot access file: {file_path}",
            details=details
        )


class ComparisonError(JsonDiffError):
    """Raised when JSON comparison fails."""
    
    def __init__(self, details: str = None):
        super().__init__(
            message="JSON comparison failed",
            details=details
        )
