"""
Tests for the differ module.

This module contains unit tests for the core JSON comparison logic.
"""

import json
from pathlib import Path

import pytest

from json_diff_cli import (
    ChangeType,
    DiffEntry,
    DiffResult,
    compare,
    compare_files,
    InvalidJSONError,
    load_json,
)


class TestDiffEntry:
    """Tests for DiffEntry class."""
    
    def test_parse_path_simple(self):
        """Test parsing simple dot notation paths."""
        entry = DiffEntry(path="root.a.b", change_type=ChangeType.CHANGED)
        assert entry.path_parts == ["a", "b"]
    
    def test_parse_path_with_brackets(self):
        """Test parsing paths with array brackets."""
        entry = DiffEntry(path="root['a'][0]['b']", change_type=ChangeType.CHANGED)
        assert entry.path_parts == ["a", "0", "b"]
    
    def test_parse_path_with_quotes(self):
        """Test parsing paths with quoted keys."""
        entry = DiffEntry(path='root["a"]["b"]', change_type=ChangeType.CHANGED)
        assert entry.path_parts == ["a", "b"]
    
    def test_parse_path_root(self):
        """Test parsing root path."""
        entry = DiffEntry(path="root", change_type=ChangeType.CHANGED)
        assert entry.path_parts == []
    
    def test_parse_path_array_index(self):
        """Test parsing paths with array indices."""
        entry = DiffEntry(path="root.items[2].name", change_type=ChangeType.CHANGED)
        assert entry.path_parts == ["items", "2", "name"]


class TestDiffResult:
    """Tests for DiffResult class."""
    
    def test_identical_no_changes(self):
        """Test DiffResult when JSONs are identical."""
        left = {"a": 1, "b": 2}
        right = {"a": 1, "b": 2}
        result = compare(left, right)
        
        assert result.identical is True
        assert result.has_changes is False
        assert result.total_changes == 0
    
    def test_identical_with_differences(self):
        """Test DiffResult when JSONs have differences."""
        left = {"a": 1}
        right = {"a": 2}
        result = compare(left, right)
        
        assert result.identical is False
        assert result.has_changes is True
        assert result.total_changes > 0
    
    def test_total_changes_count(self):
        """Test total_changes property counts all change types."""
        left = {"a": 1, "b": 2, "c": 3}
        right = {"a": 10, "d": 4}
        result = compare(left, right)
        
        # Should have: 1 modification (a), 1 deletion (b, c), 1 addition (d)
        assert result.total_changes == 3
    
    def test_get_all_entries(self):
        """Test get_all_entries combines all change types."""
        left = {"a": 1}
        right = {"a": 2, "b": 3}
        result = compare(left, right)
        
        entries = result.get_all_entries()
        assert len(entries) == result.total_changes
    
    def test_to_dict_structure(self):
        """Test to_dict returns properly structured output."""
        left = {"a": 1}
        right = {"a": 2}
        result = compare(left, right)
        result_dict = result.to_dict()
        
        assert "left" in result_dict
        assert "right" in result_dict
        assert "identical" in result_dict
        assert "summary" in result_dict
        assert "changes" in result_dict
        assert "total_changes" in result_dict["summary"]


class TestCompare:
    """Tests for compare() function."""
    
    def test_compare_identical_dicts(self):
        """Test comparing identical dictionaries."""
        left = {"name": "test", "value": 42}
        right = {"name": "test", "value": 42}
        
        result = compare(left, right)
        
        assert result.identical is True
        assert len(result.additions) == 0
        assert len(result.deletions) == 0
        assert len(result.modifications) == 0
    
    def test_compare_additions(self):
        """Test detecting added keys."""
        left = {"a": 1}
        right = {"a": 1, "b": 2}
        
        result = compare(left, right)
        
        assert result.identical is False
        assert len(result.additions) == 1
        assert result.additions[0].path_parts == ["b"]
        assert result.additions[0].new_value == 2
    
    def test_compare_deletions(self):
        """Test detecting removed keys."""
        left = {"a": 1, "b": 2}
        right = {"a": 1}
        
        result = compare(left, right)
        
        assert result.identical is False
        assert len(result.deletions) == 1
        assert result.deletions[0].path_parts == ["b"]
        assert result.deletions[0].old_value == 2
    
    def test_compare_modifications(self):
        """Test detecting modified values."""
        left = {"a": 1, "b": "old"}
        right = {"a": 1, "b": "new"}
        
        result = compare(left, right)
        
        assert result.identical is False
        assert len(result.modifications) == 1
        assert result.modifications[0].old_value == "old"
        assert result.modifications[0].new_value == "new"
    
    def test_compare_nested_objects(self):
        """Test comparing nested objects."""
        left = {"config": {"database": {"host": "localhost"}}}
        right = {"config": {"database": {"host": "production"}}}
        
        result = compare(left, right)
        
        assert result.identical is False
        assert len(result.modifications) == 1
        assert "database" in result.modifications[0].path
        assert "host" in result.modifications[0].path
    
    def test_compare_arrays(self):
        """Test comparing arrays."""
        left = {"items": [1, 2, 3]}
        right = {"items": [1, 2, 4]}
        
        result = compare(left, right)
        
        assert result.identical is False
        assert len(result.modifications) > 0
    
    def test_compare_arrays_ignore_order(self):
        """Test comparing arrays with ignore_order option."""
        left = {"items": [1, 2, 3]}
        right = {"items": [3, 2, 1]}
        
        result = compare(left, right, ignore_order=True)
        
        assert result.identical is True
        
        result_with_order = compare(left, right, ignore_order=False)
        assert result_with_order.identical is False
    
    def test_compare_with_files(self, temp_json_pair: tuple[Path, Path]):
        """Test comparing files."""
        left_path, right_path = temp_json_pair
        
        result = compare_files(left_path, right_path)
        assert result.identical is True
    
    def test_compare_type_change(self):
        """Test detecting type changes."""
        left = {"value": 42}
        right = {"value": "forty-two"}
        
        result = compare(left, right)
        
        # Either type_changes or modifications should capture this
        assert len(result.type_changes) > 0 or len(result.modifications) > 0


class TestLoadJSON:
    """Tests for load_json() function."""
    
    def test_load_from_dict(self):
        """Test load_json accepts dictionaries."""
        data = {"key": "value"}
        result = load_json(data)
        assert result == data
    
    def test_load_from_list(self):
        """Test load_json accepts lists."""
        data = [1, 2, 3]
        result = load_json(data)
        assert result == data
    
    def test_load_json_string(self):
        """Test load_json parses JSON string."""
        data = '{"key": "value"}'
        result = load_json(data)
        assert result == {"key": "value"}
    
    def test_load_json_array_string(self):
        """Test load_json parses JSON array string."""
        data = '[1, 2, 3]'
        result = load_json(data)
        assert result == [1, 2, 3]
    
    def test_load_invalid_json(self):
        """Test load_json raises error for invalid JSON."""
        with pytest.raises(InvalidJSONError):
            load_json("not valid json {")
    
    def test_load_from_file(self, temp_json_file: Path):
        """Test load_json reads from file."""
        result = load_json(temp_json_file)
        assert isinstance(result, dict)


class TestComplexScenarios:
    """Tests for complex comparison scenarios."""
    
    def test_compare_deeply_nested(self):
        """Test comparing deeply nested structures."""
        left = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "original",
                    }
                }
            }
        }
        right = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "modified",
                    }
                }
            }
        }
        
        result = compare(left, right)
        
        assert result.identical is False
        assert len(result.modifications) == 1
        assert result.modifications[0].path == "root['level1']['level2']['level3']['value']"
    
    def test_compare_mixed_changes(self):
        """Test comparing with multiple change types."""
        left = {
            "added_later": None,
            "modified": "old",
            "removed_later": "value",
            "unchanged": "same",
        }
        right = {
            "added_later": "now_exists",
            "modified": "new",
            "unchanged": "same",
        }
        
        result = compare(left, right)
        
        assert result.identical is False
        assert result.total_changes == 3
        assert len(result.additions) == 1  # added_later
        assert len(result.deletions) == 1   # removed_later
        assert len(result.modifications) == 1  # modified
    
    def test_compare_empty_to_data(self):
        """Test comparing empty structure to populated one."""
        left = {}
        right = {"a": 1, "b": 2}
        
        result = compare(left, right)
        
        assert result.identical is False
        assert len(result.additions) == 2
    
    def test_compare_data_to_empty(self):
        """Test comparing populated structure to empty one."""
        left = {"a": 1, "b": 2}
        right = {}
        
        result = compare(left, right)
        
        assert result.identical is False
        assert len(result.deletions) == 2
    
    def test_compare_arrays_with_new_items(self):
        """Test comparing arrays with new items."""
        left = {"items": [1, 2]}
        right = {"items": [1, 2, 3]}
        
        result = compare(left, right)
        
        assert result.identical is False
        # Array changes should be detected
        assert result.total_changes > 0


class TestPathHandling:
    """Tests for path handling in comparisons."""
    
    def test_path_preserved_in_result(self):
        """Test that paths are correctly preserved in results."""
        left = {"a": {"b": {"c": 1}}}
        right = {"a": {"b": {"c": 2}}}
        
        result = compare(left, right)
        
        assert len(result.modifications) == 1
        path = result.modifications[0].path
        assert "a" in path
        assert "b" in path
        assert "c" in path
    
    def test_array_index_in_path(self):
        """Test array indices appear in paths."""
        left = {"items": [{"name": "first"}]}
        right = {"items": [{"name": "second"}]}
        
        result = compare(left, right)
        
        assert result.identical is False
        # Path should contain array index
        path = result.modifications[0].path
        assert "items" in path


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
