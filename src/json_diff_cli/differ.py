"""
Core JSON diff module using deepdiff library.

This module provides the core comparison logic for JSON files,
supporting nested objects and arrays with detailed path traversal.
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from deepdiff import DeepDiff
from deepdiff.model import (
    DiffLevel,
    DictChanges,
    NestedContentChange,
    RootLevelDiffTypes,
    TextDiff,
    Tree,
    TypeChange,
    UnionTypeChange,
)

from .exceptions import FileReadError, InvalidJSONError


class ChangeType(Enum):
    """Enumeration of JSON difference types."""
    
    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"
    TYPE_CHANGE = "type_change"
    ARRAY_ITEM_ADDED = "array_item_added"
    ARRAY_ITEM_REMOVED = "array_item_removed"


@dataclass
class DiffEntry:
    """
    Represents a single difference entry with path and change details.
    
    Attributes:
        path: JSON path to the changed element (e.g., "a.b[0].c")
        change_type: Type of change (added, removed, changed, type_change)
        old_value: Original value (for removed/changed entries)
        new_value: New value (for added/changed entries)
        path_parts: List of path components for traversal
    """
    
    path: str
    change_type: ChangeType
    old_value: Any = None
    new_value: Any = None
    path_parts: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Parse path into components after initialization."""
        if not self.path_parts and self.path:
            # Parse path like "root['a']['b'][0]['c']" into ['a', 'b', '0', 'c']
            self.path_parts = self._parse_path(self.path)
    
    @staticmethod
    def _parse_path(path: str) -> List[str]:
        """
        Parse deepdiff path format into list of components.
        
        Examples:
            "root['a']['b']" -> ['a', 'b']
            "root[0]" -> ['0']
            "['a'][0].b" -> ['a', '0', 'b']
        """
        if path == "root":
            return []
        
        parts = []
        current = ""
        in_brackets = False
        in_quotes = False
        i = 0
        
        # Skip 'root' prefix
        if path.startswith("root"):
            path = path[4:]
        
        while i < len(path):
            char = path[i]
            
            if char == "[":
                # Save any accumulated content before brackets
                if current and not in_quotes:
                    parts.append(current)
                    current = ""
                in_brackets = True
                in_quotes = False
            elif char == "]":
                if in_brackets and current:
                    # Remove quotes if present
                    if current.startswith(("'", '"')) and current.endswith(("'", '"')):
                        current = current[1:-1]
                    parts.append(current)
                    current = ""
                in_brackets = False
            elif char == "'" or char == '"':
                in_quotes = not in_quotes
                if not in_brackets:
                    current += char
            elif char == ".":
                if current:
                    if current.startswith(("'", '"')) and current.endswith(("'", '"')):
                        current = current[1:-1]
                    parts.append(current)
                    current = ""
            else:
                current += char
            
            i += 1
        
        # Don't forget remaining content
        if current:
            if current.startswith(("'", '"')) and current.endswith(("'", '"')):
                current = current[1:-1]
            parts.append(current)
        
        return [p for p in parts if p]


@dataclass
class DiffResult:
    """
    Container for diff comparison results.
    
    Attributes:
        left_path: Path to the left JSON file
        right_path: Path to the right JSON file
        additions: List of entries that were added
        deletions: List of entries that were removed
        modifications: List of entries that were modified
        type_changes: List of entries with type changes
        identical: Boolean indicating if the two JSONs are identical
    """
    
    left_path: Union[str, Path]
    right_path: Union[str, Path]
    additions: List[DiffEntry] = field(default_factory=list)
    deletions: List[DiffEntry] = field(default_factory=list)
    modifications: List[DiffEntry] = field(default_factory=list)
    type_changes: List[DiffEntry] = field(default_factory=list)
    identical: bool = True
    
    @property
    def total_changes(self) -> int:
        """Total number of changes across all categories."""
        return (
            len(self.additions) +
            len(self.deletions) +
            len(self.modifications) +
            len(self.type_changes)
        )
    
    @property
    def has_changes(self) -> bool:
        """Check if there are any changes."""
        return not self.identical
    
    def get_all_entries(self) -> List[DiffEntry]:
        """Get all diff entries combined."""
        return (
            self.additions +
            self.deletions +
            self.modifications +
            self.type_changes
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "left": str(self.left_path),
            "right": str(self.right_path),
            "identical": self.identical,
            "summary": {
                "total_changes": self.total_changes,
                "additions": len(self.additions),
                "deletions": len(self.deletions),
                "modifications": len(self.modifications),
                "type_changes": len(self.type_changes),
            },
            "changes": {
                "added": [
                    {
                        "path": entry.path,
                        "value": entry.new_value,
                        "path_parts": entry.path_parts,
                    }
                    for entry in self.additions
                ],
                "removed": [
                    {
                        "path": entry.path,
                        "value": entry.old_value,
                        "path_parts": entry.path_parts,
                    }
                    for entry in self.deletions
                ],
                "changed": [
                    {
                        "path": entry.path,
                        "old_value": entry.old_value,
                        "new_value": entry.new_value,
                        "path_parts": entry.path_parts,
                    }
                    for entry in self.modifications
                ],
                "type_changed": [
                    {
                        "path": entry.path,
                        "old_value": entry.old_value,
                        "old_type": type(entry.old_value).__name__,
                        "new_value": entry.new_value,
                        "new_type": type(entry.new_value).__name__,
                        "path_parts": entry.path_parts,
                    }
                    for entry in self.type_changes
                ],
            },
        }


def load_json(source: Union[str, Path]) -> Any:
    """
    Load JSON from a file path or string content.
    
    Args:
        source: File path to JSON file or JSON string
        
    Returns:
        Parsed JSON data
        
    Raises:
        InvalidJSONError: If JSON is malformed
        FileReadError: If file cannot be read
    """
    # Try to read as file path first
    path = Path(source)
    if path.exists() and path.is_file():
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return None
                return json.loads(content)
        except json.JSONDecodeError as e:
            raise InvalidJSONError(f"Invalid JSON in file {source}: {e}")
        except OSError as e:
            raise FileReadError(f"Cannot read file {source}: {e}")
    
    # Try to parse as JSON string
    try:
        content = str(source).strip()
        if content.startswith(("{", "[")):
            return json.loads(content)
        # If it's a path that doesn't exist, try parsing as-is
        return json.loads(content)
    except json.JSONDecodeError:
        raise InvalidJSONError(f"Invalid JSON content: {source}")


def _classify_deepdiff_changes(diff: DeepDiff) -> Dict[str, List[DiffEntry]]:
    """
    Classify deepdiff results into structured DiffEntry lists.
    
    Args:
        diff: DeepDiff object containing comparison results
        
    Returns:
        Dictionary with categorized entries by change type
    """
    additions: List[DiffEntry] = []
    deletions: List[DiffEntry] = []
    modifications: List[DiffEntry] = []
    type_changes: List[DiffEntry] = []
    
    # Process dictionary item additions (new keys)
    if "dictionary_item_added" in diff:
        for path, value in diff["dictionary_item_added"].items():
            entry = DiffEntry(
                path=path,
                change_type=ChangeType.ADDED,
                new_value=value,
            )
            additions.append(entry)
    
    # Process dictionary item removals (removed keys)
    if "dictionary_item_removed" in diff:
        for path, value in diff["dictionary_item_removed"].items():
            entry = DiffEntry(
                path=path,
                change_type=ChangeType.REMOVED,
                old_value=value,
            )
            deletions.append(entry)
    
    # Process value changes
    if "values_changed" in diff:
        for path, change in diff["values_changed"].items():
            entry = DiffEntry(
                path=path,
                change_type=ChangeType.CHANGED,
                old_value=change.old_value,
                new_value=change.new_value,
            )
            modifications.append(entry)
    
    # Process type changes
    if "type_changes" in diff:
        for path, change in diff["type_changes"].items():
            entry = DiffEntry(
                path=path,
                change_type=ChangeType.TYPE_CHANGE,
                old_value=change.old_value,
                new_value=change.new_value,
            )
            type_changes.append(entry)
    
    # Process nested content changes
    if "nested_changes" in diff:
        for path, change in diff["nested_changes"].items():
            entry = DiffEntry(
                path=path,
                change_type=ChangeType.CHANGED,
                old_value=change.old_value,
                new_value=change.new_value,
            )
            modifications.append(entry)
    
    # Process array item additions
    if "array_item_added" in diff:
        for path, value in diff["array_item_added"].items():
            entry = DiffEntry(
                path=path,
                change_type=ChangeType.ARRAY_ITEM_ADDED,
                new_value=value,
            )
            additions.append(entry)
    
    # Process array item removals
    if "array_item_removed" in diff:
        for path, value in diff["array_item_removed"].items():
            entry = DiffEntry(
                path=path,
                change_type=ChangeType.ARRAY_ITEM_REMOVED,
                old_value=value,
            )
            deletions.append(entry)
    
    # Process attribute additions (for objects with __dict__)
    if "attribute_added" in diff:
        for path, value in diff["attribute_added"].items():
            entry = DiffEntry(
                path=path,
                change_type=ChangeType.ADDED,
                new_value=value,
            )
            additions.append(entry)
    
    # Process attribute removals
    if "attribute_removed" in diff:
        for path, value in diff["attribute_removed"].items():
            entry = DiffEntry(
                path=path,
                change_type=ChangeType.REMOVED,
                old_value=value,
            )
            deletions.append(entry)
    
    return {
        "additions": additions,
        "deletions": deletions,
        "modifications": modifications,
        "type_changes": type_changes,
    }


def compare(
    left: Union[str, Path, Dict[str, Any], List[Any]],
    right: Union[str, Path, Dict[str, Any], List[Any]],
    left_path: Optional[Union[str, Path]] = None,
    right_path: Optional[Union[str, Path]] = None,
    ignore_order: bool = False,
    significant_digits: Optional[int] = None,
    exclude_paths: Optional[List[str]] = None,
) -> DiffResult:
    """
    Compare two JSON sources and return structured diff results.
    
    This function performs a deep comparison of two JSON sources,
    supporting nested objects and arrays with detailed path tracking.
    
    Args:
        left: Left JSON source (file path, JSON string, or Python object)
        right: Right JSON source (file path, JSON string, or Python object)
        left_path: Optional path label for the left source (for display)
        right_path: Optional path label for the right source (for display)
        ignore_order: If True, ignore order in arrays (default: False)
        significant_digits: Number of significant digits for float comparison
        exclude_paths: List of paths to exclude from comparison
        
    Returns:
        DiffResult object containing all differences
        
    Raises:
        InvalidJSONError: If either source contains invalid JSON
        FileReadError: If a file cannot be read
        
    Example:
        >>> result = compare("old.json", "new.json")
        >>> print(f"Found {result.total_changes} differences")
        >>> for entry in result.modifications:
        ...     print(f"Changed: {entry.path}")
    """
    # Load JSON data
    if isinstance(left, (dict, list)):
        left_data = left
    else:
        left_data = load_json(left)
    
    if isinstance(right, (dict, list)):
        right_data = right
    else:
        right_data = load_json(right)
    
    # Determine display paths
    display_left = left_path or left
    display_right = right_path or right
    
    # Perform deep diff comparison
    diff_kwargs: Dict[str, Any] = {
        "ignore_order": ignore_order,
    }
    
    if significant_digits is not None:
        diff_kwargs["significant_digits"] = significant_digits
    
    if exclude_paths:
        diff_kwargs["exclude_paths"] = exclude_paths
    
    diff = DeepDiff(left_data, right_data, **diff_kwargs)
    
    # Classify changes
    classified = _classify_deepdiff_changes(diff)
    
    # Determine if identical
    identical = (
        len(classified["additions"]) == 0 and
        len(classified["deletions"]) == 0 and
        len(classified["modifications"]) == 0 and
        len(classified["type_changes"]) == 0
    )
    
    return DiffResult(
        left_path=display_left,
        right_path=display_right,
        additions=classified["additions"],
        deletions=classified["deletions"],
        modifications=classified["modifications"],
        type_changes=classified["type_changes"],
        identical=identical,
    )


def compare_files(
    left_path: Union[str, Path],
    right_path: Union[str, Path],
    **kwargs: Any,
) -> DiffResult:
    """
    Compare two JSON files and return structured diff results.
    
    Convenience function that specifically loads from files.
    
    Args:
        left_path: Path to the left JSON file
        right_path: Path to the right JSON file
        **kwargs: Additional arguments passed to compare()
        
    Returns:
        DiffResult object containing all differences
    """
    return compare(
        left=left_path,
        right=right_path,
        left_path=left_path,
        right_path=right_path,
        **kwargs,
    )
