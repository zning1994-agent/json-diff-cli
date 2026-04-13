"""Core diff comparison logic."""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from deepdiff import DeepDiff


class DiffResult:
    """
    Result of comparing two JSON structures.

    Supports two construction patterns:
    1. From actual data: DiffResult(left_data, right_data) or DiffResult(left_data, right_data, left_path, right_path)
    2. From pre-computed diff: DiffResult(left_path, right_path, added, removed, changed, differences)
    """

    def __init__(
        self,
        left_data: Any = None,
        right_data: Any = None,
        left_path: Any = None,
        right_path: Any = None,
        diff: Any = None,
        added: Optional[Set[str]] = None,
        removed: Optional[Set[str]] = None,
        changed: Optional[Set[str]] = None,
        differences: Optional[Dict[str, Any]] = None,
    ):
        # Detect which construction pattern is being used
        # If left_data is a Path or string and left_path is None, positional left_path was intended
        if isinstance(left_data, (str, Path)) and left_path is None:
            left_path, left_data = left_data, None
        if isinstance(right_data, (str, Path)) and right_path is None:
            right_path, right_data = right_data, None

        self.left_data = left_data
        self.right_data = right_data
        self.left_path = left_path
        self.right_path = right_path
        self.diff = diff
        self.added = set(added) if added else set()
        self.removed = set(removed) if removed else set()
        self.changed = set(changed) if changed else set()
        self.differences = differences or {}

        # If differences dict provided, use it as diff
        if self.differences and not self.diff:
            self.diff = self.differences

        # Compute diff from data if both provided and diff not yet set
        if self.diff is None and self.left_data is not None and self.right_data is not None:
            self.diff = DeepDiff(self.left_data, self.right_data, ignore_order=False)

    def _strip_root(self, path_str: str) -> str:
        """Strip root[] prefix from top-level path, keep nested paths as-is."""
        # "root['age']" -> "age"
        # "root['user']['name']" -> "root['user']['name']" (keep nested format)
        if "']['" not in path_str and path_str.startswith("root['"):
            # Top-level simple key: root['age'] -> age
            import re
            m = re.match(r"root\['([^']+)'\]", path_str)
            if m:
                return m.group(1)
        return path_str

    def _get_value_at_path(self, path_str: str, data: Any) -> Any:
        """Get value from data following path_str like \"root['age']\" or \"root['user'][0]\"."""
        if data is None:
            return None
        parts = re.findall(r"\[('[^']*'|\d+)\]", path_str)
        current = data
        for p in parts:
            if current is None:
                return None
            if p.startswith("'"):
                current = current[p[1:-1]]
            else:
                current = current[int(p)]
        return current

    @property
    def has_differences(self) -> bool:
        """Check if there are any differences."""
        if self.diff is not None:
            if isinstance(self.diff, dict):
                return bool(self.diff)
            return bool(self.diff)
        return bool(self.added or self.removed or self.changed)

    def has_changes(self) -> bool:
        """Alias for has_differences (method form)."""
        return self.has_differences

    def get_changed_paths(self) -> Set[str]:
        """Return all changed paths as a set."""
        paths = set()
        if hasattr(self.additions, 'keys'):
            paths.update(str(k) for k in self.additions.keys())
        elif self.additions:
            paths.update(str(x) for x in self.additions)
        if hasattr(self.deletions, 'keys'):
            paths.update(str(k) for k in self.deletions.keys())
        elif self.deletions:
            paths.update(str(x) for x in self.deletions)
        if hasattr(self.modifications, 'keys'):
            paths.update(str(k) for k in self.modifications.keys())
        elif self.modifications:
            paths.update(str(x) for x in self.modifications)
        paths.update(str(p) for p in self.added)
        paths.update(str(p) for p in self.removed)
        paths.update(str(p) for p in self.changed)
        return paths

    @property
    def additions(self) -> Dict[str, Any]:
        """Get dictionary of added items (simple key -> value)."""
        result = {}
        # From pre-computed added set
        for path_str in self.added:
            key = self._strip_root(str(path_str))
            value = self._get_value_at_path(str(path_str), self.right_data)
            result[key] = value
        # From diff object
        if self.diff:
            from deepdiff.helper import SetOrdered
            items = self.diff.get('dictionary_item_added', self.diff.get('iterable_item_added', {}))
            if isinstance(items, SetOrdered):
                for path_str in items:
                    key = self._strip_root(str(path_str))
                    if key not in result:
                        value = self._get_value_at_path(str(path_str), self.right_data)
                        result[key] = value
            elif isinstance(items, dict):
                for k, v in items.items():
                    key = self._strip_root(str(k))
                    if key not in result:
                        result[key] = v
        return result

    @property
    def deletions(self) -> Dict[str, Any]:
        """Get dictionary of removed items (simple key -> value)."""
        result = {}
        for path_str in self.removed:
            key = self._strip_root(str(path_str))
            value = self._get_value_at_path(str(path_str), self.left_data)
            result[key] = value
        if self.diff:
            from deepdiff.helper import SetOrdered
            items = self.diff.get('dictionary_item_removed', self.diff.get('iterable_item_removed', {}))
            if isinstance(items, SetOrdered):
                for path_str in items:
                    key = self._strip_root(str(path_str))
                    if key not in result:
                        value = self._get_value_at_path(str(path_str), self.left_data)
                        result[key] = value
            elif isinstance(items, dict):
                for k, v in items.items():
                    key = self._strip_root(str(k))
                    if key not in result:
                        result[key] = v
        return result

    @property
    def modifications(self) -> Dict[str, Any]:
        """Get dictionary of modified items (value changes + type changes)."""
        result = {}
        # From pre-computed changed set
        for path_str in self.changed:
            key = self._strip_root(str(path_str))
            result[key] = {'old_value': None, 'new_value': None}
        # From diff object
        if self.diff:
            for path_str, change in self.diff.get('values_changed', {}).items():
                key = self._strip_root(str(path_str))
                if key not in result:
                    result[key] = change
            for path_str, change in self.diff.get('type_changes', {}).items():
                key = self._strip_root(str(path_str))
                if key not in result:
                    result[key] = {'old_value': change.get('old_value'), 'new_value': change.get('new_value')}
        return result

    @property
    def nested_changes(self) -> Dict[str, Any]:
        """Get nested structure changes."""
        if self.diff is None:
            return {}
        return self.diff.get('nested_changes', {})

    @property
    def summary(self) -> Dict[str, int]:
        """Get summary statistics as dict."""
        n_add = len(self.additions) or len(self.added)
        n_del = len(self.deletions) or len(self.removed)
        n_mod = len(self.modifications) or len(self.changed)
        return {
            'additions': n_add,
            'deletions': n_del,
            'modifications': n_mod,
            'total_changes': n_add + n_del + n_mod
        }

    def to_terminal(self) -> str:
        """Return terminal-formatted diff output as string."""
        from .renderer import render_diff
        from io import StringIO
        from rich.console import Console
        c = Console(file=StringIO())
        render_diff(self, console=c)
        return c.file.getvalue()

    def to_json_patch(self) -> str:
        """Return JSON Patch (RFC 6902) format as string."""
        from .formatter import diff_to_json_patch
        import json
        patches = diff_to_json_patch(self)
        return json.dumps(patches, indent=2, ensure_ascii=False)

    def to_summary(self) -> str:
        """Return human-readable summary string."""
        s = self.summary
        left = str(self.left_path) if self.left_path else 'N/A'
        right = str(self.right_path) if self.right_path else 'N/A'
        lines = [
            "=== JSON Diff Summary ===",
            f"Left file:  {left}",
            f"Right file: {right}",
            "",
            "Changes:",
            f"  Additions:     {s['additions']}",
            f"  Deletions:     {s['deletions']}",
            f"  Modifications: {s['modifications']}",
            f"  Total:         {s.get('total_changes', s.get('total', 0))}",
        ]
        if not self.has_differences:
            lines.append("\nNo differences found.")
        return "\n".join(lines)


def compare(left: Union[str, Path, dict, list], right: Union[str, Path, dict, list]) -> DiffResult:
    """
    Compare two JSON sources and return a DiffResult.

    Args:
        left: Path to the left JSON file, or a dict/list containing JSON data
        right: Path to the right JSON file, or a dict/list containing JSON data

    Returns:
        DiffResult containing the comparison results

    Raises:
        FileReadError: If files cannot be read
        InvalidJsonError: If files contain invalid JSON
    """
    from .exceptions import FileReadError, InvalidJsonError

    # Handle dict/list input directly
    if isinstance(left, (dict, list)):
        left_data = left
        left_path = None
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

    if isinstance(right, (dict, list)):
        right_data = right
        right_path = None
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
        right_data=right_data,
        left_path=left_path,
        right_path=right_path,
    )
