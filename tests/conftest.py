"""Pytest fixtures for json-diff-cli tests."""

import pytest
import json
from pathlib import Path
from typing import Any, Dict


@pytest.fixture
def sample_json_left() -> Dict[str, Any]:
    """Sample JSON data for left file."""
    return {
        "name": "John",
        "age": 30,
        "city": "Beijing",
        "skills": ["Python", "Go"],
        "address": {
            "street": "Main St",
            "zip": "100000"
        }
    }


@pytest.fixture
def sample_json_right() -> Dict[str, Any]:
    """Sample JSON data for right file."""
    return {
        "name": "John",
        "age": 31,
        "city": "Shanghai",
        "skills": ["Python", "Go", "Rust"],
        "address": {
            "street": "Main St",
            "zip": "200000"
        },
        "email": "john@example.com"
    }


@pytest.fixture
def temp_json_files(tmp_path, sample_json_left, sample_json_right):
    """Create temporary JSON files."""
    left_file = tmp_path / "left.json"
    right_file = tmp_path / "right.json"
    
    left_file.write_text(json.dumps(sample_json_left, indent=2))
    right_file.write_text(json.dumps(sample_json_right, indent=2))
    
    return left_file, right_file


@pytest.fixture
def empty_json_left() -> Dict[str, Any]:
    """Empty JSON object for left."""
    return {}


@pytest.fixture
def empty_json_right() -> Dict[str, Any]:
    """Empty JSON object for right."""
    return {}


@pytest.fixture
def nested_json() -> Dict[str, Any]:
    """Deeply nested JSON structure."""
    return {
        "level1": {
            "level2": {
                "level3": {
                    "value": "deep"
                }
            }
        }
    }
