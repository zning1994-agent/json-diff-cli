"""
Core JSON comparison module.

Provides the main comparison logic using deepdiff for deep comparison
of nested JSON structures.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum

try:
    from deepdiff import DeepDiff
    from deepdiff.model import DiffLevel
    DEEPDIFF_AVAILABLE = True
except ImportError:
    DEEPDIFF_AVAILABLE = False

from .exceptions import ComparisonError


class ChangeType(Enum):
    """Types of differences between JSON values."""
    ADDED = "added"
    DELETED = "deleted"
    CHANGED = "changed"
    TYPE_CHANGED = "type_changed"
    NESTED_CHANGE = "nested_change"


@dataclass
class DiffEntry:
    """Represents a single difference entry."""
    path: str
    change_type: ChangeType
    old_value: Any = None
    new_value: Any = None
    path_parts: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.path_parts and self.path:
            # Convert path like "root['key'][0]" to parts
            self.path_parts = self._parse_path(self.path)
    
    def _parse_path(self, path: str) -> List[str]:
        """Parse a DeepDiff path string into parts."""
        parts = []
        current = ""
        in_bracket = False
        
        for char in path:
            if char == "[":
                if current:
                    parts.append(current)
                    current = ""
                in_bracket = True
            elif char == "]":
                if current:
                    parts.append(current.strip("'\""))
                    current = ""
                in_bracket = False
            elif char == "." and not in_bracket:
                if current:
                    parts.append(current)
                    current = ""
            else:
                current += char
        
        if current:
            parts.append(current)
        
        return parts
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'path': self.path,
            'change_type': self.change_type.value,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'path_parts': self.path_parts
        }


@dataclass
class DiffResult:
    """Container for comparison results."""
    left_data: Any
    right_data: Any
    differences: List[DiffEntry] = field(default_factory=list)
    raw_diff: Optional[Dict] = None
    error: Optional[str] = None
    
    @property
    def has_differences(self) -> bool:
        """Check if there are any differences."""
        return len(self.differences) > 0
    
    @property
    def additions(self) -> List[DiffEntry]:
        """Get list of additions."""
        return [d for d in self.differences if d.change_type == ChangeType.ADDED]
    
    @property
    def deletions(self) -> List[DiffEntry]:
        """Get list of deletions."""
        return [d for d in self.differences if d.change_type == ChangeType.DELETED]
    
    @property
    def changes(self) -> List[DiffEntry]:
        """Get list of modifications."""
        return [d for d in self.differences if d.change_type == ChangeType.CHANGED]
    
    @property
    def summary(self) -> Dict[str, int]:
        """Get summary statistics."""
        return {
            'total': len(self.differences),
            'additions': len(self.additions),
            'deletions': len(self.deletions),
            'changes': len(self.changes)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'has_differences': self.has_differences,
            'differences': [d.to_dict() for d in self.differences],
            'summary': self.summary,
            'raw_diff': self.raw_diff
        }
    
    def to_json_patch(self) -> List[Dict[str, Any]]:
        """Convert to JSON Patch format (RFC 6902)."""
        patches = []
        
        for diff in self.differences:
            path = "/" + "/".join(diff.path_parts) if diff.path_parts else "/"
            
            if diff.change_type == ChangeType.ADDED:
                patches.append({
                    "op": "add",
                    "path": path,
                    "value": diff.new_value
                })
            elif diff.change_type == ChangeType.DELETED:
                patches.append({
                    "op": "remove",
                    "path": path
                })
            elif diff.change_type == ChangeType.CHANGED:
                patches.append({
                    "op": "replace",
                    "path": path,
                    "value": diff.new_value
                })
        
        return patches


def compare(
    left: Union[Dict, List, str],
    right: Union[Dict, List, str],
    ignore_order: bool = False,
    ignore_paths: Optional[List[str]] = None,
    **kwargs
) -> DiffResult:
    """
    Compare two JSON objects and return differences.
    
    Args:
        left: Left side JSON data (original)
        right: Right side JSON data (modified)
        ignore_order: Whether to ignore array order differences
        ignore_paths: List of paths to ignore (dot notation)
        **kwargs: Additional arguments passed to DeepDiff
        
    Returns:
        DiffResult containing all differences
        
    Raises:
        ComparisonError: If comparison fails
    """
    if not DEEPDIFF_AVAILABLE:
        raise ComparisonError(
            "deepdiff library is required for comparison. "
            "Please install it with: pip install deepdiff"
        )
    
    try:
        # Build DeepDiff parameters
        diff_kwargs = {
            'ignore_order': ignore_order,
            'report_repetition': True,
            'verbose_level': 2,
        }
        
        if ignore_paths:
            diff_kwargs['exclude_paths'] = ignore_paths
        
        diff_kwargs.update(kwargs)
        
        # Perform comparison
        diff = DeepDiff(left, right, **diff_kwargs)
        
        # Convert to our DiffResult format
        differences = []
        
        for key, value in diff.items():
            if key == 'dictionary_item_added':
                for path, new_val in value.items():
                    differences.append(DiffEntry(
                        path=path,
                        change_type=ChangeType.ADDED,
                        new_value=new_val
                    ))
            
            elif key == 'dictionary_item_removed':
                for path, old_val in value.items():
                    differences.append(DiffEntry(
                        path=path,
                        change_type=ChangeType.DELETED,
                        old_value=old_val
                    ))
            
            elif key == 'type_changes':
                for path, change in value.items():
                    differences.append(DiffEntry(
                        path=path,
                        change_type=ChangeType.TYPE_CHANGED,
                        old_value=change.get('old_value'),
                        new_value=change.get('new_value')
                    ))
            
            elif key == 'values_changed':
                for path, change in value.items():
                    differences.append(DiffEntry(
                        path=path,
                        change_type=ChangeType.CHANGED,
                        old_value=change.get('old_value'),
                        new_value=change.get('new_value')
                    ))
            
            elif key == 'type_changes':
                for path, change in value.items():
                    differences.append(DiffEntry(
                        path=path,
                        change_type=ChangeType.TYPE_CHANGED,
                        old_value=change.get('old_value'),
                        new_value=change.get('new_value')
                    ))
            
            elif key == 'nested_changed':
                for path, change in value.items():
                    differences.append(DiffEntry(
                        path=path,
                        change_type=ChangeType.NESTED_CHANGE,
                        old_value=change.get('old_value'),
                        new_value=change.get('new_value')
                    ))
            
            elif key == 'iterable_item_added':
                for path, new_val in value.items():
                    differences.append(DiffEntry(
                        path=path,
                        change_type=ChangeType.ADDED,
                        new_value=new_val
                    ))
            
            elif key == 'iterable_item_removed':
                for path, old_val in value.items():
                    differences.append(DiffEntry(
                        path=path,
                        change_type=ChangeType.DELETED,
                        old_value=old_val
                    ))
        
        return DiffResult(
            left_data=left,
            right_data=right,
            differences=differences,
            raw_diff=diff.to_dict() if hasattr(diff, 'to_dict') else dict(diff)
        )
        
    except Exception as e:
        raise ComparisonError(details=str(e))
