"""Core JSON comparison logic using deepdiff."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from deepdiff import DeepDiff

from .exceptions import ComparisonError, FileReadError, InvalidJsonError


class DiffType(Enum):
    """Types of differences."""
    ADDED = "added"
    DELETED = "deleted"
    CHANGED = "changed"
    TYPE_CHANGED = "type_changed"
    ARRAY_ITEM_ADDED = "array_item_added"
    ARRAY_ITEM_REMOVED = "array_item_removed"


@dataclass
class DiffEntry:
    """Single difference entry."""
    path: str
    diff_type: DiffType
    old_value: Any = None
    new_value: Any = None
    path_parts: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.path_parts and self.path:
            # Parse path like "root['key']['nested']" into parts
            import re
            parts = re.findall(r"\[([^\]]+)\]|\.(\w+)", self.path)
            self.path_parts = [p[0] or p[1] for p in parts if p]
            if not self.path_parts:
                self.path_parts = [self.path]


@dataclass
class DiffResult:
    """Result of JSON comparison."""
    left_path: Union[str, Path]
    right_path: Union[str, Path]
    additions: List[DiffEntry] = field(default_factory=list)
    deletions: List[DiffEntry] = field(default_factory=list)
    modifications: List[DiffEntry] = field(default_factory=list)
    type_changes: List[DiffEntry] = field(default_factory=list)
    raw_diff: Optional[Dict[str, Any]] = None

    @property
    def has_differences(self) -> bool:
        """Check if there are any differences."""
        return bool(self.additions or self.deletions or self.modifications or self.type_changes)

    @property
    def total_changes(self) -> int:
        """Total number of changes."""
        return (
            len(self.additions)
            + len(self.deletions)
            + len(self.modifications)
            + len(self.type_changes)
        )

    @property
    def summary(self) -> str:
        """Get summary string."""
        if not self.has_differences:
            return "No differences found."

        parts = []
        if self.additions:
            parts.append(f"{len(self.additions)} addition(s)")
        if self.deletions:
            parts.append(f"{len(self.deletions)} deletion(s)")
        if self.modifications:
            parts.append(f"{len(self.modifications)} modification(s)")
        if self.type_changes:
            parts.append(f"{len(self.type_changes)} type change(s)")

        return f"Total: {self.total_changes} change(s) - " + ", ".join(parts)


def _convert_deepdiff_path(path: str) -> str:
    """Convert deepdiff path to readable format."""
    import re
    # Convert "root['key']" to "root.key" format for display
    parts = re.findall(r"\[([^\]]+)\]|\.(\w+)", path)
    readable_parts = []
    for p in parts:
        part = p[0] or p[1]
        # Quote strings that need it
        if part.isdigit():
            readable_parts.append(f"[{part}]")
        else:
            readable_parts.append(f".{part}")
    result = "".join(readable_parts)
    return result.lstrip(".") or "root"


def _classify_diff(raw_diff: Dict[str, Any]) -> tuple[List[DiffEntry], List[DiffEntry], List[DiffEntry], List[DiffEntry]]:
    """Classify deepdiff results into categorized entries."""
    additions = []
    deletions = []
    modifications = []
    type_changes = []

    # Handle added items
    for path, value in raw_diff.get("dictionary_item_added", {}).items():
        entry = DiffEntry(
            path=_convert_deepdiff_path(path),
            diff_type=DiffType.ADDED,
            new_value=value
        )
        additions.append(entry)

    for path, value in raw_diff.get("iterable_item_added", {}).items():
        entry = DiffEntry(
            path=_convert_deepdiff_path(path),
            diff_type=DiffType.ARRAY_ITEM_ADDED,
            new_value=value
        )
        additions.append(entry)

    # Handle deleted items
    for path, value in raw_diff.get("dictionary_item_removed", {}).items():
        entry = DiffEntry(
            path=_convert_deepdiff_path(path),
            diff_type=DiffType.DELETED,
            old_value=value
        )
        deletions.append(entry)

    for path, value in raw_diff.get("iterable_item_removed", {}).items():
        entry = DiffEntry(
            path=_convert_deepdiff_path(path),
            diff_type=DiffType.ARRAY_ITEM_REMOVED,
            old_value=value
        )
        deletions.append(entry)

    # Handle value changes
    for path, changes in raw_diff.get("values_changed", {}).items():
        entry = DiffEntry(
            path=_convert_deepdiff_path(path),
            diff_type=DiffType.CHANGED,
            old_value=changes.get("old_value"),
            new_value=changes.get("new_value")
        )
        modifications.append(entry)

    # Handle type changes
    for path, changes in raw_diff.get("type_changes", {}).items():
        entry = DiffEntry(
            path=_convert_deepdiff_path(path),
            diff_type=DiffType.TYPE_CHANGED,
            old_value=changes.get("old_value"),
            new_value=changes.get("new_value")
        )
        type_changes.append(entry)

    return additions, deletions, modifications, type_changes


def compare(left_data: Union[str, Path, Dict[str, Any]], right_data: Union[str, Path, Dict[str, Any]]) -> DiffResult:
    """
    Compare two JSON data sources.

    Args:
        left_data: Path to left JSON file or dict
        right_data: Path to right JSON file or dict

    Returns:
        DiffResult containing all differences

    Raises:
        FileReadError: If file cannot be read
        InvalidJsonError: If file contains invalid JSON
        ComparisonError: If comparison fails
    """
    try:
        # Load left data
        if isinstance(left_data, (str, Path)):
            left_path = Path(left_data)
            if not left_path.exists():
                raise FileReadError(f"File not found: {left_path}")
            with open(left_path, "r", encoding="utf-8") as f:
                left_json = json.load(f)
        else:
            left_json = left_data
            left_path = Path("input")

        # Load right data
        if isinstance(right_data, (str, Path)):
            right_path = Path(right_data)
            if not right_path.exists():
                raise FileReadError(f"File not found: {right_path}")
            with open(right_path, "r", encoding="utf-8") as f:
                right_json = json.load(f)
        else:
            right_json = right_data
            right_path = Path("input")

    except json.JSONDecodeError as e:
        raise InvalidJsonError(f"Invalid JSON: {e}")
    except IOError as e:
        raise FileReadError(f"Failed to read file: {e}")

    try:
        # Perform deep comparison
        raw_diff = DeepDiff(left_json, right_json, ignore_order=False, report_repetition=True)
        raw_dict = raw_diff.to_dict() if hasattr(raw_diff, "to_dict") else dict(raw_diff)

        additions, deletions, modifications, type_changes = _classify_diff(raw_dict)

        return DiffResult(
            left_path=left_path,
            right_path=right_path,
            additions=additions,
            deletions=deletions,
            modifications=modifications,
            type_changes=type_changes,
            raw_diff=raw_dict
        )

    except Exception as e:
        raise ComparisonError(f"Comparison failed: {e}")


def compare_files(left_path: Union[str, Path], right_path: Union[str, Path]) -> DiffResult:
    """Compare two JSON files. Alias for compare() for clarity."""
    return compare(left_path, right_path)
