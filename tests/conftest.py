"""Pytest fixtures for json-diff-cli tests."""

import json
from pathlib import Path
from typing import Any, Dict, Union

import pytest


# =============================================================================
# JSON Data Fixtures
# =============================================================================

@pytest.fixture
def sample_json_left() -> Dict[str, Any]:
    """Sample left JSON data for testing."""
    return {
        "name": "John",
        "age": 30,
        "city": "Beijing",
        "skills": ["Python", "Go"],
        "profile": {
            "education": "MIT",
            "experience": 5
        }
    }


@pytest.fixture
def sample_json_right() -> Dict[str, Any]:
    """Sample right JSON data for testing."""
    return {
        "name": "John",
        "age": 31,
        "city": "Shanghai",
        "skills": ["Python", "JavaScript"],
        "profile": {
            "education": "MIT",
            "experience": 6
        },
        "email": "john@example.com"
    }


@pytest.fixture
def nested_json_left() -> Dict[str, Any]:
    """Nested left JSON data for testing deep comparisons."""
    return {
        "level1": {
            "level2": {
                "level3": {
                    "value": "old"
                }
            }
        }
    }


@pytest.fixture
def nested_json_right() -> Dict[str, Any]:
    """Nested right JSON data for testing deep comparisons."""
    return {
        "level1": {
            "level2": {
                "level3": {
                    "value": "new"
                }
            }
        }
    }


@pytest.fixture
def array_json_left() -> Dict[str, Any]:
    """Left JSON with array data."""
    return {
        "items": [1, 2, 3],
        "matrix": [[1, 2], [3, 4]],
        "mixed": [{"a": 1}, {"b": 2}]
    }


@pytest.fixture
def array_json_right() -> Dict[str, Any]:
    """Right JSON with array data (modified)."""
    return {
        "items": [1, 2, 4, 5],
        "matrix": [[1, 2], [3, 5]],
        "mixed": [{"a": 1}, {"c": 3}]
    }


@pytest.fixture
def edge_case_json_left() -> Dict[str, Any]:
    """Left JSON with edge case values."""
    return {
        "null_value": None,
        "bool_true": True,
        "bool_false": False,
        "zero": 0,
        "empty_string": "",
        "empty_array": [],
        "empty_object": {},
        "float_precision": 3.14159,
        "unicode": "张三",
        "special_chars": "key.with.dots",
        "negative": -100,
        "scientific": 1e10
    }


@pytest.fixture
def edge_case_json_right() -> Dict[str, Any]:
    """Right JSON with edge case values (different)."""
    return {
        "null_value": "string",
        "bool_true": False,
        "bool_false": True,
        "zero": 1,
        "empty_string": "text",
        "empty_array": [1],
        "empty_object": {"key": "value"},
        "float_precision": 3.14160,
        "unicode": "李四",
        "special_chars": "key.with.dots.modified",
        "negative": 100,
        "scientific": 1e-10
    }


@pytest.fixture
def type_change_json_left() -> Dict[str, Any]:
    """Left JSON with values that change type."""
    return {
        "string_to_number": "123",
        "number_to_string": 123,
        "array_to_object": [1, 2, 3],
        "object_to_array": {"a": 1, "b": 2},
        "null_to_value": None,
        "value_to_null": "something"
    }


@pytest.fixture
def type_change_json_right() -> Dict[str, Any]:
    """Right JSON with changed types."""
    return {
        "string_to_number": 123,
        "number_to_string": "123",
        "array_to_object": {"0": 1, "1": 2, "2": 3},
        "object_to_array": [1, 2],
        "null_to_value": "new value",
        "value_to_null": None
    }


@pytest.fixture
def identical_json() -> Dict[str, Any]:
    """JSON data that is identical in both files."""
    return {
        "name": "Alice",
        "age": 30,
        "active": True,
        "tags": ["python", "cli"],
        "config": {
            "debug": False,
            "timeout": 30
        }
    }


@pytest.fixture
def mixed_changes_left() -> Dict[str, Any]:
    """Left JSON for testing mixed additions, deletions, and modifications."""
    return {
        "keep": "same",
        "modify": "old_value",
        "delete_this": "removed",
        "nested": {
            "keep": "same",
            "modify": 100,
            "delete_nested": "value"
        }
    }


@pytest.fixture
def mixed_changes_right() -> Dict[str, Any]:
    """Right JSON for testing mixed additions, deletions, and modifications."""
    return {
        "keep": "same",
        "modify": "new_value",
        "add_this": "new",
        "nested": {
            "keep": "same",
            "modify": 200,
            "add_nested": "value"
        }
    }


# =============================================================================
# File Creation Fixtures
# =============================================================================

@pytest.fixture
def json_file_left(tmp_path, sample_json_left) -> Path:
    """Create a temporary left JSON file with sample data."""
    file_path = tmp_path / "left.json"
    file_path.write_text(json.dumps(sample_json_left, indent=2), encoding='utf-8')
    return file_path


@pytest.fixture
def json_file_right(tmp_path, sample_json_right) -> Path:
    """Create a temporary right JSON file with sample data."""
    file_path = tmp_path / "right.json"
    file_path.write_text(json.dumps(sample_json_right, indent=2), encoding='utf-8')
    return file_path


@pytest.fixture
def empty_json_file(tmp_path) -> Path:
    """Create an empty JSON file (valid empty object)."""
    file_path = tmp_path / "empty.json"
    file_path.write_text('{}', encoding='utf-8')
    return file_path


@pytest.fixture
def invalid_json_file(tmp_path) -> Path:
    """Create an invalid JSON file."""
    file_path = tmp_path / "invalid.json"
    file_path.write_text('{ invalid json }', encoding='utf-8')
    return file_path


@pytest.fixture
def empty_file(tmp_path) -> Path:
    """Create an empty file (not valid JSON)."""
    file_path = tmp_path / "empty.txt"
    file_path.write_text('', encoding='utf-8')
    return file_path


@pytest.fixture
def binary_file(tmp_path) -> Path:
    """Create a binary file that cannot be decoded as text."""
    file_path = tmp_path / "binary.bin"
    file_path.write_bytes(b'\x00\x01\x02\x03\xff\xfe\xfd')
    return file_path


# =============================================================================
# Factory Fixtures
# =============================================================================

@pytest.fixture
def create_json_file(tmp_path):
    """Factory fixture to create JSON files with arbitrary data.
    
    Usage:
        file_path = create_json_file("test.json", {"key": "value"})
        file_path = create_json_file("nested.json", {"a": {"b": {"c": 1}}})
    """
    def _create(filename: str, data: Dict[str, Any]) -> Path:
        file_path = tmp_path / filename
        file_path.write_text(json.dumps(data, indent=2), encoding='utf-8')
        return file_path
    return _create


@pytest.fixture
def create_json_pair(tmp_path):
    """Factory fixture to create a pair of JSON files.
    
    Usage:
        left, right = create_json_pair(
            {"name": "Alice"},
            {"name": "Bob"}
        )
    """
    def _create(left_data: Dict[str, Any], right_data: Dict[str, Any]) -> tuple[Path, Path]:
        left_path = tmp_path / "left.json"
        right_path = tmp_path / "right.json"
        left_path.write_text(json.dumps(left_data, indent=2), encoding='utf-8')
        right_path.write_text(json.dumps(right_data, indent=2), encoding='utf-8')
        return left_path, right_path
    return _create


# =============================================================================
# CLI Testing Fixtures
# =============================================================================

@pytest.fixture
def cli_runner():
    """Fixture providing Click CLI test runner."""
    from click.testing import CliRunner
    return CliRunner()


# =============================================================================
# Helper Functions
# =============================================================================

def create_json_file_helper(path: Union[str, Path], data: Dict[str, Any]) -> Path:
    """Helper function to create a JSON file with given data.
    
    Args:
        path: File path to create
        data: Dictionary data to write as JSON
        
    Returns:
        Path to the created file
    """
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(data, indent=2), encoding='utf-8')
    return file_path
