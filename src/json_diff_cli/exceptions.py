"""
Custom exceptions for json-diff-cli.

This module defines all custom exceptions used by the package
for error handling and reporting.
"""


class JSONDiffError(Exception):
    """Base exception for json-diff-cli errors."""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class FileReadError(JSONDiffError):
    """Raised when a file cannot be read."""
    
    def __init__(self, message: str, file_path: str = None):
        self.file_path = file_path
        super().__init__(message)


class InvalidJSONError(JSONDiffError):
    """Raised when JSON content is invalid or malformed."""
    
    def __init__(self, message: str, json_content: str = None):
        self.json_content = json_content
        super().__init__(message)


class ComparisonError(JSONDiffError):
    """Raised when comparison between two JSON sources fails."""
    
    def __init__(self, message: str):
        super().__init__(message)


class OutputFormatError(JSONDiffError):
    """Raised when output formatting fails."""
    
    def __init__(self, message: str):
        super().__init__(message)
