"""
json-diff-cli - A Python CLI tool for comparing JSON files with colorful output.

This package provides both a command-line interface and a Python API
for comparing JSON files and displaying differences in a human-readable format.
"""

__version__ = "0.1.0"
__author__ = "json-diff-cli contributors"
__license__ = "MIT"

# Core comparison API
from .differ import (
    ChangeType,
    DiffEntry,
    DiffResult,
    compare,
    compare_files,
    load_json,
)

# Exceptions
from .exceptions import (
    ComparisonError,
    FileReadError,
    InvalidJSONError,
    JSONDiffError,
    OutputFormatError,
)

__all__ = [
    # Version
    "__version__",
    # Core API
    "ChangeType",
    "DiffEntry",
    "DiffResult",
    "compare",
    "compare_files",
    "load_json",
    # Exceptions
    "JSONDiffError",
    "FileReadError",
    "InvalidJSONError",
    "ComparisonError",
    "OutputFormatError",
]
