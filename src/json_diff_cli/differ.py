"""Core diff comparison logic."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from deepdiff import DeepDiff


@dataclass
class DiffResult:
    """Result of comparing two JSON structures."""
    
    left_data: Any
    right_data: Any
    left_path: Optional[Path] = None
    right_path: Optional[Path] = None
    diff: Optional[DeepDiff] = None
    
    def __post_init__(self):
        # Support simple dict-only construction: DiffResult(left_dict, right_dict)
        # If left_path is a dict, it means first arg is left_data
        if isinstance(self.left_path, (dict, list)) and self.left_data is not None:
            # Swap: left_path actually contains left_data
            self.left_data, self.right_data = self.left_path, self.left_data
            self.left_path = None
            self.right_path = None
        if self.diff is None and self.left_data is not None and self.right_data is not None:
            self.diff = DeepDiff(self.left_data, self.right_data, ignore_order=False)
    
    @property
    def has_differences(self) -> bool:
        """Check if there are any differences."""
        return bool(self.diff)
    
    @property
    def additions(self) -> Dict[str, Any]:
        """Get dictionary of added items."""
        return self.diff.get('dictionary_item_added', 
                            self.diff.get('iterable_item_added', {}))
    
    @property
    def deletions(self) -> Dict[str, Any]:
        """Get dictionary of removed items."""
        return self.diff.get('dictionary_item_removed',
                            self.diff.get('iterable_item_removed', {}))
    
    @property
    def modifications(self) -> Dict[str, Any]:
        """Get dictionary of modified items."""
        return self.diff.get('values_changed', {})
    
    @property
    def nested_changes(self) -> Dict[str, Any]:
        """Get nested structure changes."""
        return self.diff.get('nested_changes', {})
    
    @property
    def summary(self) -> Dict[str, int]:
        """Get summary statistics."""
        return {
            'additions': len(self.additions),
            'deletions': len(self.deletions),
            'modifications': len(self.modifications),
            'total_changes': len(self.diff)
        }
    
    def get_all_changes(self) -> List[Dict[str, Any]]:
        """Get all changes as a list of structured items."""
        changes = []
        
        for path, value in self.additions.items():
            changes.append({
                'type': 'addition',
                'path': path,
                'value': value
            })
        
        for path, value in self.deletions.items():
            changes.append({
                'type': 'deletion',
                'path': path,
                'value': value
            })
        
        for path, change in self.modifications.items():
            changes.append({
                'type': 'modification',
                'path': path,
                'old_value': change.get('old_value'),
                'new_value': change.get('new_value')
            })
        
        return changes


def compare(left: Union[str, Path], right: Union[str, Path]) -> DiffResult:
    """
    Compare two JSON files and return a DiffResult.
    
    Args:
        left: Path to the left (original) JSON file
        right: Path to the right (modified) JSON file
    
    Returns:
        DiffResult containing the comparison results
    
    Raises:
        FileReadError: If files cannot be read
        InvalidJsonError: If files contain invalid JSON
    """
    from .exceptions import FileReadError, InvalidJsonError
    
    left_path = Path(left)
    right_path = Path(right)
    
    # Read and parse left file
    try:
        with open(left_path, 'r', encoding='utf-8') as f:
            left_data = json.load(f)
    except FileNotFoundError:
        raise FileReadError(f"File not found: {left_path}")
    except json.JSONDecodeError as e:
        raise InvalidJsonError(f"Invalid JSON in {left_path}: {e}")
    except Exception as e:
        raise FileReadError(f"Error reading {left_path}: {e}")
    
    # Read and parse right file
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
        left_path=left_path,
        right_path=right_path,
        left_data=left_data,
        right_data=right_data
    )
