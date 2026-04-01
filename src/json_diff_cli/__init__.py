"""json-diff-cli - JSON file comparison tool."""

__version__ = '0.1.0'

from .differ import compare, DiffResult
from .formatter import OutputFormat, format_diff, diff_to_json_patch
from .exceptions import (
    JsonDiffError,
    FileReadError,
    InvalidJsonError,
    OutputFormatError
)

__all__ = [
    '__version__',
    'compare',
    'DiffResult',
    'OutputFormat',
    'format_diff',
    'diff_to_json_patch',
    'JsonDiffError',
    'FileReadError',
    'InvalidJsonError',
    'OutputFormatError',
]
