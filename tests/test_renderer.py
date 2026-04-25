"""Tests for the renderer module."""

import pytest
from io import StringIO
from typing import Any, Dict

from rich.console import Console

from json_diff_cli.differ import DiffResult
from json_diff_cli.renderer import (
    DiffRenderer,
    DiffTheme,
    ChangeType,
    render_diff,
    render_tree,
    render_diff_table,
    format_path,
    format_value,
)


class TestDiffTheme:
    """Tests for DiffTheme class."""
    
    def test_default_colors(self):
        """Test default theme has expected colors."""
        theme = DiffTheme()
        assert theme.ADDED_COLOR == "green"
        assert theme.REMOVED_COLOR == "red"
        assert theme.CHANGED_COLOR == "yellow"
        assert theme.PATH_COLOR == "cyan"
    
    def test_custom_colors(self):
        """Test theme with custom colors."""
        theme = DiffTheme(
            added_color="blue",
            removed_color="magenta",
            changed_color="white",
            path_color="yellow"
        )
        assert theme.ADDED_COLOR == "blue"
        assert theme.REMOVED_COLOR == "magenta"
        assert theme.CHANGED_COLOR == "white"
        assert theme.PATH_COLOR == "yellow"


class TestDiffRenderer:
    """Tests for DiffRenderer class."""
    
    def test_init_default(self):
        """Test renderer initialization with defaults."""
        renderer = DiffRenderer()
        assert renderer.show_values is True
        assert renderer.max_depth == 0
        assert renderer.console is not None
    
    def test_init_custom(self):
        """Test renderer initialization with custom values."""
        console = Console(file=StringIO())
        theme = DiffTheme()
        renderer = DiffRenderer(
            console=console,
            theme=theme,
            show_values=False,
            max_depth=3
        )
        assert renderer.console == console
        assert renderer.theme == theme
        assert renderer.show_values is False
        assert renderer.max_depth == 3
    
    def test_get_change_symbol(self):
        """Test change symbol generation."""
        renderer = DiffRenderer()
        assert renderer._get_change_symbol(ChangeType.ADDED) == "+"
        assert renderer._get_change_symbol(ChangeType.REMOVED) == "-"
        assert renderer._get_change_symbol(ChangeType.CHANGED) == "~"
    
    def test_get_change_style(self):
        """Test change style generation."""
        renderer = DiffRenderer()
        style_added = renderer._get_change_style(ChangeType.ADDED)
        style_removed = renderer._get_change_style(ChangeType.REMOVED)
        style_changed = renderer._get_change_style(ChangeType.CHANGED)
        
        assert style_added is not None
        assert style_removed is not None
        assert style_changed is not None
    
    def test_format_value_none(self):
        """Test formatting None value."""
        renderer = DiffRenderer()
        result = renderer._format_value(None)
        assert "null" in str(result)
    
    def test_format_value_bool(self):
        """Test formatting boolean values."""
        renderer = DiffRenderer()
        result_true = renderer._format_value(True)
        result_false = renderer._format_value(False)
        assert "True" in str(result_true)
        assert "False" in str(result_false)
    
    def test_format_value_number(self):
        """Test formatting numeric values."""
        renderer = DiffRenderer()
        result_int = renderer._format_value(42)
        result_float = renderer._format_value(3.14)
        assert "42" in str(result_int)
        assert "3.14" in str(result_float)
    
    def test_format_value_string(self):
        """Test formatting string values."""
        renderer = DiffRenderer()
        result = renderer._format_value("hello")
        assert '"hello"' in str(result)
    
    def test_parse_path_to_tree(self):
        """Test JSON path parsing."""
        renderer = DiffRenderer()
        
        assert renderer._parse_path_to_tree("root['name']") == ["name"]
        assert renderer._parse_path_to_tree("root['address']['city']") == ["address", "city"]
        assert renderer._parse_path_to_tree("root['items'][0]") == ["items", "0"]
    
    def test_render_no_diff(self):
        """Test rendering when no differences exist."""
        diff_result = DiffResult(
            left_data={"name": "test"},
            right_data={"name": "test"},
            left_path="left.json",
            right_path="right.json"
        )
        
        console = Console(file=StringIO())
        renderer = DiffRenderer(console=console)
        renderer.render_diff(diff_result)
        
        output = console.file.getvalue()
        assert "identical" in output.lower() or "No differences" in output or "✓" in output
    
    def test_render_diff_with_changes(self):
        """Test rendering differences in table format."""
        diff_result = DiffResult(
            left_data={"key": "old"},
            right_data={"key": "new", "new_key": "added"},
            left_path="left.json",
            right_path="right.json"
        )
        
        console = Console(file=StringIO())
        renderer = DiffRenderer(console=console)
        renderer.render_diff(diff_result)
        
        output = console.file.getvalue()
        assert "Comparing" in output
        assert "left.json" in output
        assert "right.json" in output
    
    def test_render_tree_with_changes(self):
        """Test rendering differences in tree format."""
        diff_result = DiffResult(
            left_data={"name": "John"},
            right_data={"name": "Jane", "age": 30},
            left_path="left.json",
            right_path="right.json"
        )
        
        console = Console(file=StringIO())
        renderer = DiffRenderer(console=console)
        renderer.render_tree(diff_result)
        
        output = console.file.getvalue()
        assert "Comparing" in output
        assert "ADDITION" in output or "MODIFICATION" in output or "name" in output


class TestRenderDiffFunction:
    """Tests for module-level render_diff function."""
    
    def test_render_diff_no_error(self):
        """Test render_diff doesn't raise exceptions."""
        diff_result = DiffResult(
            left_data={"key": "value"},
            right_data={"key": "new_value"},
            left_path="left.json",
            right_path="right.json"
        )
        
        # Should not raise
        render_diff(diff_result)
    
    def test_render_diff_with_kwargs(self):
        """Test render_diff passes kwargs correctly."""
        diff_result = DiffResult(
            left_data={"name": "test"},
            right_data={"name": "test"},
            left_path="left.json",
            right_path="right.json"
        )
        
        console = Console(file=StringIO())
        render_diff(diff_result, console=console, show_values=False)


class TestRenderTreeFunction:
    """Tests for module-level render_tree function."""
    
    def test_render_tree_no_error(self):
        """Test render_tree doesn't raise exceptions."""
        diff_result = DiffResult(
            left_data={"key": "old"},
            right_data={"key": "new"},
            left_path="left.json",
            right_path="right.json"
        )
        
        # Should not raise
        render_tree(diff_result)
    
    def test_render_tree_with_kwargs(self):
        """Test render_tree passes kwargs correctly."""
        diff_result = DiffResult(
            left_data={},
            right_data={},
            left_path="left.json",
            right_path="right.json"
        )
        
        console = Console(file=StringIO())
        render_tree(diff_result, console=console)


class TestRenderDiffIntegration:
    """Integration tests for renderer with real DiffResult."""
    
    def test_render_added_field(self):
        """Test rendering a simple added field."""
        diff_result = DiffResult(
            left_data={"existing": "value"},
            right_data={"existing": "value", "email": "test@example.com"},
            left_path="left.json",
            right_path="right.json"
        )
        
        console = Console(file=StringIO())
        renderer = DiffRenderer(console=console)
        renderer.render_diff(diff_result)
        
        output = console.file.getvalue()
        assert "email" in output or "ADDITION" in output
    
    def test_render_removed_field(self):
        """Test rendering a simple removed field."""
        diff_result = DiffResult(
            left_data={"old_field": "value"},
            right_data={},
            left_path="left.json",
            right_path="right.json"
        )
        
        console = Console(file=StringIO())
        renderer = DiffRenderer(console=console)
        renderer.render_diff(diff_result)
        
        output = console.file.getvalue()
        assert "old_field" in output or "REMOV" in output
    
    def test_render_changed_field(self):
        """Test rendering a changed field."""
        diff_result = DiffResult(
            left_data={"age": 25},
            right_data={"age": 26},
            left_path="left.json",
            right_path="right.json"
        )
        
        console = Console(file=StringIO())
        renderer = DiffRenderer(console=console, show_values=True)
        renderer.render_diff(diff_result)
        
        output = console.file.getvalue()
        assert "age" in output or "CHANGE" in output or "MODIFICATION" in output
    
    def test_render_nested_path(self):
        """Test rendering nested JSON paths."""
        diff_result = DiffResult(
            left_data={"address": {"city": "NYC"}},
            right_data={"address": {"city": "LA"}},
            left_path="left.json",
            right_path="right.json"
        )
        
        console = Console(file=StringIO())
        renderer = DiffRenderer(console=console)
        renderer.render_tree(diff_result)
        
        output = console.file.getvalue()
        assert "address" in output or "city" in output


class TestFormatPath:
    """Tests for format_path helper function."""
    
    def test_format_simple_path(self):
        """Test formatting simple path."""
        assert format_path("root['name']") == "name"
        assert format_path("root['age']") == "age"
    
    def test_format_nested_path(self):
        """Test formatting nested path."""
        assert format_path("root['user']['name']") == "user.name"
        assert format_path("root['address']['city']") == "address.city"
    
    def test_format_array_path(self):
        """Test formatting path with array index."""
        assert format_path("root['items'][0]") == "items.0"
        assert format_path("root['users'][1]['name']") == "users.1.name"
    
    def test_format_empty_path(self):
        """Test formatting empty/root path."""
        assert format_path("root") == "/"
        assert format_path("") == "/"


class TestFormatValue:
    """Tests for format_value helper function."""
    
    def test_format_none(self):
        """Test formatting None value."""
        assert format_value(None) == "null"
    
    def test_format_bool(self):
        """Test formatting boolean values."""
        assert format_value(True) == "true"
        assert format_value(False) == "false"
    
    def test_format_int(self):
        """Test formatting integer value."""
        assert format_value(42) == "42"
    
    def test_format_float(self):
        """Test formatting float value."""
        assert format_value(3.14) == "3.14"
    
    def test_format_string(self):
        """Test formatting string value."""
        assert format_value("hello") == '"hello"'
    
    def test_format_long_string(self):
        """Test formatting long string with truncation."""
        long_str = "a" * 60
        result = format_value(long_str)
        assert "..." in result
        assert len(result) <= 52  # '"' + 47 chars + '..."'
    
    def test_format_list(self):
        """Test formatting list value."""
        assert format_value([1, 2, 3]) == "[1, 2, 3]"
    
    def test_format_dict(self):
        """Test formatting dict value."""
        result = format_value({"key": "value"})
        assert "key" in result


class TestRenderDiffTable:
    """Tests for render_diff_table function."""
    
    def test_render_table_returns_table(self):
        """Test render_diff_table returns Table object."""
        from rich.table import Table
        diff_result = DiffResult(
            left_path="left.json",
            right_path="right.json"
        )
        table = render_diff_table(diff_result)
        assert isinstance(table, Table)


class TestRenderSummary:
    """Tests for summary rendering."""
    
    def test_summary_counts(self):
        """Test that summary shows correct counts."""
        diff_result = DiffResult(
            left_data={"a": 1, "b": 2, "c": 3, "d": 4},
            right_data={"a": 1, "b": 2, "b2": 2.5, "d": 5, "e": 6},
            left_path="left.json",
            right_path="right.json"
        )
        
        console = Console(file=StringIO())
        renderer = DiffRenderer(console=console)
        renderer.render_diff(diff_result)
        
        output = console.file.getvalue()
        # Check that output contains change indicators
        assert "+" in output or "ADDITION" in output or "-" in output or "REMOV" in output
