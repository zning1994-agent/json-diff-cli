"""Core diff comparison logic for JSON files and data structures."""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from deepdiff import DeepDiff


@dataclass
class DiffResult:
    """Result of comparing two JSON structures.
    
    Attributes:
        left_data: The left (original) JSON data
        right_data: The right (modified) JSON data
        additions: Dict of added keys with their new values
        deletions: Dict of deleted keys with their old values
        modifications: Dict of modified keys with old/new values
    """
    
    left_data: Any
    right_data: Any
    additions: Dict[str, Any] = field(default_factory=dict)
    deletions: Dict[str, Any] = field(default_factory=dict)
    modifications: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize diff comparison."""
        diff = DeepDiff(self.left_data, self.right_data, ignore_order=False, verbose_level=2)
        self._parse_diff(diff)
    
    def _parse_diff(self, diff: DeepDiff):
        """Parse DeepDiff output into additions, deletions, modifications."""
        # Helper to extract the key from DeepDiff path
        def get_key(path: str) -> str:
            # DeepDiff paths like: root['key'] or root['user']['email']
            # For top-level keys, extract just 'key'
            # For nested, format as root['user']['email']
            if path.startswith("root['"):
                # Check if it's a top-level key
                match = re.match(r"root\['([^']+)'\]", path)
                if match:
                    # Top-level key
                    return match.group(1)
                # Nested path - keep as is
                return path
            elif path.startswith('root.'):
                # Old format like root.key.nested
                parts = path.replace('root.', '').split('.')
                if len(parts) == 1:
                    return parts[0]
                # Convert to root['key']['nested'] format
                return "root['" + "']['".join(parts) + "']"
            return path
        
        # Parse additions (dictionary items added)
        if 'dictionary_item_added' in diff:
            for path, value in diff['dictionary_item_added'].items():
                key = get_key(path)
                self.additions[key] = value
        
        # Parse additions (iterable items added)
        if 'iterable_item_added' in diff:
            for path, value in diff['iterable_item_added'].items():
                key = get_key(path)
                self.additions[key] = value
        
        # Parse type changes as modifications
        if 'type_changes' in diff:
            for path, change in diff['type_changes'].items():
                key = get_key(path)
                self.modifications[key] = {
                    'old_value': change.get('old_value'),
                    'new_value': change.get('new_value')
                }
        
        # Parse value changes
        if 'values_changed' in diff:
            for path, change in diff['values_changed'].items():
                key = get_key(path)
                self.modifications[key] = {
                    'old_value': change.get('old_value'),
                    'new_value': change.get('new_value')
                }
        
        # Parse nested changes
        if 'nested_changes' in diff:
            for path, change in diff['nested_changes'].items():
                key = get_key(path)
                if 'root' in key:
                    self.modifications[key] = {
                        'old_value': change.get('old_value'),
                        'new_value': change.get('new_value')
                    }
        
        # Parse deletions (dictionary items removed)
        if 'dictionary_item_removed' in diff:
            for path, value in diff['dictionary_item_removed'].items():
                key = get_key(path)
                self.deletions[key] = value
        
        # Parse deletions (iterable items removed)
        if 'iterable_item_removed' in diff:
            for path, value in diff['iterable_item_removed'].items():
                key = get_key(path)
                self.deletions[key] = value
    
    def has_changes(self) -> bool:
        """Check if there are any differences.
        
        Returns:
            True if there are any changes, False otherwise.
        """
        return bool(self.additions or self.deletions or self.modifications)
    
    @property
    def summary(self) -> Dict[str, int]:
        """Get summary statistics.
        
        Returns:
            Dict containing counts of additions, deletions, modifications,
            and total_changes.
        """
        total_changes = len(self.additions) + len(self.deletions) + len(self.modifications)
        return {
            'additions': len(self.additions),
            'deletions': len(self.deletions),
            'modifications': len(self.modifications),
            'total_changes': total_changes
        }
    
    def get_changed_paths(self) -> List[str]:
        """Get all changed paths.
        
        Returns:
            List of all paths that have changes.
        """
        paths = []
        paths.extend(self.additions.keys())
        paths.extend(self.deletions.keys())
        paths.extend(self.modifications.keys())
        return paths


def compare(
    left: Union[str, Path, Dict[str, Any]],
    right: Union[str, Path, Dict[str, Any]]
) -> DiffResult:
    """
    Compare two JSON sources (files or dicts) and return a DiffResult.
    
    Args:
        left: Path to the left JSON file OR a dict containing JSON data
        right: Path to the right JSON file OR a dict containing JSON data
    
    Returns:
        DiffResult containing the comparison results
    
    Raises:
        FileReadError: If file paths cannot be read
        InvalidJsonError: If files contain invalid JSON
    """
    from .exceptions import FileReadError, InvalidJsonError
    
    # Handle dict input directly
    if isinstance(left, dict):
        left_data = left
    else:
        left_path = Path(left)
        try:
            with open(left_path, 'r', encoding='utf-8') as f:
                left_data = json.load(f)
        except FileNotFoundError:
            raise FileReadError(f"File not found: {left_path}")
        except json.JSONDecodeError as e:
            raise InvalidJsonError(f"Invalid JSON in {left_path}: {e}")
        except Exception as e:
            raise FileReadError(f"Error reading {left_path}: {e}")
    
    # Handle dict input directly
    if isinstance(right, dict):
        right_data = right
    else:
        right_path = Path(right)
        try:
            with open(right_path, 'r', encoding='utf-8') as f:
                right_data = json.load(f)
        except FileNotFoundError:
            raise FileReadError(f"File not found: {right_path}")
        except json.JSONDecodeError as e:
            raise InvalidJsonError(f"Invalid JSON in {right_path}: {e}")
        except Exception as e:
            raise FileReadError(f"Error reading {right_path}: {e}")
    
    return DiffResult(
        left_data=left_data,
        right_data=right_data
    )
