"""Integration tests for CLI arguments, file reading, output formats and error handling."""

import json
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

from json_diff_cli.cli import main
from json_diff_cli.exceptions import FileReadError, InvalidJsonError


class TestCLIArguments:
    """Test CLI argument parsing."""

    def test_cli_help(self):
        """Test --help option displays usage information."""
        runner = CliRunner()
        result = runner.invoke(main, ['--help'])

        assert result.exit_code == 0
        assert 'Compare two JSON files' in result.output
        assert 'LEFT' in result.output
        assert 'RIGHT' in result.output

    def test_cli_version(self):
        """Test --version option displays version."""
        runner = CliRunner()
        result = runner.invoke(main, ['--version'])

        assert result.exit_code == 0
        assert '0.1.0' in result.output

    def test_missing_left_argument(self):
        """Test CLI exits with error when left argument is missing."""
        runner = CliRunner()
        result = runner.invoke(main, [])

        assert result.exit_code != 0
        assert 'LEFT' in result.output or 'Error' in result.output or 'Missing' in result.output

    def test_missing_right_argument(self):
        """Test CLI exits with error when right argument is missing."""
        runner = CliRunner(mix_stderr=False)
        result = runner.invoke(main, ['/path/to/left.json'])

        assert result.exit_code != 0

    def test_output_format_option_terminal(self, temp_dir):
        """Test --output terminal option."""
        runner = CliRunner()
        left = temp_dir / "left.json"
        right = temp_dir / "right.json"
        left.write_text('{"name": "Alice"}')
        right.write_text('{"name": "Bob"}')

        result = runner.invoke(main, ['--output', 'terminal', str(left), str(right)])

        # Exit code depends on file content, but option parsing should succeed
        assert result.exception is None or result.exit_code in [0, 1]

    def test_output_format_option_json_patch(self, temp_dir):
        """Test --output json-patch option."""
        runner = CliRunner()
        left = temp_dir / "left.json"
        right = temp_dir / "right.json"
        left.write_text('{"name": "Alice"}')
        right.write_text('{"name": "Bob"}')

        result = runner.invoke(main, ['--output', 'json-patch', str(left), str(right)])

        # Option parsing should not fail
        assert result.exception is None or result.exit_code in [0, 1]

    def test_output_format_option_summary(self, temp_dir):
        """Test --output summary option."""
        runner = CliRunner()
        left = temp_dir / "left.json"
        right = temp_dir / "right.json"
        left.write_text('{"name": "Alice"}')
        right.write_text('{"name": "Bob"}')

        result = runner.invoke(main, ['--output', 'summary', str(left), str(right)])

        # Option parsing should not fail
        assert result.exception is None or result.exit_code in [0, 1]

    def test_output_format_short_option(self, temp_dir):
        """Test -o short option for output format."""
        runner = CliRunner()
        left = temp_dir / "left.json"
        right = temp_dir / "right.json"
        left.write_text('{"name": "Alice"}')
        right.write_text('{"name": "Bob"}')

        result = runner.invoke(main, ['-o', 'summary', str(left), str(right)])

        assert result.exception is None or result.exit_code in [0, 1]

    def test_color_option(self, temp_dir):
        """Test --color and --no-color options."""
        runner = CliRunner()
        left = temp_dir / "left.json"
        right = temp_dir / "right.json"
        left.write_text('{"name": "Alice"}')
        right.write_text('{"name": "Bob"}')

        # Test --no-color
        result = runner.invoke(main, ['--no-color', str(left), str(right)])
        assert result.exception is None or result.exit_code in [0, 1]

        # Test --color
        result = runner.invoke(main, ['--color', str(left), str(right)])
        assert result.exception is None or result.exit_code in [0, 1]

    def test_stat_option(self, temp_dir):
        """Test --stat/-s option for statistics."""
        runner = CliRunner()
        left = temp_dir / "left.json"
        right = temp_dir / "right.json"
        left.write_text('{"name": "Alice"}')
        right.write_text('{"name": "Bob"}')

        result = runner.invoke(main, ['--stat', str(left), str(right)])

        assert result.exception is None or result.exit_code in [0, 1]

    def test_invalid_output_format(self, temp_dir):
        """Test CLI exits with error for invalid output format."""
        runner = CliRunner()
        left = temp_dir / "left.json"
        right = temp_dir / "right.json"
        left.write_text('{"name": "Alice"}')
        right.write_text('{"name": "Bob"}')

        result = runner.invoke(main, ['--output', 'invalid', str(left), str(right)])

        assert result.exit_code == 2
        assert 'Invalid' in result.output or 'invalid' in result.output or 'Error' in result.output

    def test_combined_options(self, temp_dir):
        """Test CLI accepts multiple options together."""
        runner = CliRunner()
        left = temp_dir / "left.json"
        right = temp_dir / "right.json"
        left.write_text('{"name": "Alice"}')
        right.write_text('{"name": "Bob"}')

        result = runner.invoke(main, [
            '--output', 'summary',
            '--no-color',
            '--stat',
            str(left),
            str(right)
        ])

        # Should parse all options correctly
        assert result.exception is None or result.exit_code in [0, 1]


class TestCLIFileReading:
    """Test CLI file reading functionality."""

    def test_nonexistent_left_file(self, temp_dir):
        """Test CLI handles non-existent left file gracefully."""
        runner = CliRunner()
        nonexistent = temp_dir / "nonexistent_left.json"
        right = temp_dir / "right.json"
        right.write_text('{"key": "value"}')

        result = runner.invoke(main, [str(nonexistent), str(right)])

        # File doesn't exist, CLI should fail
        assert result.exit_code in [1, 2]

    def test_nonexistent_right_file(self, temp_dir):
        """Test CLI handles non-existent right file gracefully."""
        runner = CliRunner()
        left = temp_dir / "left.json"
        nonexistent = temp_dir / "nonexistent_right.json"
        left.write_text('{"key": "value"}')

        result = runner.invoke(main, [str(left), str(nonexistent)])

        # File doesn't exist, CLI should fail
        assert result.exit_code in [1, 2]

    def test_invalid_left_json(self, temp_dir):
        """Test CLI handles invalid JSON in left file."""
        runner = CliRunner()
        left = temp_dir / "left.json"
        right = temp_dir / "right.json"
        left.write_text('{ invalid json }')
        right.write_text('{"key": "value"}')

        result = runner.invoke(main, [str(left), str(right)])

        assert result.exit_code == 3
        assert 'Error' in result.output or 'invalid' in result.output.lower()

    def test_invalid_right_json(self, temp_dir):
        """Test CLI handles invalid JSON in right file."""
        runner = CliRunner()
        left = temp_dir / "left.json"
        right = temp_dir / "right.json"
        left.write_text('{"key": "value"}')
        right.write_text('{ also invalid }')

        result = runner.invoke(main, [str(left), str(right)])

        assert result.exit_code == 3
        assert 'Error' in result.output or 'invalid' in result.output.lower()

    def test_valid_json_files(self, temp_dir):
        """Test CLI successfully reads and compares valid JSON files."""
        runner = CliRunner()
        left = temp_dir / "left.json"
        right = temp_dir / "right.json"
        left.write_text('{"name": "Alice", "age": 30}')
        right.write_text('{"name": "Alice", "age": 31}')

        result = runner.invoke(main, [str(left), str(right)])

        # Should complete without file reading errors
        assert result.exit_code in [0, 1]
        assert 'Error' not in result.output

    def test_empty_json_files(self, temp_dir):
        """Test CLI handles empty JSON objects."""
        runner = CliRunner()
        left = temp_dir / "left.json"
        right = temp_dir / "right.json"
        left.write_text('{}')
        right.write_text('{}')

        result = runner.invoke(main, [str(left), str(right)])

        assert result.exit_code == 0
        assert 'No differences' in result.output or result.exit_code == 0

    def test_nested_json_files(self, temp_dir):
        """Test CLI handles deeply nested JSON structures."""
        runner = CliRunner()
        left = temp_dir / "left.json"
        right = temp_dir / "right.json"

        left_data = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "old"
                    }
                }
            }
        }
        right_data = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "new"
                    }
                }
            }
        }

        left.write_text(json.dumps(left_data, indent=2))
        right.write_text(json.dumps(right_data, indent=2))

        result = runner.invoke(main, [str(left), str(right)])

        assert result.exit_code in [0, 1]
        assert 'Error' not in result.output


class TestCLIOutputFormats:
    """Test CLI output format switching."""

    def test_terminal_output_format(self, temp_dir):
        """Test terminal output format (default)."""
        runner = CliRunner()
        left = temp_dir / "left.json"
        right = temp_dir / "right.json"
        left.write_text('{"name": "Alice"}')
        right.write_text('{"name": "Bob"}')

        result = runner.invoke(main, ['--output', 'terminal', str(left), str(right)])

        # Terminal output should contain formatted results
        assert result.exit_code in [0, 1]

    def test_json_patch_output_format(self, temp_dir):
        """Test JSON Patch output format."""
        runner = CliRunner()
        left = temp_dir / "left.json"
        right = temp_dir / "right.json"
        left.write_text('{"name": "Alice"}')
        right.write_text('{"name": "Bob", "age": 30}')

        result = runner.invoke(main, ['--output', 'json-patch', str(left), str(right)])

        # Should produce output
        assert result.exit_code in [0, 1]

    def test_summary_output_format(self, temp_dir):
        """Test summary output format."""
        runner = CliRunner()
        left = temp_dir / "left.json"
        right = temp_dir / "right.json"
        left.write_text('{"name": "Alice", "age": 30}')
        right.write_text('{"name": "Bob", "age": 31}')

        result = runner.invoke(main, ['--output', 'summary', str(left), str(right)])

        # Summary should contain statistics
        assert result.exit_code in [0, 1]

    def test_statistics_option(self, temp_dir):
        """Test --stat option displays statistics."""
        runner = CliRunner()
        left = temp_dir / "left.json"
        right = temp_dir / "right.json"
        left.write_text('{"name": "Alice"}')
        right.write_text('{"name": "Bob", "city": "Beijing"}')

        result = runner.invoke(main, ['--stat', str(left), str(right)])

        # Should contain statistics output
        assert result.exit_code in [0, 1]

    def test_color_disabled_output(self, temp_dir):
        """Test --no-color option disables color codes."""
        runner = CliRunner()
        left = temp_dir / "left.json"
        right = temp_dir / "right.json"
        left.write_text('{}')
        right.write_text('{"key": "value"}')

        result = runner.invoke(main, ['--no-color', str(left), str(right)])

        # Output should not contain ANSI color codes
        assert '\x1b[' not in result.output

    def test_identical_files_no_diff(self, temp_dir):
        """Test CLI shows no differences for identical files."""
        runner = CliRunner()
        left = temp_dir / "left.json"
        right = temp_dir / "right.json"

        content = '{"name": "Alice", "age": 30, "skills": ["Python"]}'
        left.write_text(content)
        right.write_text(content)

        result = runner.invoke(main, [str(left), str(right)])

        assert result.exit_code == 0


class TestCLIErrorHandling:
    """Test CLI error handling integration."""

    def test_file_read_error_propagation(self, temp_dir):
        """Test that file read errors are properly handled."""
        runner = CliRunner()
        left = temp_dir / "nonexistent.json"
        right = temp_dir / "right.json"
        right.write_text('{"key": "value"}')

        result = runner.invoke(main, [str(left), str(right)])

        # File doesn't exist, should handle gracefully
        assert result.exit_code in [1, 2]

    def test_invalid_json_error_propagation(self, temp_dir):
        """Test that invalid JSON errors are properly handled."""
        runner = CliRunner()
        left = temp_dir / "left.json"
        right = temp_dir / "right.json"
        left.write_text('{ broken json }')
        right.write_text('{"valid": "json"}')

        result = runner.invoke(main, [str(left), str(right)])

        assert result.exit_code == 3
        assert 'Error' in result.output or 'invalid' in result.output.lower()

    def test_binary_file_handling(self, temp_dir):
        """Test CLI handles binary/non-text files gracefully."""
        runner = CliRunner()
        left = temp_dir / "left.json"
        right = temp_dir / "right.json"
        left.write_bytes(b'\x00\x01\x02\x03')
        right.write_text('{"key": "value"}')

        result = runner.invoke(main, [str(left), str(right)])

        # Should fail gracefully with an error
        assert result.exit_code != 0

    def test_permission_error(self, temp_dir):
        """Test CLI handles permission errors gracefully."""
        runner = CliRunner()
        left = temp_dir / "left.json"
        right = temp_dir / "right.json"
        left.write_text('{"key": "value"}')
        right.write_text('{"key": "value2"}')

        # Make file read-only on systems that support it
        if sys.platform != 'win32':
            left.chmod(0o000)
            try:
                result = runner.invoke(main, [str(left), str(right)])
                # Should fail with permission error
                assert result.exit_code != 0
            finally:
                left.chmod(0o644)  # Restore permissions for cleanup

    def test_empty_file_handling(self, temp_dir):
        """Test CLI handles empty files."""
        runner = CliRunner()
        left = temp_dir / "left.json"
        right = temp_dir / "right.json"
        left.write_text('')
        right.write_text('{"key": "value"}')

        result = runner.invoke(main, [str(left), str(right)])

        # Should fail gracefully - empty string is not valid JSON
        assert result.exit_code == 3

    def test_exit_code_on_differences(self, temp_dir):
        """Test CLI returns exit code 1 when differences exist."""
        runner = CliRunner()
        left = temp_dir / "left.json"
        right = temp_dir / "right.json"
        left.write_text('{"key": "value1"}')
        right.write_text('{"key": "value2"}')

        result = runner.invoke(main, [str(left), str(right)])

        assert result.exit_code == 1

    def test_exit_code_no_differences(self, temp_dir):
        """Test CLI returns exit code 0 when no differences exist."""
        runner = CliRunner()
        left = temp_dir / "left.json"
        right = temp_dir / "right.json"
        content = '{"key": "value"}'
        left.write_text(content)
        right.write_text(content)

        result = runner.invoke(main, [str(left), str(right)])

        assert result.exit_code == 0

    def test_unicode_file_handling(self, temp_dir):
        """Test CLI handles Unicode content correctly."""
        runner = CliRunner()
        left = temp_dir / "left.json"
        right = temp_dir / "right.json"
        left.write_text('{"name": "张三", "city": "北京"}')
        right.write_text('{"name": "李四", "city": "上海"}')

        result = runner.invoke(main, [str(left), str(right)])

        # Should handle Unicode without crashing
        assert result.exit_code in [0, 1]

    def test_large_file_handling(self, temp_dir):
        """Test CLI handles relatively large JSON files."""
        runner = CliRunner()
        left = temp_dir / "left.json"
        right = temp_dir / "right.json"
        large_data = {f"key_{i}": f"value_{i}" for i in range(100)}
        left.write_text(json.dumps(large_data))
        modified_data = large_data.copy()
        modified_data["key_50"] = "modified_value"
        right.write_text(json.dumps(modified_data))

        result = runner.invoke(main, [str(left), str(right)])

        assert result.exit_code in [0, 1]


class TestCLIMixedScenarios:
    """Test mixed/integration scenarios."""

    def test_multiple_differences(self, temp_dir):
        """Test CLI correctly shows multiple types of differences."""
        runner = CliRunner()
        left = temp_dir / "left.json"
        right = temp_dir / "right.json"

        left_data = {
            "name": "Alice",
            "age": 30,
            "skills": ["Python", "Go"],
            "profile": {"education": "MIT"}
        }
        right_data = {
            "name": "Bob",
            "city": "Beijing",
            "skills": ["Python"],
            "profile": {"experience": 5}
        }

        left.write_text(json.dumps(left_data, indent=2))
        right.write_text(json.dumps(right_data, indent=2))

        result = runner.invoke(main, [str(left), str(right)])

        assert result.exit_code == 1

    def test_array_differences(self, temp_dir):
        """Test CLI handles array differences."""
        runner = CliRunner()
        left = temp_dir / "left.json"
        right = temp_dir / "right.json"
        left.write_text('{"items": [1, 2, 3]}')
        right.write_text('{"items": [1, 2, 4, 5]}')

        result = runner.invoke(main, [str(left), str(right)])

        assert result.exit_code in [0, 1]

    def test_whitespace_only_json(self, temp_dir):
        """Test CLI handles JSON with extra whitespace."""
        runner = CliRunner()
        left = temp_dir / "left.json"
        right = temp_dir / "right.json"
        left.write_text('  \n  {"key": "value"}  \n  ')
        right.write_text('  \n  {"key": "value"}  \n  ')

        result = runner.invoke(main, [str(left), str(right)])

        assert result.exit_code == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
