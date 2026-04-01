"""
Test fixtures and configuration for json-diff-cli tests.
"""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest


@pytest.fixture
def sample_json_simple() -> Dict[str, Any]:
    """Simple JSON object for testing."""
    return {
        "name": "test",
        "version": "1.0.0",
        "enabled": True,
    }


@pytest.fixture
def sample_json_nested() -> Dict[str, Any]:
    """Nested JSON object for testing."""
    return {
        "project": "json-diff-cli",
        "config": {
            "database": {
                "host": "localhost",
                "port": 5432,
                "credentials": {
                    "username": "admin",
                    "password": "secret",
                },
            },
            "cache": {
                "enabled": True,
                "ttl": 3600,
            },
        },
        "features": ["cli", "api", "webhook"],
    }


@pytest.fixture
def sample_json_array() -> Dict[str, Any]:
    """JSON with arrays for testing."""
    return {
        "users": [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ],
        "tags": ["python", "cli", "json"],
    }


@pytest.fixture
def temp_json_file(tmp_path: Path, sample_json_simple: Dict[str, Any]) -> Path:
    """Create a temporary JSON file with simple content."""
    file_path = tmp_path / "test.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(sample_json_simple, f)
    return file_path


@pytest.fixture
def temp_json_pair(
    tmp_path: Path,
    sample_json_simple: Dict[str, Any],
) -> tuple[Path, Path]:
    """Create a pair of temporary JSON files."""
    left_path = tmp_path / "left.json"
    right_path = tmp_path / "right.json"
    
    with open(left_path, "w", encoding="utf-8") as f:
        json.dump(sample_json_simple, f)
    
    with open(right_path, "w", encoding="utf-8") as f:
        json.dump(sample_json_simple, f)
    
    return left_path, right_path
