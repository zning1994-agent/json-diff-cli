"""Tests for the renderer module.

Tests the render_diff(), render_diff_table(), render_tree(), format_path(),
and format_value() functions.
"""

import pytest
from io import StringIO
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from json_diff_cli.differ import DiffResult
from json_diff_cli.renderer import (
    render_diff,
    render_diff_table,
    render_tree,
    format_path,
    format_value,
)


class TestFormatPath:
    """Tests for format_path() function."""

    def test_format_path_simple(self):
        """Test formatting simple key path."""
        result = format_path("name")
        assert result == "name"

    def test_format_path_with_root(self):
        """Test formatting path with root prefix."""
        result = format_path("root['name']")
        assert result == "name"

    def test_format_path_nested(self):
        """Test formatting nested path."""
        result = format_path("root['user']['name']")
        assert result == "user.name"

    def test_format_path_array_index(self):
        """Test formatting path with array index."""
        result = format_path("root['items'][0]")
        assert result == "items.0"

    def test_format_path_deeply_nested(self):
        """Test formatting deeply nested path."""
        result = format_path("root['a']['b']['c']['d']")
        assert result == "a.b.c.d"

    def test_format_path_empty(self):
        """Test formatting empty/root path."""
        result = format_path("root")
        assert result == "/"

    def test_format_path_special_chars(self):
        """Test formatting path with special characters."""
        result = format_path("root['key.with.dots']")
        assert result == "key.with.dots"


class TestFormatValue:
    """Tests for format_value() function."""

    def test_format_value_none(self):
        """Test formatting None value."""
        result = format_value(None)
        assert result == "null"

    def test_format_value_true(self):
        """Test formatting True value."""
        result = format_value(True)
        assert result == "true"

    def test_format_value_false(self):
        """Test formatting False value."""
        result = format_value(False)
        assert result == "false"

    def test_format_value_integer(self):
        """Test formatting integer value."""
        result = format_value(42)
        assert result == "42"

    def test_format_value_float(self):
        """Test formatting float value."""
        result = format_value(3.14)
        assert result == "3.14"

    def test_format_value_string(self):
        """Test formatting string value."""
        result = format_value("hello")
        assert result == '"hello"'

    def test_format_value_string_long(self):
        """Test formatting long string gets truncated."""
        long_string = "a" * 100
        result = format_value(long_string)
        assert "..." in result
        assert len(result) < len(f'"{long_string}"')

    def test_format_value_list(self):
        """Test formatting list value."""
        result = format_value([1, 2, 3])
        assert "[1, 2, 3]" in result

    def test_format_value_dict(self):
        """Test formatting dict value."""
        result = format_value({"key": "value"})
        assert "key" in result
        assert "value" in result


class TestRenderDiff:
    """Tests for render_diff() function."""

    def test_render_diff_no_changes(self):
        """Test render_diff with no differences."""
        left = {"name": "alice"}
        right = {"name": "alice"}
        result = DiffResult(left, right)

        output = render_diff(result)

        assert output is not None
        assert isinstance(output, str)
        assert "No differences" in output or "no differences" in output.lower()

    def test_render_diff_with_additions(self):
        """Test render_diff includes additions."""
        left = {"name": "alice"}
        right = {"name": "alice", "age": 30}
        result = DiffResult(left, right)

        output = render_diff(result)

        assert output is not None
        assert "age" in output
        assert "30" in output

    def test_render_diff_with_deletions(self):
        """Test render_diff includes deletions."""
        left = {"name": "alice", "age": 25}
        right = {"name": "alice"}
        result = DiffResult(left, right)

        output = render_diff(result)

        assert output is not None
        assert "age" in output

    def test_render_diff_with_modifications(self):
        """Test render_diff includes modifications."""
        left = {"name": "alice", "age": 25}
        right = {"name": "bob", "age": 25}
        result = DiffResult(left, right)

        output = render_diff(result)

        assert output is not None
        assert "name" in output
        assert "-" in output or "+" in output

    def test_render_diff_nested_path(self):
        """Test render_diff with nested paths."""
        left = {"user": {"name": "alice"}}
        right = {"user": {"name": "bob"}}
        result = DiffResult(left, right)

        output = render_diff(result)

        assert output is not None
        assert "user" in output or "name" in output

    def test_render_diff_returns_string(self):
        """Test render_diff returns string type."""
        left = {"a": 1}
        right = {"a": 2}
        result = DiffResult(left, right)

        output = render_diff(result)

        assert isinstance(output, str)


class TestRenderDiffTable:
    """Tests for render_diff_table() function."""

    def test_render_diff_table_no_changes(self):
        """Test render_diff_table with no differences."""
        left = {"name": "alice"}
        right = {"name": "alice"}
        result = DiffResult(left, right)

        table = render_diff_table(result)

        assert table is not None
        assert isinstance(table, Table)

    def test_render_diff_table_with_changes(self):
        """Test render_diff_table includes changes."""
        left = {"name": "alice"}
        right = {"name": "bob"}
        result = DiffResult(left, right)

        table = render_diff_table(result)

        assert table is not None
        assert isinstance(table, Table)
        assert len(table.columns) == 3  # Type, Path, Value

    def test_render_diff_table_returns_table(self):
        """Test render_diff_table returns Table instance."""
        left = {"a": 1}
        right = {"a": 2, "b": 3}
        result = DiffResult(left, right)

        table = render_diff_table(result)

        assert isinstance(table, Table)


class TestRenderTree:
    """Tests for render_tree() function."""

    def test_render_tree_simple_dict(self):
        """Test render_tree with simple dict."""
        data = {"name": "alice", "age": 30}

        tree = render_tree(data)

        assert tree is not None
        assert isinstance(tree, Tree)

    def test_render_tree_nested(self):
        """Test render_tree with nested dict."""
        data = {"user": {"name": "alice", "profile": {"age": 30}}}

        tree = render_tree(data)

        assert tree is not None
        assert isinstance(tree, Tree)

    def test_render_tree_with_list(self):
        """Test render_tree with list data."""
        data = {"items": [1, 2, 3]}

        tree = render_tree(data)

        assert tree is not None
        assert isinstance(tree, Tree)

    def test_render_tree_with_title(self):
        """Test render_tree with custom title."""
        data = {"key": "value"}

        tree = render_tree(data, title="Custom Title")

        assert tree is not None
        assert isinstance(tree, Tree)

    def test_render_tree_empty_dict(self):
        """Test render_tree with empty dict."""
        tree = render_tree({})

        assert tree is not None
        assert isinstance(tree, Tree)

    def test_render_tree_returns_tree(self):
        """Test render_tree returns Tree instance."""
        data = {"a": 1}

        tree = render_tree(data)

        assert isinstance(tree, Tree)


class TestRenderDiffIntegration:
    """Integration tests for renderer with real DiffResult."""

    def test_render_complex_diff(self):
        """Test rendering complex diff with all change types."""
        left = {
            "name": "alice",
            "age": 25,
            "tags": ["python", "cli"],
            "config": {"debug": True}
        }
        right = {
            "name": "bob",
            "city": "NYC",
            "tags": ["python", "rust"],
            "config": {"debug": False, "verbose": True}
        }
        result = DiffResult(left, right)

        output = render_diff(result)

        assert isinstance(output, str)
        assert len(output) > 0

    def test_render_array_changes(self):
        """Test rendering array element changes."""
        left = {"items": [1, 2, 3]}
        right = {"items": [1, 99, 3]}
        result = DiffResult(left, right)

        output = render_diff(result)

        assert isinstance(output, str)

    def test_render_unicode_content(self):
        """Test rendering unicode content."""
        left = {"name": "张三"}
        right = {"name": "李四"}
        result = DiffResult(left, right)

        output = render_diff(result)

        assert isinstance(output, str)
        assert len(output) > 0

    def test_render_special_characters(self):
        """Test rendering special characters in values."""
        left = {"text": "line1\nline2"}
        right = {"text": "line1\tline2"}
        result = DiffResult(left, right)

        output = render_diff(result)

        assert isinstance(output, str)

    def test_render_null_values(self):
        """Test rendering null values."""
        left = {"value": None}
        right = {"value": "not null"}
        result = DiffResult(left, right)

        output = render_diff(result)

        assert isinstance(output, str)
        assert "null" in output.lower() or "None" in output


class TestRendererEdgeCases:
    """Tests for edge cases."""

    def test_render_empty_diff_result(self):
        """Test rendering empty DiffResult."""
        left = {}
        right = {}
        result = DiffResult(left, right)

        output = render_diff(result)

        assert isinstance(output, str)
        assert "No differences" in output or "no differences" in output.lower()

    def test_render_large_numbers(self):
        """Test rendering large numbers."""
        left = {"big": 10**20}
        right = {"big": 10**21}
        result = DiffResult(left, right)

        output = render_diff(result)

        assert isinstance(output, str)

    def test_render_boolean_changes(self):
        """Test rendering boolean value changes."""
        left = {"active": True}
        right = {"active": False}
        result = DiffResult(left, right)

        output = render_diff(result)

        assert isinstance(output, str)
        assert "true" in output.lower() or "false" in output.lower()

    def test_render_mixed_types(self):
        """Test rendering mixed type values."""
        left = {"str": "text", "num": 42, "bool": True, "null": None}
        right = {"str": "changed", "num": 43, "bool": False, "null": "value"}
        result = DiffResult(left, right)

        output = render_diff(result)

        assert isinstance(output, str)
        assert len(output) > 0

    def test_format_path_edge_cases(self):
        """Test format_path with various edge cases."""
        # Various path formats
        assert format_path("") == ""
        assert format_path("root") == "/"
        assert format_path("root[]") == "[]"
        assert format_path("root[0]") == "[0]"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
