"""json-diff-cli: A Python CLI tool for comparing JSON files."""

__version__ = "0.1.0"

from .differ import DiffEntry, DiffResult, DiffType, compare, compare_files
from .formatter import Formatter, OutputFormat, format_diff
from .exceptions import (
    ComparisonError,
    FileReadError,
    InvalidJsonError,
    JsonDiffError,
    OutputFormatError,
)

__all__ = [
    # Version
    "__version__",
    # Diff types
    "DiffType",
    "DiffEntry",
    "DiffResult",
    # Comparison functions
    "compare",
    "compare_files",
    # Formatter
    "Formatter",
    "OutputFormat",
    "format_diff",
    # Exceptions
    "JsonDiffError",
    "FileReadError",
    "InvalidJsonError",
    "ComparisonError",
    "OutputFormatError",
]
