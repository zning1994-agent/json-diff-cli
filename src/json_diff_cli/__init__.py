"""JSON Diff CLI - A tool for comparing JSON files with colorful output."""

__version__ = "0.1.0"
__author__ = "Developer"

from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Optional


class OutputFormat(Enum):
    """Output format options."""
    TERMINAL = "terminal"
    JSON_PATCH = "json-patch"
    SUMMARY = "summary"


@dataclass
class DiffResult:
    """Result of comparing two JSON structures.
    
    Attributes:
        left_path: Path to the left JSON file
        right_path: Path to the right JSON file
        differences: Dictionary of differences from deepdiff
        added: Set of added paths
        removed: Set of removed paths
        changed: Set of changed paths
    """
    left_path: str
    right_path: str
    differences: dict = field(default_factory=dict)
    added: set = field(default_factory=set)
    removed: set = field(default_factory=set)
    changed: set = field(default_factory=set)
    
    @property
    def has_differences(self) -> bool:
        """Check if there are any differences."""
        return bool(self.added or self.removed or self.changed)
    
    @property
    def total_changes(self) -> int:
        """Total number of changes."""
        return len(self.added) + len(self.removed) + len(self.changed)
    
    @property
    def summary(self) -> str:
        """Generate a human-readable summary."""
        lines = [
            f"Comparison: {self.left_path} vs {self.right_path}",
            f"Total changes: {self.total_changes}",
        ]
        if self.added:
            lines.append(f"  Added: {len(self.added)}")
        if self.removed:
            lines.append(f"  Removed: {len(self.removed)}")
        if self.changed:
            lines.append(f"  Modified: {len(self.changed)}")
        if not self.has_differences:
            lines.append("  No differences found!")
        return "\n".join(lines)


def compare(left: Any, right: Any) -> DiffResult:
    """Compare two JSON structures and return the differences.
    
    Args:
        left: Left JSON structure (path string or dict/list)
        right: Right JSON structure (path string or dict/list)
        
    Returns:
        DiffResult containing the differences
    """
    from .differ import compare_json
    return compare_json(left, right)


__all__ = [
    "DiffResult",
    "OutputFormat",
    "compare",
    "__version__",
]
