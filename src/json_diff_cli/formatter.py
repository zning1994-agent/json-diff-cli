"""Output formatting for JSON diff results.

This module provides various output formats:
- Terminal output with colors
- JSON Patch (RFC 6902) format
- Summary statistics
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from .differ import DiffEntry, DiffResult, DiffType


class OutputFormat(Enum):
    """Available output formats."""
    TERMINAL = "terminal"
    JSON_PATCH = "json-patch"
    SUMMARY = "summary"


@dataclass
class JsonPatchOperation:
    """Single JSON Patch operation."""
    op: str  # "add", "remove", "replace"
    path: str
    value: Any = None


class Formatter:
    """Formatter for DiffResult objects."""

    def __init__(self, result: DiffResult):
        """
        Initialize formatter with a diff result.

        Args:
            result: The DiffResult to format
        """
        self.result = result

    def to_terminal(self, use_color: bool = True) -> str:
        """
        Format diff result for terminal output.

        Args:
            use_color: Whether to include ANSI color codes

        Returns:
            Formatted string for terminal display
        """
        if not self.result.has_differences:
            return self._format_no_diff(use_color)

        lines = []

        # Header
        lines.append(self._format_header(use_color))

        # Additions
        if self.result.additions:
            lines.append(self._format_section("ADDITIONS", self.result.additions, "green", "+", use_color))

        # Deletions
        if self.result.deletions:
            lines.append(self._format_section("DELETIONS", self.result.deletions, "red", "-", use_color))

        # Modifications
        if self.result.modifications:
            lines.append(self._format_section("MODIFICATIONS", self.result.modifications, "yellow", "~", use_color))

        # Type changes
        if self.result.type_changes:
            lines.append(self._format_section("TYPE CHANGES", self.result.type_changes, "magenta", "!", use_color))

        # Summary
        lines.append(self._format_summary_line(use_color))

        return "\n".join(lines)

    def to_json_patch(self) -> str:
        """
        Convert diff result to JSON Patch (RFC 6902) format.

        JSON Patch operations:
        - "add" for additions
        - "remove" for deletions
        - "replace" for modifications

        Returns:
            JSON string representing the patch operations
        """
        operations = []

        # Process deletions (remove operations)
        for entry in self.result.deletions:
            operations.append(JsonPatchOperation(
                op="remove",
                path=self._diff_path_to_json_pointer(entry.path)
            ))

        # Process additions (add operations)
        for entry in self.result.additions:
            operations.append(JsonPatchOperation(
                op="add",
                path=self._diff_path_to_json_pointer(entry.path),
                value=entry.new_value
            ))

        # Process modifications (replace operations)
        for entry in self.result.modifications:
            operations.append(JsonPatchOperation(
                op="replace",
                path=self._diff_path_to_json_pointer(entry.path),
                value=entry.new_value
            ))

        # Process type changes (replace operations)
        for entry in self.result.type_changes:
            operations.append(JsonPatchOperation(
                op="replace",
                path=self._diff_path_to_json_pointer(entry.path),
                value=entry.new_value
            ))

        # Convert to list of dicts for JSON serialization
        patch_list = []
        for op in operations:
            op_dict = {"op": op.op, "path": op.path}
            if op.value is not None:
                op_dict["value"] = op.value
            patch_list.append(op_dict)

        return json.dumps(patch_list, indent=2, ensure_ascii=False)

    def to_summary(self) -> str:
        """
        Get a summary of the differences.

        Returns:
            Human-readable summary string
        """
        if not self.result.has_differences:
            return "✓ No differences found. Files are identical."

        lines = [
            f"📊 Diff Summary",
            f"{'=' * 40}",
            f"Left:  {self.result.left_path}",
            f"Right: {self.result.right_path}",
            f"{'=' * 40}",
            ""
        ]

        # Statistics
        stats = []
        if self.result.additions:
            stats.append(f"  • {len(self.result.additions)} addition(s)")
        if self.result.deletions:
            stats.append(f"  • {len(self.result.deletions)} deletion(s)")
        if self.result.modifications:
            stats.append(f"  • {len(self.result.modifications)} modification(s)")
        if self.result.type_changes:
            stats.append(f"  • {len(self.result.type_changes)} type change(s)")

        lines.append(f"Total Changes: {self.result.total_changes}")
        lines.append("")
        lines.append("Breakdown:")
        lines.extend(stats)

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert diff result to dictionary format.

        Returns:
            Dictionary representation of the diff
        """
        return {
            "left": str(self.result.left_path),
            "right": str(self.result.right_path),
            "has_differences": self.result.has_differences,
            "total_changes": self.result.total_changes,
            "additions": [
                {"path": e.path, "value": e.new_value}
                for e in self.result.additions
            ],
            "deletions": [
                {"path": e.path, "value": e.old_value}
                for e in self.result.deletions
            ],
            "modifications": [
                {"path": e.path, "old_value": e.old_value, "new_value": e.new_value}
                for e in self.result.modifications
            ],
            "type_changes": [
                {"path": e.path, "old_value": e.old_value, "new_value": e.new_value}
                for e in self.result.type_changes
            ]
        }

    def to_json(self, indent: int = 2) -> str:
        """
        Convert diff result to JSON string.

        Args:
            indent: JSON indentation level

        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def _diff_path_to_json_pointer(self, path: str) -> str:
        """
        Convert diff path to JSON Pointer (RFC 6901) format.

        JSON Pointer uses ~0 for ~ and ~1 for /

        Args:
            path: Diff path like "key.nested.value" or "key[0]"

        Returns:
            JSON Pointer path like "/key/nested/value"
        """
        # Handle root case
        if not path or path == "root":
            return "/"

        # Convert path format to JSON Pointer format
        parts = []
        current = ""

        for char in path:
            if char == ".":
                if current:
                    parts.append(self._escape_json_pointer(current))
                    current = ""
            elif char == "[":
                if current:
                    parts.append(self._escape_json_pointer(current))
                    current = ""
            elif char == "]":
                if current:
                    parts.append(self._escape_json_pointer(current))
                    current = ""
            else:
                current += char

        if current:
            parts.append(self._escape_json_pointer(current))

        return "/" + "/".join(parts) if parts else "/"

    def _escape_json_pointer(self, part: str) -> str:
        """Escape special characters for JSON Pointer (RFC 6901)."""
        # JSON Pointer requires ~0 for ~ and ~1 for /
        part = part.replace("~", "~0")
        part = part.replace("/", "~1")
        return part

    def _format_header(self, use_color: bool) -> str:
        """Format the header section."""
        if use_color:
            return (
                f"\033[1;36m{'=' * 50}\033[0m\n"
                f"\033[1;37mJSON Diff Results\033[0m\n"
                f"\033[1;36m{'=' * 50}\033[0m\n"
                f"Left:  \033[33m{self.result.left_path}\033[0m\n"
                f"Right: \033[33m{self.result.right_path}\033[0m\n"
            )
        return (
            f"{'=' * 50}\n"
            f"JSON Diff Results\n"
            f"{'=' * 50}\n"
            f"Left:  {self.result.left_path}\n"
            f"Right: {self.result.right_path}\n"
        )

    def _format_section(self, title: str, entries: List[DiffEntry], color: str, prefix: str, use_color: bool) -> str:
        """Format a section of diff entries."""
        color_codes = {
            "green": ("\033[32m", "\033[0m"),
            "red": ("\033[31m", "\033[0m"),
            "yellow": ("\033[33m", "\033[0m"),
            "magenta": ("\033[35m", "\033[0m"),
        }

        lines = []
        start_color, end_color = color_codes.get(color, ("", ""))

        if use_color:
            lines.append(f"\n{start_color}{title} ({len(entries)})\033[0m")
            lines.append("-" * 40)
            for entry in entries:
                if entry.diff_type == DiffType.CHANGED:
                    lines.append(
                        f"  {start_color}{prefix}\033[0m \033[36m{entry.path}\033[0m\n"
                        f"      {start_color}old\033[0m: {self._format_value(entry.old_value)}\n"
                        f"      {start_color}new\033[0m: {self._format_value(entry.new_value)}"
                    )
                elif entry.diff_type == DiffType.TYPE_CHANGED:
                    lines.append(
                        f"  {start_color}{prefix}\033[0m \033[36m{entry.path}\033[0m\n"
                        f"      {start_color}type\033[0m: {type(entry.old_value).__name__} -> {type(entry.new_value).__name__}"
                    )
                else:
                    value = entry.new_value if entry.new_value is not None else entry.old_value
                    lines.append(
                        f"  {start_color}{prefix}\033[0m \033[36m{entry.path}\033[0m"
                        f" \033[37m{self._format_value(value)}\033[0m"
                    )
        else:
            lines.append(f"\n{title} ({len(entries)})")
            lines.append("-" * 40)
            for entry in entries:
                if entry.diff_type == DiffType.CHANGED:
                    lines.append(
                        f"  {prefix} {entry.path}\n"
                        f"      old: {self._format_value(entry.old_value)}\n"
                        f"      new: {self._format_value(entry.new_value)}"
                    )
                elif entry.diff_type == DiffType.TYPE_CHANGED:
                    lines.append(
                        f"  {prefix} {entry.path}\n"
                        f"      type: {type(entry.old_value).__name__} -> {type(entry.new_value).__name__}"
                    )
                else:
                    value = entry.new_value if entry.new_value is not None else entry.old_value
                    lines.append(f"  {prefix} {entry.path} {self._format_value(value)}")

        return "\n".join(lines)

    def _format_value(self, value: Any) -> str:
        """Format a value for display."""
        if value is None:
            return "null"
        if isinstance(value, str):
            return f'"{value}"'
        if isinstance(value, bool):
            return str(value)
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, (list, dict)):
            try:
                return json.dumps(value, ensure_ascii=False)
            except Exception:
                return str(value)
        return repr(value)

    def _format_no_diff(self, use_color: bool) -> str:
        """Format message when no differences found."""
        if use_color:
            return (
                f"\n\033[1;32m✓ No differences found\033[0m\n"
                f"Files are identical.\n"
            )
        return "\n✓ No differences found\nFiles are identical.\n"

    def _format_summary_line(self, use_color: bool) -> str:
        """Format the summary line at the bottom."""
        if use_color:
            return f"\n\033[1;37mTotal: \033[0m\033[1;33m{self.result.total_changes}\033[0m \033[1;37mchange(s)\033[0m"
        return f"\nTotal: {self.result.total_changes} change(s)"


def format_diff(result: DiffResult, output_format: OutputFormat = OutputFormat.TERMINAL, use_color: bool = True) -> str:
    """
    Convenience function to format a DiffResult.

    Args:
        result: The DiffResult to format
        output_format: The desired output format
        use_color: Whether to use colors (for terminal format)

    Returns:
        Formatted string
    """
    formatter = Formatter(result)

    if output_format == OutputFormat.TERMINAL:
        return formatter.to_terminal(use_color)
    elif output_format == OutputFormat.JSON_PATCH:
        return formatter.to_json_patch()
    elif output_format == OutputFormat.SUMMARY:
        return formatter.to_summary()
    else:
        return formatter.to_terminal(use_color)
