"""Output formatting for different formats."""

import json
from typing import Dict, List, Any, Optional

from .differ import generate_json_patch
from . import DiffResult, OutputFormat


class DiffFormatter:
    """Formatter for DiffResult objects."""
    
    def __init__(self, diff_result: DiffResult):
        """Initialize formatter with a diff result.
        
        Args:
            diff_result: The comparison result to format
        """
        self.diff_result = diff_result
    
    def to_terminal(self) -> str:
        """Format differences for terminal display (raw text version).
        
        Returns:
            Formatted string for terminal output
        """
        lines = []
        lines.append(f"Comparing: {self.diff_result.left_path}")
        lines.append(f"     with: {self.diff_result.right_path}")
        lines.append("-" * 50)
        
        if not self.diff_result.has_differences:
            lines.append("No differences found!")
            return "\n".join(lines)
        
        if self.diff_result.added:
            lines.append(f"\n[+] Added ({len(self.diff_result.added)}):")
            for path in sorted(self.diff_result.added):
                lines.append(f"    {path}")
        
        if self.diff_result.removed:
            lines.append(f"\n[-] Removed ({len(self.diff_result.removed)}):")
            for path in sorted(self.diff_result.removed):
                lines.append(f"    {path}")
        
        if self.diff_result.changed:
            lines.append(f"\n[~] Modified ({len(self.diff_result.changed)}):")
            for path in sorted(self.diff_result.changed):
                lines.append(f"    {path}")
        
        lines.append("-" * 50)
        lines.append(f"Total: {self.diff_result.total_changes} change(s)")
        
        return "\n".join(lines)
    
    def to_json_patch(self) -> str:
        """Format differences as JSON Patch (RFC 6902).
        
        Returns:
            JSON string of patch operations
        """
        patch = generate_json_patch(self.diff_result)
        return json.dumps(patch, indent=2, ensure_ascii=False)
    
    def to_summary(self) -> str:
        """Generate a brief summary of differences.
        
        Returns:
            Summary string
        """
        return self.diff_result.summary
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format.
        
        Returns:
            Dictionary representation
        """
        return {
            "left": self.diff_result.left_path,
            "right": self.diff_result.right_path,
            "has_differences": self.diff_result.has_differences,
            "total_changes": self.diff_result.total_changes,
            "added": sorted(self.diff_result.added),
            "removed": sorted(self.diff_result.removed),
            "changed": sorted(self.diff_result.changed),
            "differences": self.diff_result.differences,
        }


def format_diff(diff_result: DiffResult, fmt: OutputFormat = OutputFormat.TERMINAL) -> str:
    """Format a diff result in the specified format.
    
    Args:
        diff_result: The comparison result
        fmt: Output format
        
    Returns:
        Formatted string
    """
    formatter = DiffFormatter(diff_result)
    
    if fmt == OutputFormat.TERMINAL:
        return formatter.to_terminal()
    elif fmt == OutputFormat.JSON_PATCH:
        return formatter.to_json_patch()
    elif fmt == OutputFormat.SUMMARY:
        return formatter.to_summary()
    else:
        return formatter.to_terminal()
