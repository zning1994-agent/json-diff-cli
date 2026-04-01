"""Core JSON comparison logic using deepdiff."""

import json
import importlib.resources
from pathlib import Path
from typing import Any, Union, Dict, List

from deepdiff import DeepDiff

from .exceptions import FileReadError, InvalidJsonError, ComparisonError
from . import DiffResult


def load_json(source: Union[str, Path, Dict, List]) -> Any:
    """Load JSON from a file path or return the object directly.
    
    Args:
        source: File path (str/Path) or JSON object (dict/list)
        
    Returns:
        Parsed JSON object
        
    Raises:
        FileReadError: If file cannot be read
        InvalidJsonError: If JSON content is invalid
    """
    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.exists():
            raise FileReadError(f"File not found: {source}")
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise InvalidJsonError(f"Invalid JSON in {source}: {e}")
        except IOError as e:
            raise FileReadError(f"Cannot read {source}: {e}")
    else:
        return source


def compare_json(left: Any, right: Any) -> DiffResult:
    """Compare two JSON structures.
    
    Args:
        left: Left JSON source (file path or object)
        right: Right JSON source (file path or object)
        
    Returns:
        DiffResult containing all differences
    """
    try:
        left_data = load_json(left)
        right_data = load_json(right)
        
        diff = DeepDiff(left_data, right_data, ignore_order=False, verbose_level=2)
        
        added = set()
        removed = set()
        changed = set()
        
        if 'dictionary_item_added' in diff:
            for path in diff['dictionary_item_added']:
                added.add(path)
        
        if 'dictionary_item_removed' in diff:
            for path in diff['dictionary_item_removed']:
                removed.add(path)
        
        if 'values_changed' in diff:
            for path in diff['values_changed']:
                changed.add(path)
        
        if 'type_changes' in diff:
            for path in diff['type_changes']:
                changed.add(path)
        
        left_path = str(left) if not isinstance(left, (dict, list)) else "<inline>"
        right_path = str(right) if not isinstance(right, (dict, list)) else "<inline>"
        
        return DiffResult(
            left_path=left_path,
            right_path=right_path,
            differences=diff.to_dict(),
            added=added,
            removed=removed,
            changed=changed,
        )
        
    except (FileReadError, InvalidJsonError):
        raise
    except Exception as e:
        raise ComparisonError(f"Comparison failed: {e}")


def generate_json_patch(diff_result: DiffResult) -> List[Dict]:
    """Generate JSON Patch (RFC 6902) format from diff result.
    
    Args:
        diff_result: The DiffResult to convert
        
    Returns:
        List of JSON Patch operations
    """
    import jsonpatch
    
    patch = []
    
    for path in sorted(diff_result.removed):
        patch.append({
            "op": "remove",
            "path": path_to_json_pointer(path)
        })
    
    for path in sorted(diff_result.added):
        patch.append({
            "op": "add",
            "path": path_to_json_pointer(path),
            "value": diff_result.differences.get('dictionary_item_added', {}).get(path)
        })
    
    for path in sorted(diff_result.changed):
        changes = diff_result.differences.get('values_changed', {}).get(path, {})
        patch.append({
            "op": "replace",
            "path": path_to_json_pointer(path),
            "value": changes.get('new_value')
        })
    
    return patch


def path_to_json_pointer(path: str) -> str:
    """Convert deepdiff path to JSON Pointer format.
    
    Args:
        path: Deepdiff path like "root['key']['subkey']"
        
    Returns:
        JSON Pointer like "/key/subkey"
    """
    import re
    
    path = path.replace("root", "")
    parts = re.findall(r"\['([^']+)'\]", path)
    return "/" + "/".join(parts) if parts else "/"
