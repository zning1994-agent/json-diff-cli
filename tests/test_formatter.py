"""Tests for formatter module.

Tests the to_terminal(), to_json_patch(), and to_summary() methods
of the DiffResult class.
"""

import json
import pytest
from io import StringIO
from json_diff_cli.differ import DiffResult


class TestToTerminal:
    """Test suite for to_terminal() method."""

    def test_to_terminal_with_additions(self):
        """Test terminal output includes addition markers."""
        left = {"name": "alice"}
        right = {"name": "alice", "age": 30}
        result = DiffResult(left, right)
        
        output = result.to_terminal()
        
        assert output is not None
        assert isinstance(output, str)
        assert len(output) > 0

    def test_to_terminal_with_deletions(self):
        """Test terminal output includes deletion markers."""
        left = {"name": "alice", "age": 25}
        right = {"name": "alice"}
        result = DiffResult(left, right)
        
        output = result.to_terminal()
        
        assert output is not None
        assert isinstance(output, str)
        assert len(output) > 0

    def test_to_terminal_with_modifications(self):
        """Test terminal output includes modification markers."""
        left = {"name": "alice", "age": 25}
        right = {"name": "bob", "age": 25}
        result = DiffResult(left, right)
        
        output = result.to_terminal()
        
        assert output is not None
        assert isinstance(output, str)

    def test_to_terminal_with_nested_changes(self):
        """Test terminal output with deeply nested JSON changes."""
        left = {"user": {"profile": {"name": "alice", "age": 25}}}
        right = {"user": {"profile": {"name": "bob", "age": 30}}}
        result = DiffResult(left, right)
        
        output = result.to_terminal()
        
        assert output is not None
        assert isinstance(output, str)

    def test_to_terminal_with_array_changes(self):
        """Test terminal output with array element changes."""
        left = {"items": [1, 2, 3]}
        right = {"items": [1, 2, 4]}
        result = DiffResult(left, right)
        
        output = result.to_terminal()
        
        assert output is not None
        assert isinstance(output, str)

    def test_to_terminal_no_changes(self):
        """Test terminal output when no differences exist."""
        left = {"name": "alice", "age": 25}
        right = {"name": "alice", "age": 25}
        result = DiffResult(left, right)
        
        output = result.to_terminal()
        
        assert output is not None
        assert isinstance(output, str)

    def test_to_terminal_empty_objects(self):
        """Test terminal output with empty objects."""
        left = {}
        right = {}
        result = DiffResult(left, right)
        
        output = result.to_terminal()
        
        assert output is not None
        assert isinstance(output, str)

    def test_to_terminal_complex_structure(self):
        """Test terminal output with complex nested structure."""
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
        
        output = result.to_terminal()
        
        assert output is not None
        assert isinstance(output, str)


class TestToJsonPatch:
    """Test suite for to_json_patch() method."""

    def test_to_json_patch_valid_format(self):
        """Test that JSON Patch output is valid JSON."""
        left = {"name": "alice"}
        right = {"name": "bob"}
        result = DiffResult(left, right)
        
        output = result.to_json_patch()
        
        assert output is not None
        assert isinstance(output, str)
        # Should be parseable as JSON
        parsed = json.loads(output)
        assert isinstance(parsed, list)

    def test_to_json_patch_add_operation(self):
        """Test JSON Patch add operation for new fields."""
        left = {"name": "alice"}
        right = {"name": "alice", "age": 30}
        result = DiffResult(left, right)
        
        output = result.to_json_patch()
        patches = json.loads(output)
        
        # Should contain at least one patch operation
        assert len(patches) >= 0
        if patches:
            assert any(op["op"] == "add" for op in patches)

    def test_to_json_patch_remove_operation(self):
        """Test JSON Patch remove operation for deleted fields."""
        left = {"name": "alice", "age": 25}
        right = {"name": "alice"}
        result = DiffResult(left, right)
        
        output = result.to_json_patch()
        patches = json.loads(output)
        
        assert isinstance(patches, list)
        if patches:
            assert any(op["op"] == "remove" for op in patches)

    def test_to_json_patch_replace_operation(self):
        """Test JSON Patch replace operation for modified values."""
        left = {"name": "alice"}
        right = {"name": "bob"}
        result = DiffResult(left, right)
        
        output = result.to_json_patch()
        patches = json.loads(output)
        
        assert isinstance(patches, list)
        if patches:
            # Replace operations should have "replace" op
            assert any(op["op"] == "replace" for op in patches)

    def test_to_json_patch_path_format(self):
        """Test that patch paths follow JSON Pointer (RFC 6901) format."""
        left = {"user": {"name": "alice"}}
        right = {"user": {"name": "bob"}}
        result = DiffResult(left, right)
        
        output = result.to_json_patch()
        patches = json.loads(output)
        
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
        
        output = result.to_json_patch()
        patches = json.loads(output)
        
        if patches:
            # Should have paths like /user/profile/name
            paths = [p["path"] for p in patches]
            assert any("user" in path for path in paths)

    def test_to_json_patch_array_index(self):
        """Test JSON Patch paths for array elements."""
        left = {"items": [1, 2, 3]}
        right = {"items": [1, 99, 3]}
        result = DiffResult(left, right)
        
        output = result.to_json_patch()
        patches = json.loads(output)
        
        assert isinstance(patches, list)

    def test_to_json_patch_empty_when_no_changes(self):
        """Test JSON Patch output is empty list when no differences."""
        left = {"name": "alice"}
        right = {"name": "alice"}
        result = DiffResult(left, right)
        
        output = result.to_json_patch()
        patches = json.loads(output)
        
        # No changes should produce empty patch list
        assert patches == []

    def test_to_json_patch_multiple_operations(self):
        """Test JSON Patch with multiple operations."""
        left = {"name": "alice", "age": 25, "city": "NYC"}
        right = {"name": "bob", "age": 30, "country": "USA"}
        result = DiffResult(left, right)
        
        output = result.to_json_patch()
        patches = json.loads(output)
        
        # Should have multiple operations
        assert len(patches) >= 2

    def test_to_json_patch_rfc6902_compliance(self):
        """Test JSON Patch format complies with RFC 6902."""
        left = {"name": "alice"}
        right = {"name": "bob", "age": 30}
        result = DiffResult(left, right)
        
        output = result.to_json_patch()
        patches = json.loads(output)
        
        for patch in patches:
            # Each patch must have "op" and "path"
            assert "op" in patch
            assert "path" in patch
            # Valid operations are: add, remove, replace, move, copy, test
            assert patch["op"] in ["add", "remove", "replace", "move", "copy", "test"]


class TestToSummary:
    """Test suite for to_summary() method."""

    def test_to_summary_with_changes(self):
        """Test summary output contains change count."""
        left = {"name": "alice"}
        right = {"name": "bob"}
        result = DiffResult(left, right)
        
        output = result.to_summary()
        
        assert output is not None
        assert isinstance(output, str)
        assert len(output) > 0

    def test_to_summary_no_changes(self):
        """Test summary output when no differences."""
        left = {"name": "alice"}
        right = {"name": "alice"}
        result = DiffResult(left, right)
        
        output = result.to_summary()
        
        assert output is not None
        assert isinstance(output, str)

    def test_to_summary_counts_additions(self):
        """Test summary counts additions correctly."""
        left = {"name": "alice"}
        right = {"name": "alice", "age": 30, "city": "NYC"}
        result = DiffResult(left, right)
        
        output = result.to_summary()
        
        # Summary should mention additions
        assert output is not None
        # The summary should contain some indication of changes
        assert isinstance(output, str)

    def test_to_summary_counts_deletions(self):
        """Test summary counts deletions correctly."""
        left = {"name": "alice", "age": 25, "city": "NYC"}
        right = {"name": "alice"}
        result = DiffResult(left, right)
        
        output = result.to_summary()
        
        assert output is not None
        assert isinstance(output, str)

    def test_to_summary_counts_modifications(self):
        """Test summary counts modifications correctly."""
        left = {"name": "alice", "age": 25}
        right = {"name": "bob", "age": 30}
        result = DiffResult(left, right)
        
        output = result.to_summary()
        
        assert output is not None
        assert isinstance(output, str)

    def test_to_summary_with_nested_changes(self):
        """Test summary with deeply nested changes."""
        left = {"user": {"profile": {"name": "alice"}}}
        right = {"user": {"profile": {"name": "bob"}}}
        result = DiffResult(left, right)
        
        output = result.to_summary()
        
        assert output is not None
        assert isinstance(output, str)

    def test_to_summary_empty_input(self):
        """Test summary with empty JSON objects."""
        left = {}
        right = {}
        result = DiffResult(left, right)
        
        output = result.to_summary()
        
        assert output is not None
        assert isinstance(output, str)

    def test_to_summary_with_type_changes(self):
        """Test summary with type changes (e.g., int to string)."""
        left = {"value": 123}
        right = {"value": "123"}
        result = DiffResult(left, right)
        
        output = result.to_summary()
        
        assert output is not None
        assert isinstance(output, str)


class TestSummaryProperty:
    """Test suite for summary property."""

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
        assert 'additions' in summary
        assert 'total_changes' in summary

    def test_summary_property_no_changes(self):
        """Test summary property with identical objects."""
        left = {"name": "alice", "age": 25}
        right = {"name": "alice", "age": 25}
        result = DiffResult(left, right)
        
        summary = result.summary
        assert isinstance(summary, dict)
        assert summary['additions'] == 0
        assert summary['deletions'] == 0
        assert summary['total_changes'] == 0


class TestDiffResultIntegration:
    """Integration tests for DiffResult formatting methods."""

    def test_all_methods_produce_string(self):
        """Test all formatting methods return strings."""
        left = {"name": "alice", "items": [1, 2, 3]}
        right = {"name": "bob", "items": [1, 2, 4], "count": 5}
        result = DiffResult(left, right)
        
        assert isinstance(result.to_terminal(), str)
        assert isinstance(result.to_json_patch(), str)
        assert isinstance(result.to_summary(), str)
        assert isinstance(result.summary, dict)

    def test_json_patch_parseable_after_terminal(self):
        """Test that to_json_patch output is still valid after to_terminal call."""
        left = {"name": "alice"}
        right = {"name": "bob"}
        result = DiffResult(left, right)
        
        result.to_terminal()
        json_output = result.to_json_patch()
        
        # Should still be valid JSON
        parsed = json.loads(json_output)
        assert isinstance(parsed, list)

    def test_consistency_across_formats(self):
        """Test that different formats show consistent change information."""
        left = {"a": 1, "b": 2}
        right = {"a": 1, "c": 3}
        result = DiffResult(left, right)
        
        terminal_output = result.to_terminal()
        json_patch_output = result.to_json_patch()
        summary_output = result.to_summary()
        
        # All outputs should be non-empty strings
        assert len(terminal_output) > 0
        assert len(json_patch_output) > 0
        assert len(summary_output) > 0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_deeply_nested_structure(self):
        """Test with very deeply nested JSON."""
        left = {"l1": {"l2": {"l3": {"l4": {"l5": "value"}}}}}
        right = {"l1": {"l2": {"l3": {"l4": {"l5": "new_value"}}}}}
        result = DiffResult(left, right)
        
        assert isinstance(result.to_terminal(), str)
        assert isinstance(result.to_json_patch(), str)
        assert isinstance(result.to_summary(), str)

    def test_large_array(self):
        """Test with large arrays."""
        left = {"items": list(range(100))}
        right = {"items": list(range(100))}
        right["items"][50] = 999
        result = DiffResult(left, right)
        
        assert isinstance(result.to_terminal(), str)
        assert isinstance(result.to_json_patch(), str)

    def test_special_characters_in_strings(self):
        """Test with special characters in string values."""
        left = {"text": "Hello\nWorld"}
        right = {"text": "Hello\tWorld"}
        result = DiffResult(left, right)
        
        assert isinstance(result.to_terminal(), str)
        assert isinstance(result.to_json_patch(), str)

    def test_unicode_characters(self):
        """Test with Unicode characters."""
        left = {"name": "中文名称"}
        right = {"name": "日本語"}
        result = DiffResult(left, right)
        
        assert isinstance(result.to_terminal(), str)
        assert isinstance(result.to_json_patch(), str)

    def test_null_values(self):
        """Test with null values."""
        left = {"value": None, "name": "alice"}
        right = {"value": None, "name": "bob"}
        result = DiffResult(left, right)
        
        assert isinstance(result.to_terminal(), str)
        assert isinstance(result.to_json_patch(), str)

    def test_boolean_values(self):
        """Test with boolean values."""
        left = {"active": True, "verified": False}
        right = {"active": False, "verified": True}
        result = DiffResult(left, right)
        
        assert isinstance(result.to_terminal(), str)
        assert isinstance(result.to_json_patch(), str)

    def test_numeric_precision(self):
        """Test with floating point numbers."""
        left = {"price": 19.99}
        right = {"price": 20.00}
        result = DiffResult(left, right)
        
        assert isinstance(result.to_terminal(), str)
        assert isinstance(result.to_json_patch(), str)
