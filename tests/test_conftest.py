"""Tests to verify conftest.py fixtures work correctly."""

import json
import pytest
from pathlib import Path


class TestDataFixtures:
    """Test JSON data fixtures."""

    def test_sample_json_left(self, sample_json_left):
        """Test sample_json_left fixture returns expected data."""
        assert sample_json_left["name"] == "John"
        assert sample_json_left["age"] == 30
        assert sample_json_left["city"] == "Beijing"
        assert len(sample_json_left["skills"]) == 2

    def test_sample_json_right(self, sample_json_right):
        """Test sample_json_right fixture returns expected data."""
        assert sample_json_right["name"] == "John"
        assert sample_json_right["age"] == 31
        assert sample_json_right["email"] == "john@example.com"

    def test_nested_json_fixtures(self, nested_json_left, nested_json_right):
        """Test nested JSON fixtures have different values."""
        assert nested_json_left["level1"]["level2"]["level3"]["value"] == "old"
        assert nested_json_right["level1"]["level2"]["level3"]["value"] == "new"

    def test_edge_case_fixtures(self, edge_case_json_left, edge_case_json_right):
        """Test edge case fixtures contain expected edge cases."""
        assert edge_case_json_left["null_value"] is None
        assert edge_case_json_right["null_value"] == "string"
        assert edge_case_json_left["bool_true"] is True
        assert edge_case_json_right["bool_false"] is True
        assert edge_case_json_left["zero"] == 0
        assert edge_case_json_left["empty_string"] == ""

    def test_identical_json_fixture(self, identical_json):
        """Test identical_json fixture has proper structure."""
        assert identical_json["name"] == "Alice"
        assert identical_json["active"] is True
        assert isinstance(identical_json["config"], dict)


class TestFileFixtures:
    """Test file creation fixtures."""

    def test_json_file_left(self, json_file_left, sample_json_left):
        """Test json_file_left creates valid file with correct data."""
        assert json_file_left.exists()
        assert json_file_left.suffix == ".json"
        content = json.loads(json_file_left.read_text(encoding='utf-8'))
        assert content == sample_json_left

    def test_json_file_right(self, json_file_right, sample_json_right):
        """Test json_file_right creates valid file with correct data."""
        assert json_file_right.exists()
        content = json.loads(json_file_right.read_text(encoding='utf-8'))
        assert content == sample_json_right

    def test_empty_json_file(self, empty_json_file):
        """Test empty_json_file creates valid empty JSON."""
        assert empty_json_file.exists()
        content = json.loads(empty_json_file.read_text(encoding='utf-8'))
        assert content == {}

    def test_invalid_json_file(self, invalid_json_file):
        """Test invalid_json_file contains invalid JSON."""
        assert invalid_json_file.exists()
        with pytest.raises(json.JSONDecodeError):
            json.loads(invalid_json_file.read_text(encoding='utf-8'))

    def test_binary_file(self, binary_file):
        """Test binary_file contains binary data."""
        assert binary_file.exists()
        with pytest.raises(UnicodeDecodeError):
            binary_file.read_text(encoding='utf-8')


class TestFactoryFixtures:
    """Test factory fixtures."""

    def test_create_json_file(self, create_json_file, tmp_path):
        """Test create_json_file factory creates files correctly."""
        data = {"custom": "data", "nested": {"key": 123}}
        file_path = create_json_file("custom.json", data)
        
        assert file_path.exists()
        assert file_path.name == "custom.json"
        content = json.loads(file_path.read_text(encoding='utf-8'))
        assert content == data

    def test_create_json_pair(self, create_json_pair):
        """Test create_json_pair factory creates both files correctly."""
        left_data = {"key": "left_value"}
        right_data = {"key": "right_value", "new_key": "added"}
        
        left_path, right_path = create_json_pair(left_data, right_data)
        
        assert left_path.exists()
        assert right_path.exists()
        assert left_path.read_text(encoding='utf-8') == json.dumps(left_data, indent=2)
        assert right_path.read_text(encoding='utf-8') == json.dumps(right_data, indent=2)


class TestCLIFixtures:
    """Test CLI fixtures."""

    def test_cli_runner(self, cli_runner):
        """Test cli_runner provides Click test runner."""
        from click.testing import CliRunner as ClickCliRunner
        assert isinstance(cli_runner, ClickCliRunner)

    def test_cli_runner_invoke(self, cli_runner):
        """Test cli_runner can invoke CLI commands."""
        from json_diff_cli.cli import main
        result = cli_runner.invoke(main, ['--version'])
        assert result.exit_code == 0
        assert '0.1.0' in result.output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
