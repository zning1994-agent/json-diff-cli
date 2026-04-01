"""Tests for the renderer module."""

import pytest
from io import StringIO
from typing import Any, Dict

from rich.console import Console

from json_diff_cli import DiffResult
from json_diff_cli.renderer import (
    DiffRenderer,
    DiffTheme,
    ChangeType,
    render_diff,
    render_tree,
    DiffRenderer,
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
            left_path="left.json",
            right_path="right.json"
        )
        
        console = Console(file=StringIO())
        renderer = DiffRenderer(console=console)
        renderer.render_diff(diff_result)
        
        output = console.file.getvalue()
        assert "identical" in output.lower() or "No differences" in output
    
    def test_render_diff_with_changes(self):
        """Test rendering differences in table format."""
        diff_result = DiffResult(
            left_path="left.json",
            right_path="right.json",
            added={"root['new_key']"},
            removed={"root['old_key']"},
            changed={"root['modified_key']"}
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
            left_path="left.json",
            right_path="right.json",
            added={"root['name']"},
            changed={"root['age']"}
        )
        
        console = Console(file=StringIO())
        renderer = DiffRenderer(console=console)
        renderer.render_tree(diff_result)
        
        output = console.file.getvalue()
        assert "Comparing" in output
        assert "ADDITIONS" in output or "MODIFICATIONS" in output


class TestRenderDiffFunction:
    """Tests for module-level render_diff function."""
    
    def test_render_diff_no_error(self):
        """Test render_diff doesn't raise exceptions."""
        diff_result = DiffResult(
            left_path="left.json",
            right_path="right.json",
            added={"root['key']"}
        )
        
        # Should not raise
        render_diff(diff_result)
    
    def test_render_diff_with_kwargs(self):
        """Test render_diff passes kwargs correctly."""
        diff_result = DiffResult(
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
            left_path="left.json",
            right_path="right.json",
            changed={"root['key']"}
        )
        
        # Should not raise
        render_tree(diff_result)
    
    def test_render_tree_with_kwargs(self):
        """Test render_tree passes kwargs correctly."""
        diff_result = DiffResult(
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
            left_path="left.json",
            right_path="right.json",
            added={"root['email']"},
            differences={
                "dictionary_item_added": {
                    "root['email']": "test@example.com"
                }
            }
        )
        
        console = Console(file=StringIO())
        renderer = DiffRenderer(console=console)
        renderer.render_diff(diff_result)
        
        output = console.file.getvalue()
        assert "email" in output
        assert "+" in output or "ADD" in output
    
    def test_render_removed_field(self):
        """Test rendering a simple removed field."""
        diff_result = DiffResult(
            left_path="left.json",
            right_path="right.json",
            removed={"root['old_field']"}
        )
        
        console = Console(file=StringIO())
        renderer = DiffRenderer(console=console)
        renderer.render_diff(diff_result)
        
        output = console.file.getvalue()
        assert "old_field" in output
        assert "-" in output or "REMOV" in output
    
    def test_render_changed_field(self):
        """Test rendering a changed field."""
        diff_result = DiffResult(
            left_path="left.json",
            right_path="right.json",
            changed={"root['age']"},
            differences={
                "values_changed": {
                    "root['age']": {
                        "old_value": 25,
                        "new_value": 26
                    }
                }
            }
        )
        
        console = Console(file=StringIO())
        renderer = DiffRenderer(console=console, show_values=True)
        renderer.render_diff(diff_result)
        
        output = console.file.getvalue()
        assert "age" in output
        assert "~" in output or "CHANGE" in output
    
    def test_render_nested_path(self):
        """Test rendering nested JSON paths."""
        diff_result = DiffResult(
            left_path="left.json",
            right_path="right.json",
            changed={"root['address']['city']"}
        )
        
        console = Console(file=StringIO())
        renderer = DiffRenderer(console=console)
        renderer.render_tree(diff_result)
        
        output = console.file.getvalue()
        assert "address" in output
        assert "city" in output


class TestRenderSummary:
    """Tests for summary rendering."""
    
    def test_summary_counts(self):
        """Test that summary shows correct counts."""
        diff_result = DiffResult(
            left_path="left.json",
            right_path="right.json",
            added={"root['a']", "root['b']"},
            removed={"root['c']"},
            changed={"root['d']"}
        )
        
        console = Console(file=StringIO())
        renderer = DiffRenderer(console=console)
        renderer.render_diff(diff_result)
        
        output = console.file.getvalue()
        assert "2" in output  # 2 additions
        assert "1" in output  # 1 removal
