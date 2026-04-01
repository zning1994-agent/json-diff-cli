"""
Test module for differ.py - core JSON comparison logic.

Tests cover:
- Additions: keys present in right but not in left
- Deletions: keys present in left but not in right
- Modifications: same key, different values
- Nested structure comparisons
- Array comparisons
"""

import json
import tempfile
import pytest
from pathlib import Path

from json_diff_cli.differ import compare, DiffResult


class TestCompareFunction:
    """Test the main compare() function."""

    def test_compare_returns_diff_result(self):
        """Test that compare() returns a DiffResult instance."""
        left_data = {"name": "Alice"}
        right_data = {"name": "Bob"}
        
        result = compare(left_data, right_data)
        
        assert isinstance(result, DiffResult)

    def test_compare_with_identical_data(self):
        """Test compare with completely identical data."""
        left_data = {"name": "Alice", "age": 30}
        right_data = {"name": "Alice", "age": 30}
        
        result = compare(left_data, right_data)
        
        assert result.additions == {}
        assert result.deletions == {}
        assert result.modifications == {}
        assert result.summary["total_changes"] == 0


class TestAdditions:
    """Test detection of added keys (present in right but not in left)."""

    def test_simple_addition(self):
        """Test simple key addition."""
        left_data = {"name": "Alice"}
        right_data = {"name": "Alice", "age": 30}
        
        result = compare(left_data, right_data)
        
        assert "age" in result.additions
        assert result.additions["age"] == 30
        assert result.summary["additions"] == 1

    def test_nested_addition(self):
        """Test nested key addition."""
        left_data = {"user": {"name": "Alice"}}
        right_data = {"user": {"name": "Alice", "email": "alice@example.com"}}
        
        result = compare(left_data, right_data)
        
        assert "root['user']['email']" in result.additions
        assert result.additions["root['user']['email']"] == "alice@example.com"

    def test_multiple_additions(self):
        """Test multiple key additions."""
        left_data = {"a": 1}
        right_data = {"a": 1, "b": 2, "c": 3}
        
        result = compare(left_data, right_data)
        
        assert len(result.additions) == 2
        assert "b" in result.additions
        assert "c" in result.additions

    def test_array_item_addition(self):
        """Test array item addition."""
        left_data = {"items": [1, 2]}
        right_data = {"items": [1, 2, 3]}
        
        result = compare(left_data, right_data)
        
        assert len(result.additions) >= 1


class TestDeletions:
    """Test detection of deleted keys (present in left but not in right)."""

    def test_simple_deletion(self):
        """Test simple key deletion."""
        left_data = {"name": "Alice", "age": 30}
        right_data = {"name": "Alice"}
        
        result = compare(left_data, right_data)
        
        assert "age" in result.deletions
        assert result.deletions["age"] == 30
        assert result.summary["deletions"] == 1

    def test_nested_deletion(self):
        """Test nested key deletion."""
        left_data = {"user": {"name": "Alice", "email": "alice@example.com"}}
        right_data = {"user": {"name": "Alice"}}
        
        result = compare(left_data, right_data)
        
        assert "root['user']['email']" in result.deletions
        assert result.deletions["root['user']['email']"] == "alice@example.com"

    def test_multiple_deletions(self):
        """Test multiple key deletions."""
        left_data = {"a": 1, "b": 2, "c": 3}
        right_data = {"a": 1}
        
        result = compare(left_data, right_data)
        
        assert len(result.deletions) == 2
        assert "b" in result.deletions
        assert "c" in result.deletions


class TestModifications:
    """Test detection of modified values (same key, different value)."""

    def test_simple_modification(self):
        """Test simple value modification."""
        left_data = {"name": "Alice"}
        right_data = {"name": "Bob"}
        
        result = compare(left_data, right_data)
        
        assert "name" in result.modifications
        assert result.modifications["name"]["old_value"] == "Alice"
        assert result.modifications["name"]["new_value"] == "Bob"
        assert result.summary["modifications"] == 1

    def test_type_change_modification(self):
        """Test modification from one type to another."""
        left_data = {"value": "123"}
        right_data = {"value": 123}
        
        result = compare(left_data, right_data)
        
        assert "value" in result.modifications

    def test_nested_modification(self):
        """Test nested value modification."""
        left_data = {"user": {"name": "Alice", "age": 30}}
        right_data = {"user": {"name": "Alice", "age": 31}}
        
        result = compare(left_data, right_data)
        
        assert "root['user']['age']" in result.modifications
        assert result.modifications["root['user']['age']"]["old_value"] == 30
        assert result.modifications["root['user']['age']"]["new_value"] == 31

    def test_deeply_nested_modification(self):
        """Test deeply nested value modification."""
        left_data = {"a": {"b": {"c": {"d": 1}}}}
        right_data = {"a": {"b": {"c": {"d": 2}}}}
        
        result = compare(left_data, right_data)
        
        assert "root['a']['b']['c']['d']" in result.modifications
        assert result.modifications["root['a']['b']['c']['d']"]["old_value"] == 1
        assert result.modifications["root['a']['b']['c']['d']"]["new_value"] == 2


class TestNestedStructures:
    """Test comparison of nested data structures."""

    def test_deeply_nested_objects(self):
        """Test comparison of deeply nested objects."""
        left_data = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "original"
                    }
                }
            }
        }
        right_data = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "modified"
                    }
                }
            }
        }
        
        result = compare(left_data, right_data)
        
        assert len(result.modifications) == 1
        assert "root['level1']['level2']['level3']['value']" in result.modifications

    def test_mixed_nested_changes(self):
        """Test nested structure with additions, deletions, and modifications."""
        left_data = {
            "config": {
                "database": {
                    "host": "localhost",
                    "port": 5432
                },
                "cache": True
            }
        }
        right_data = {
            "config": {
                "database": {
                    "host": "production-db",
                    "port": 5432,
                    "ssl": True
                },
                "cache": False,
                "debug": True
            }
        }
        
        result = compare(left_data, right_data)
        
        # Should have modifications, additions, and deletions
        assert result.summary["total_changes"] >= 4

    def test_empty_nested_object(self):
        """Test comparison with empty nested object."""
        left_data = {"empty": {}}
        right_data = {"empty": {"key": "value"}}
        
        result = compare(left_data, right_data)
        
        assert len(result.additions) >= 1

    def test_nested_object_to_primitive(self):
        """Test type change from object to primitive."""
        left_data = {"value": {"nested": "object"}}
        right_data = {"value": "string"}
        
        result = compare(left_data, right_data)
        
        assert len(result.modifications) == 1


class TestArrayComparisons:
    """Test comparison of arrays/lists."""

    def test_identical_arrays(self):
        """Test identical arrays."""
        left_data = {"items": [1, 2, 3]}
        right_data = {"items": [1, 2, 3]}
        
        result = compare(left_data, right_data)
        
        assert result.summary["total_changes"] == 0

    def test_array_order_change(self):
        """Test array with changed order."""
        left_data = {"items": [1, 2, 3]}
        right_data = {"items": [3, 2, 1]}
        
        result = compare(left_data, right_data)
        
        # Arrays with different order should be detected as modified
        assert result.summary["total_changes"] >= 1

    def test_array_element_modification(self):
        """Test array with modified element."""
        left_data = {"items": [1, 2, 3]}
        right_data = {"items": [1, 99, 3]}
        
        result = compare(left_data, right_data)
        
        assert result.summary["total_changes"] >= 1

    def test_array_length_change(self):
        """Test array with different length."""
        left_data = {"items": [1, 2]}
        right_data = {"items": [1, 2, 3, 4]}
        
        result = compare(left_data, right_data)
        
        assert result.summary["total_changes"] >= 1

    def test_nested_array(self):
        """Test nested array structures."""
        left_data = {"matrix": [[1, 2], [3, 4]]}
        right_data = {"matrix": [[1, 2], [3, 5]]}
        
        result = compare(left_data, right_data)
        
        assert result.summary["total_changes"] >= 1


class TestSummaryStatistics:
    """Test summary statistics calculation."""

    def test_empty_diff_summary(self):
        """Test summary for identical data."""
        left_data = {"a": 1, "b": 2}
        right_data = {"a": 1, "b": 2}
        
        result = compare(left_data, right_data)
        
        assert result.summary["total_changes"] == 0
        assert result.summary["additions"] == 0
        assert result.summary["deletions"] == 0
        assert result.summary["modifications"] == 0

    def test_all_change_types_summary(self):
        """Test summary with all types of changes."""
        left_data = {
            "keep": "same",
            "modify": "old",
            "delete": "this"
        }
        right_data = {
            "keep": "same",
            "modify": "new",
            "add": "value"
        }
        
        result = compare(left_data, right_data)
        
        assert result.summary["total_changes"] >= 3
        assert result.summary["additions"] >= 1
        assert result.summary["deletions"] >= 1
        assert result.summary["modifications"] >= 1


class TestDiffResultMethods:
    """Test DiffResult utility methods."""

    def test_has_changes_false(self):
        """Test has_changes returns False for identical data."""
        left_data = {"name": "Alice"}
        right_data = {"name": "Alice"}
        
        result = compare(left_data, right_data)
        
        assert result.has_changes() is False

    def test_has_changes_true(self):
        """Test has_changes returns True when differences exist."""
        left_data = {"name": "Alice"}
        right_data = {"name": "Bob"}
        
        result = compare(left_data, right_data)
        
        assert result.has_changes() is True

    def test_get_changed_paths(self):
        """Test getting all changed paths."""
        left_data = {"a": 1, "b": 2}
        right_data = {"a": 99, "c": 3}
        
        result = compare(left_data, right_data)
        
        paths = result.get_changed_paths()
        assert len(paths) >= 2


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_empty_objects(self):
        """Test comparison of two empty objects."""
        left_data = {}
        right_data = {}
        
        result = compare(left_data, right_data)
        
        assert result.summary["total_changes"] == 0

    def test_none_values(self):
        """Test handling of None values."""
        left_data = {"value": None}
        right_data = {"value": "string"}
        
        result = compare(left_data, right_data)
        
        assert result.summary["modifications"] >= 1

    def test_boolean_values(self):
        """Test comparison of boolean values."""
        left_data = {"enabled": True}
        right_data = {"enabled": False}
        
        result = compare(left_data, right_data)
        
        assert result.summary["modifications"] == 1

    def test_numeric_precision(self):
        """Test handling of numeric values with precision."""
        left_data = {"pi": 3.14159}
        right_data = {"pi": 3.14160}
        
        result = compare(left_data, right_data)
        
        assert result.summary["modifications"] == 1

    def test_special_characters_in_keys(self):
        """Test handling of special characters in keys."""
        left_data = {"key.with.dots": 1}
        right_data = {"key.with.dots": 2}
        
        result = compare(left_data, right_data)
        
        assert result.summary["modifications"] == 1

    def test_unicode_strings(self):
        """Test handling of unicode strings."""
        left_data = {"name": "张三"}
        right_data = {"name": "李四"}
        
        result = compare(left_data, right_data)
        
        assert result.summary["modifications"] == 1


class TestFileComparison:
    """Test comparison using file paths (when files exist)."""

    def test_compare_with_file_paths(self):
        """Test compare() with actual file paths."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as left_file:
            json.dump({"name": "Alice", "age": 30}, left_file)
            left_path = left_file.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as right_file:
            json.dump({"name": "Bob", "age": 30}, right_file)
            right_path = right_file.name
        
        try:
            result = compare(left_path, right_path)
            
            assert result.summary["modifications"] >= 1
            assert result.summary["additions"] >= 0
            assert result.summary["deletions"] >= 0
        finally:
            Path(left_path).unlink(missing_ok=True)
            Path(right_path).unlink(missing_ok=True)

    def test_compare_nonexistent_file(self):
        """Test compare() with nonexistent file path."""
        from json_diff_cli.exceptions import FileReadError
        
        with pytest.raises(FileReadError):
            compare("/nonexistent/path/left.json", "/nonexistent/path/right.json")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
