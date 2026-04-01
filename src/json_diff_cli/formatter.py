"""
Output formatting module.

Provides various output format conversions for diff results.
"""

import json
from typing import Dict, List, Any

from .differ import DiffResult, DiffEntry, ChangeType


def format_terminal(diff_result: DiffResult) -> str:
    """
    Format diff result for terminal display (plain text).
    
    Args:
        diff_result: The comparison result
        
    Returns:
        Formatted string for terminal display
    """
    if not diff_result.has_differences:
        return "✓ No differences found"
    
    lines = []
    
    # Summary
    summary = diff_result.summary
    lines.append(f"Found {summary['total']} difference(s):")
    
    # Additions
    if summary['additions'] > 0:
        lines.append(f"\n  + Added ({summary['additions']}):")
        for diff in diff_result.additions:
            lines.append(f"    {diff.path}: {diff.new_value}")
    
    # Deletions
    if summary['deletions'] > 0:
        lines.append(f"\n  - Deleted ({summary['deletions']}):")
        for diff in diff_result.deletions:
            lines.append(f"    {diff.path}: {diff.old_value}")
    
    # Changes
    if summary['changes'] > 0:
        lines.append(f"\n  ~ Modified ({summary['changes']}):")
        for diff in diff_result.changes:
            lines.append(f"    {diff.path}:")
            lines.append(f"      - {diff.old_value}")
            lines.append(f"      + {diff.new_value}")
    
    return "\n".join(lines)


def format_json_patch(diff_result: DiffResult) -> List[Dict[str, Any]]:
    """
    Format diff result as JSON Patch (RFC 6902).
    
    Args:
        diff_result: The comparison result
        
    Returns:
        List of JSON Patch operations
    """
    return diff_result.to_json_patch()


def format_summary(diff_result: DiffResult) -> str:
    """
    Format a brief summary of differences.
    
    Args:
        diff_result: The comparison result
        
    Returns:
        Summary string
    """
    summary = diff_result.summary
    
    if not diff_result.has_differences:
        return "✓ JSON files are identical"
    
    parts = []
    if summary['additions'] > 0:
        parts.append(f"{summary['additions']} addition(s)")
    if summary['deletions'] > 0:
        parts.append(f"{summary['deletions']} deletion(s)")
    if summary['changes'] > 0:
        parts.append(f"{summary['changes']} modification(s)")
    
    return f"✗ {', '.join(parts)}"


def format_json_output(diff_result: DiffResult) -> str:
    """
    Format diff result as machine-readable JSON.
    
    Args:
        diff_result: The comparison result
        
    Returns:
        JSON string
    """
    return json.dumps(diff_result.to_dict(), indent=2, default=str)


def format_verbose(diff_result: DiffResult) -> str:
    """
    Format diff result with verbose details.
    
    Args:
        diff_result: The comparison result
        
    Returns:
        Verbose formatted string
    """
    lines = []
    
    lines.append("=" * 60)
    lines.append("JSON DIFF REPORT")
    lines.append("=" * 60)
    
    summary = diff_result.summary
    lines.append(f"\nSummary:")
    lines.append(f"  Total differences: {summary['total']}")
    lines.append(f"  Additions: {summary['additions']}")
    lines.append(f"  Deletions: {summary['deletions']}")
    lines.append(f"  Modifications: {summary['changes']}")
    
    if diff_result.has_differences:
        lines.append("\n" + "-" * 60)
        lines.append("Details:")
        
        for diff in diff_result.differences:
            lines.append(f"\n  [{diff.change_type.value.upper()}] {diff.path}")
            
            if diff.old_value is not None:
                lines.append(f"    Old: {diff.old_value}")
            if diff.new_value is not None:
                lines.append(f"    New: {diff.new_value}")
    
    lines.append("\n" + "=" * 60)
    
    return "\n".join(lines)
