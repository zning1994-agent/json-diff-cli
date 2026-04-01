"""Output formatting for different formats."""

import json
from enum import Enum
from typing import Any, Dict, List

import jsonpatch

from .differ import DiffResult


class OutputFormat(Enum):
    """Supported output formats."""
    TERMINAL = 'terminal'
    JSON_PATCH = 'json-patch'
    SUMMARY = 'summary'


def format_diff(result: DiffResult, fmt: OutputFormat) -> str:
    """
    Format diff result in the specified format.
    
    Args:
        result: The diff result to format
        fmt: The output format
    
    Returns:
        Formatted string
    """
    if fmt == OutputFormat.TERMINAL:
        return _format_terminal(result)
    elif fmt == OutputFormat.JSON_PATCH:
        return _format_json_patch(result)
    elif fmt == OutputFormat.SUMMARY:
        return _format_summary(result)
    else:
        return _format_terminal(result)


def _format_terminal(result: DiffResult) -> str:
    """Format result for terminal output."""
    from .renderer import render_diff
    
    return render_diff(result)


def _format_json_patch(result: DiffResult) -> str:
    """Format result as JSON Patch (RFC 6902)."""
    patches = diff_to_json_patch(result)
    return json.dumps(patches, indent=2, ensure_ascii=False)


def _format_summary(result: DiffResult) -> str:
    """Format result as summary text."""
    summary = result.summary
    
    lines = [
        "=== JSON Diff Summary ===",
        f"Left file:  {result.left_path}",
        f"Right file: {result.right_path}",
        "",
        "Changes:",
        f"  Additions:     {summary['additions']}",
        f"  Deletions:     {summary['deletions']}",
        f"  Modifications: {summary['modifications']}",
        f"  Total:         {summary['total']}",
    ]
    
    if not result.has_differences:
        lines.append("\nNo differences found.")
    
    return "\n".join(lines)


def diff_to_json_patch(result: DiffResult) -> List[Dict[str, Any]]:
    """
    Convert diff result to JSON Patch format (RFC 6902).
    
    Args:
        result: The diff result to convert
    
    Returns:
        List of JSON Patch operations
    """
    patches = []
    
    # Process additions - convert paths to JSON Pointer (RFC 6901)
    for path, value in result.additions.items():
        pointer = path_to_pointer(path)
        patches.append({
            "op": "add",
            "path": pointer,
            "value": value
        })
    
    # Process deletions
    for path, value in result.deletions.items():
        pointer = path_to_pointer(path)
        patches.append({
            "op": "remove",
            "path": pointer
        })
    
    # Process modifications
    for path, change in result.modifications.items():
        pointer = path_to_pointer(path)
        patches.append({
            "op": "replace",
            "path": pointer,
            "value": change.get('new_value')
        })
    
    return patches


def path_to_pointer(path: str) -> str:
    """
    Convert deepdiff path to JSON Pointer (RFC 6901).
    
    Examples:
        "root['key']" -> "/key"
        "root['a']['b']" -> "/a/b"
        "root[0]" -> "/0"
    """
    # Remove 'root' prefix
    path = path.replace('root', '')
    
    # Convert to pointer format
    parts = []
    for part in path.replace('[', ' ').replace(']', '').replace("'", '').split():
        if part:
            if part.isdigit():
                parts.append(f"/{part}")
            else:
                parts.append(f"/{part}")
    
    if not parts:
        return "/"
    
    return ''.join(parts)
