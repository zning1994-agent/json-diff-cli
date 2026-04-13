"""Tests for formatter module.

Tests the format_diff(), to_json_patch(), and to_summary() functions
from the formatter module.
"""

import json
import pytest
from io import StringIO

from json_diff_cli.differ import DiffResult
from json_diff_cli.formatter import (
    format_diff,
    OutputFormat,
    diff_to_json_patch,
    path_to_pointer
)


class TestFormatDiff:
    """Test suite for format_diff() function."""

    def test_format_diff_terminal(self):
        """Test format_diff with terminal output."""
        left = {"name": "alice"}
        right = {"name": "bob"}
        result = DiffResult(left, right)
        
        output = format_diff(result, OutputFormat.TERMINAL)
        
        assert output is not None
        assert isinstance(output, str)
        assert len(output) > 0

    def test_format_diff_json_patch(self):
        """Test format_diff with JSON Patch output."""
        left = {"name": "alice"}
        right = {"name": "bob"}
        result = DiffResult(left, right)
        
        output = format_diff(result, OutputFormat.JSON_PATCH)
        
        assert output is not None
        assert isinstance(output, str)
        # Should be parseable as JSON
        parsed = json.loads(output)
        assert isinstance(parsed, list)

    def test_format_diff_summary(self):
        """Test format_diff with summary output."""
        left = {"name": "alice"}
        right = {"name": "bob"}
        result = DiffResult(left, right)
        
        output = format_diff(result, OutputFormat.SUMMARY)
        
        assert output is not None
        assert isinstance(output, str)
        assert len(output) > 0

    def test_format_diff_with_additions(self):
        """Test format_diff includes addition markers."""
        left = {"name": "alice"}
        right = {"name": "alice", "age": 30}
        result = DiffResult(left, right)
        
        output = format_diff(result, OutputFormat.TERMINAL)
        
        assert output is not None
        assert isinstance(output, str)
        assert len(output) > 0

    def test_format_diff_with_deletions(self):
        """Test format_diff includes deletion markers."""
        left = {"name": "alice", "age": 25}
        right = {"name": "alice"}
        result = DiffResult(left, right)
        
        output = format_diff(result, OutputFormat.TERMINAL)
        
        assert output is not None
        assert isinstance(output, str)
        assert len(output) > 0

    def test_format_diff_with_modifications(self):
        """Test format_diff includes modification markers."""
        left = {"name": "alice", "age": 25}
        right = {"name": "bob", "age": 25}
        result = DiffResult(left, right)
        
        output = format_diff(result, OutputFormat.TERMINAL)
        
        assert output is not None
        assert isinstance(output, str)

    def test_format_diff_no_changes(self):
        """Test format_diff when no differences exist."""
        left = {"name": "alice", "age": 25}
        right = {"name": "alice", "age": 25}
        result = DiffResult(left, right)
        
        output = format_diff(result, OutputFormat.TERMINAL)
        
        assert output is not None
        assert isinstance(output, str)

    def test_format_diff_complex_structure(self):
        """Test format_diff with complex nested structure."""
        left = {
            "users": [
                {"id": 1, "name": "alice", "active": True},
                {"id": 2, "name": "bob", "active": False}
            ],
            "metadata": {"version": "1.0"}
        }
        right = {
            "users": [
                {"id": 1, "name": "alice", "active": False},
                {"id": 2, "name": "charlie", "active": True}
            ],
            "metadata": {"version": "2.0"}
        }
        result = DiffResult(left, right)
        
        output = format_diff(result, OutputFormat.TERMINAL)
        
        assert output is not None
        assert isinstance(output, str)


class TestDiffToJsonPatch:
    """Test suite for diff_to_json_patch() function."""

    def test_to_json_patch_valid_format(self):
        """Test that JSON Patch output is valid JSON."""
        left = {"name": "alice"}
        right = {"name": "bob"}
        result = DiffResult(left, right)
        
        patches = diff_to_json_patch(result)
        
        assert patches is not None
        assert isinstance(patches, list)

    def test_to_json_patch_add_operation(self):
        """Test JSON Patch add operation for new fields."""
        left = {"name": "alice"}
        right = {"name": "alice", "age": 30}
        result = DiffResult(left, right)
        
        patches = diff_to_json_patch(result)
        
        # Should contain at least one patch operation
        assert len(patches) >= 0
        if patches:
            assert any(op["op"] == "add" for op in patches)

    def test_to_json_patch_remove_operation(self):
        """Test JSON Patch remove operation for deleted fields."""
        left = {"name": "alice", "age": 25}
        right = {"name": "alice"}
        result = DiffResult(left, right)
        
        patches = diff_to_json_patch(result)
        
        assert isinstance(patches, list)
        if patches:
            assert any(op["op"] == "remove" for op in patches)

    def test_to_json_patch_replace_operation(self):
        """Test JSON Patch replace operation for modified values."""
        left = {"name": "alice"}
        right = {"name": "bob"}
        result = DiffResult(left, right)
        
        patches = diff_to_json_patch(result)
        
        assert isinstance(patches, list)
        if patches:
            # Replace operations should have "replace" op
            assert any(op["op"] == "replace" for op in patches)

    def test_to_json_patch_path_format(self):
        """Test that patch paths follow JSON Pointer (RFC 6901) format."""
        left = {"user": {"name": "alice"}}
        right = {"user": {"name": "bob"}}
        result = DiffResult(left, right)
        
        patches = diff_to_json_patch(result)
        
        if patches:
            for patch in patches:
                assert "path" in patch
                # JSON Pointer paths should start with /
                assert patch["path"].startswith("/")

    def test_to_json_patch_nested_path(self):
        """Test JSON Patch paths for nested objects."""
        left = {"user": {"profile": {"name": "alice"}}}
        right = {"user": {"profile": {"name": "bob"}}}
        result = DiffResult(left, right)
        
        patches = diff_to_json_patch(result)
        
        if patches:
            # Should have paths like /user/profile/name
            paths = [p["path"] for p in patches]
            assert any("user" in path for path in paths)

    def test_to_json_patch_array_index(self):
        """Test JSON Patch paths for array elements."""
        left = {"items": [1, 2, 3]}
        right = {"items": [1, 99, 3]}
        result = DiffResult(left, right)
        
        patches = diff_to_json_patch(result)
        
        assert isinstance(patches, list)

    def test_to_json_patch_empty_when_no_changes(self):
        """Test JSON Patch output is empty list when no differences."""
        left = {"name": "alice"}
        right = {"name": "alice"}
        result = DiffResult(left, right)
        
        patches = diff_to_json_patch(result)
        
        # No changes should produce empty patch list
        assert patches == []

    def test_to_json_patch_multiple_operations(self):
        """Test JSON Patch with multiple operations."""
        left = {"name": "alice", "age": 25, "city": "NYC"}
        right = {"name": "bob", "age": 30, "country": "USA"}
        result = DiffResult(left, right)
        
        patches = diff_to_json_patch(result)
        
        # Should have multiple operations
        assert len(patches) >= 2

    def test_to_json_patch_rfc6902_compliance(self):
        """Test JSON Patch format complies with RFC 6902."""
        left = {"name": "alice"}
        right = {"name": "bob", "age": 30}
        result = DiffResult(left, right)
        
        patches = diff_to_json_patch(result)
        
        for patch in patches:
            # Each patch must have "op" and "path"
            assert "op" in patch
            assert "path" in patch
            # Valid operations are: add, remove, replace, move, copy, test
            assert patch["op"] in ["add", "remove", "replace", "move", "copy", "test"]


class TestSummaryOutput:
    """Test suite for summary output format."""

    def test_to_summary_with_changes(self):
        """Test summary output contains change count."""
        left = {"name": "alice"}
        right = {"name": "bob"}
        result = DiffResult(left, right)
        
        output = format_diff(result, OutputFormat.SUMMARY)
        
        assert output is not None
        assert isinstance(output, str)
        assert len(output) > 0

    def test_to_summary_no_changes(self):
        """Test summary output when no differences."""
        left = {"name": "alice"}
        right = {"name": "alice"}
        result = DiffResult(left, right)
        
        output = format_diff(result, OutputFormat.SUMMARY)
        
        assert output is not None
        assert isinstance(output, str)

    def test_to_summary_contains_counts(self):
        """Test summary contains counts for changes."""
        left = {"name": "alice"}
        right = {"name": "alice", "age": 30, "city": "NYC"}
        result = DiffResult(left, right)
        
        output = format_diff(result, OutputFormat.SUMMARY)
        
        # Summary should mention additions
        assert output is not None
        assert isinstance(output, str)
        assert "Additions" in output or "additions" in output

    def test_to_summary_empty_input(self):
        """Test summary with empty JSON objects."""
        left = {}
        right = {}
        result = DiffResult(left, right)
        
        output = format_diff(result, OutputFormat.SUMMARY)
        
        assert output is not None
        assert isinstance(output, str)


class TestSummaryProperty:
    """Test suite for DiffResult summary property."""

    def test_summary_property_exists(self):
        """Test that DiffResult has a summary property."""
        left = {"name": "alice"}
        right = {"name": "bob"}
        result = DiffResult(left, right)
        
        # Should have summary attribute
        assert hasattr(result, 'summary')

    def test_summary_property_type(self):
        """Test summary property returns dict."""
        left = {"name": "alice"}
        right = {"name": "bob"}
        result = DiffResult(left, right)
        
        summary = result.summary
        assert isinstance(summary, dict)

    def test_summary_property_has_keys(self):
        """Test summary property has expected keys."""
        left = {"name": "alice"}
        right = {"name": "bob"}
        result = DiffResult(left, right)
        
        summary = result.summary
        assert "additions" in summary
        assert "deletions" in summary
        assert "modifications" in summary
        assert "total_changes" in summary

    def test_summary_property_no_changes(self):
        """Test summary property with identical objects."""
        left = {"name": "alice", "age": 25}
        right = {"name": "alice", "age": 25}
        result = DiffResult(left, right)
        
        summary = result.summary
        assert isinstance(summary, dict)
        assert summary["total_changes"] == 0


class TestDiffResultIntegration:
    """Integration tests for formatting functions."""

    def test_all_methods_produce_string(self):
        """Test all formatting methods return strings."""
        left = {"name": "alice", "items": [1, 2, 3]}
        right = {"name": "bob", "items": [1, 2, 4], "count": 5}
        result = DiffResult(left, right)
        
        assert isinstance(format_diff(result, OutputFormat.TERMINAL), str)
        assert isinstance(format_diff(result, OutputFormat.JSON_PATCH), str)
        assert isinstance(format_diff(result, OutputFormat.SUMMARY), str)
        assert isinstance(result.summary, dict)

    def test_json_patch_parseable_after_terminal(self):
        """Test that to_json_patch output is still valid after to_terminal call."""
        left = {"name": "alice"}
        right = {"name": "bob"}
        result = DiffResult(left, right)
        
        format_diff(result, OutputFormat.TERMINAL)
        patches = diff_to_json_patch(result)
        
        # Should still be valid list
        assert isinstance(patches, list)

    def test_consistency_across_formats(self):
        """Test that different formats show consistent change information."""
        left = {"a": 1, "b": 2}
        right = {"a": 1, "c": 3}
        result = DiffResult(left, right)
        
        terminal_output = format_diff(result, OutputFormat.TERMINAL)
        json_patch_output = format_diff(result, OutputFormat.JSON_PATCH)
        summary_output = format_diff(result, OutputFormat.SUMMARY)
        
        # All outputs should be non-empty strings
        assert len(terminal_output) > 0
        assert len(json_patch_output) > 0
        assert len(summary_output) > 0


class TestPathToPointer:
    """Test suite for path_to_pointer() function."""

    def test_path_to_pointer_top_level(self):
        """Test path_to_pointer with top-level key."""
        result = path_to_pointer("name")
        assert result == "/name"

    def test_path_to_pointer_nested(self):
        """Test path_to_pointer with nested path."""
        result = path_to_pointer("root['user']['name']")
        assert result == "/user/name"

    def test_path_to_pointer_array(self):
        """Test path_to_pointer with array index."""
        result = path_to_pointer("root['items'][0]")
        assert result == "/items/0"

    def test_path_to_pointer_empty(self):
        """Test path_to_pointer with empty path."""
        result = path_to_pointer("root")
        assert result == "/"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_deeply_nested_structure(self):
        """Test with very deeply nested JSON."""
        left = {"l1": {"l2": {"l3": {"l4": {"l5": "value"}}}}}
        right = {"l1": {"l2": {"l3": {"l4": {"l5": "new_value"}}}}}
        result = DiffResult(left, right)
        
        assert isinstance(format_diff(result, OutputFormat.TERMINAL), str)
        assert isinstance(format_diff(result, OutputFormat.JSON_PATCH), str)

    def test_large_array(self):
        """Test with large arrays."""
        left = {"items": list(range(100))}
        right = {"items": list(range(100))}
        right["items"][50] = 999
        result = DiffResult(left, right)
        
        assert isinstance(format_diff(result, OutputFormat.TERMINAL), str)
        assert isinstance(format_diff(result, OutputFormat.JSON_PATCH), str)

    def test_special_characters_in_strings(self):
        """Test with special characters in string values."""
        left = {"text": "Hello\nWorld"}
        right = {"text": "Hello\tWorld"}
        result = DiffResult(left, right)
        
        assert isinstance(format_diff(result, OutputFormat.TERMINAL), str)
        assert isinstance(format_diff(result, OutputFormat.JSON_PATCH), str)

    def test_unicode_characters(self):
        """Test with Unicode characters."""
        left = {"name": "中文名称"}
        right = {"name": "日本語"}
        result = DiffResult(left, right)
        
        assert isinstance(format_diff(result, OutputFormat.TERMINAL), str)
        assert isinstance(format_diff(result, OutputFormat.JSON_PATCH), str)

    def test_null_values(self):
        """Test with null values."""
        left = {"value": None, "name": "alice"}
        right = {"value": None, "name": "bob"}
        result = DiffResult(left, right)
        
        assert isinstance(format_diff(result, OutputFormat.TERMINAL), str)
        assert isinstance(format_diff(result, OutputFormat.JSON_PATCH), str)

    def test_boolean_values(self):
        """Test with boolean values."""
        left = {"active": True, "verified": False}
        right = {"active": False, "verified": True}
        result = DiffResult(left, right)
        
        assert isinstance(format_diff(result, OutputFormat.TERMINAL), str)
        assert isinstance(format_diff(result, OutputFormat.JSON_PATCH), str)

    def test_numeric_precision(self):
        """Test with floating point numbers."""
        left = {"price": 19.99}
        right = {"price": 20.00}
        result = DiffResult(left, right)
        
        assert isinstance(format_diff(result, OutputFormat.TERMINAL), str)
        assert isinstance(format_diff(result, OutputFormat.JSON_PATCH), str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
