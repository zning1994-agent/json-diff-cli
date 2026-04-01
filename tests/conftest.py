"""Pytest fixtures for json-diff-cli tests."""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test files."""
    return tmp_path


@pytest.fixture
def sample_json_left():
    """Sample left JSON data."""
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
def sample_json_right():
    """Sample right JSON data."""
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
def json_file_left(temp_dir, sample_json_left):
    """Create a temporary left JSON file."""
    file_path = temp_dir / "left.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(sample_json_left, f, indent=2)
    return file_path


@pytest.fixture
def json_file_right(temp_dir, sample_json_right):
    """Create a temporary right JSON file."""
    file_path = temp_dir / "right.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(sample_json_right, f, indent=2)
    return file_path


@pytest.fixture
def empty_json_file(temp_dir):
    """Create an empty JSON file."""
    file_path = temp_dir / "empty.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump({}, f)
    return file_path


@pytest.fixture
def invalid_json_file(temp_dir):
    """Create an invalid JSON file."""
    file_path = temp_dir / "invalid.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("{ invalid json }")
    return file_path


@pytest.fixture
def nested_json_left():
    """Nested left JSON data."""
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
def nested_json_right():
    """Nested right JSON data."""
    return {
        "level1": {
            "level2": {
                "level3": {
                    "value": "new"
                }
            }
        }
    }


def create_json_file(path: Path, data: Dict[str, Any]) -> Path:
    """Helper to create a JSON file with given data."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    return path
