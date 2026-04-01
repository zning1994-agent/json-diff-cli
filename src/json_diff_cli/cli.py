"""
CLI module for json-diff-cli.

Provides command-line interface using click framework for comparing JSON files.
"""

import sys
import json
from pathlib import Path
from typing import Optional, List

import click
from rich.console import Console

from . import __version__
from .differ import compare, DiffResult
from .formatter import format_terminal, format_json_patch, format_summary
from .renderer import render_diff, render_summary
from .exceptions import JsonDiffError


# Output format enum
class OutputFormat:
    """Supported output formats."""
    TERMINAL = "terminal"
    JSON_PATCH = "json-patch"
    SUMMARY = "summary"
    STATS = "stats"


# Console instance for rich output
console = Console()


def validate_file_path(path: str, name: str) -> Path:
    """
    Validate that a file path exists and is readable.
    
    Args:
        path: The file path to validate
        name: Parameter name for error messages
        
    Returns:
        Path object if valid
        
    Raises:
        click.BadParameter: If file doesn't exist or is not readable
    """
    file_path = Path(path)
    
    if not file_path.exists():
        raise click.BadParameter(f"File not found: {path}")
    
    if not file_path.is_file():
        raise click.BadParameter(f"Expected a file, got directory: {path}")
    
    if not file_path.stat().st_size >= 0:
        raise click.BadParameter(f"Cannot read file: {path}")
    
    return file_path


def load_json_file(file_path: Path) -> dict:
    """
    Load and parse a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Parsed JSON content as dictionary
        
    Raises:
        click.BadParameter: If JSON is invalid
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise click.BadParameter(f"Invalid JSON in {file_path}: {e}")
    except IOError as e:
        raise click.BadParameter(f"Cannot read {file_path}: {e}")


def resolve_ignore_paths(paths: Optional[List[str]]) -> List[str]:
    """
    Resolve and validate ignore paths from command line.
    
    Args:
        paths: List of dot-notation paths to ignore
        
    Returns:
        List of validated paths
    """
    if not paths:
        return []
    return paths


@click.command()
@click.argument('left', type=str, required=True)
@click.argument('right', type=str, required=True)
@click.option(
    '--output', '-o',
    type=click.Choice([OutputFormat.TERMINAL, OutputFormat.JSON_PATCH, OutputFormat.SUMMARY]),
    default=OutputFormat.TERMINAL,
    help='Output format (default: terminal)'
)
@click.option(
    '--color/--no-color',
    default=None,
    help='Force enable/disable color output (default: auto-detect based on terminal)'
)
@click.option(
    '--stat',
    is_flag=True,
    help='Show statistics summary alongside the diff'
)
@click.option(
    '--ignore-order',
    is_flag=True,
    help='Ignore order of array elements when comparing'
)
@click.option(
    '--ignore',
    multiple=True,
    type=str,
    help='Ignore specific paths (dot notation, e.g., "metadata.timestamp")'
)
@click.option(
    '--version',
    '-v',
    is_flag=True,
    help='Show version information'
)
@click.option(
    '--quiet', '-q',
    is_flag=True,
    help='Suppress non-essential output, only show diff'
)
@click.option(
    '--json-output',
    is_flag=True,
    help='Output raw JSON comparison result (for scripting)'
)
@click.pass_context
def main(
    ctx: click.Context,
    left: str,
    right: str,
    output: str,
    color: Optional[bool],
    stat: bool,
    ignore_order: bool,
    ignore: tuple,
    version: bool,
    quiet: bool,
    json_output: bool
) -> int:
    """
    Compare two JSON files and display differences with colorful terminal output.
    
    LEFT is the path to the left (original) JSON file.
    
    RIGHT is the path to the right (modified) JSON file.
    
    Examples:
    
      json-diff left.json right.json
    
      json-diff --output json-patch left.json right.json
    
      json-diff --ignore metadata.timestamp --ignore created_at left.json right.json
    """
    # Handle version flag
    if version:
        console.print(f"[bold]json-diff-cli[/bold] version {__version__}")
        console.print("A CLI tool for comparing JSON files with colorful output.")
        console.print(f"\nLicensed under {__license__}")
        return 0
    
    # Validate input files
    try:
        left_path = validate_file_path(left, 'LEFT')
        right_path = validate_file_path(right, 'RIGHT')
    except click.BadParameter:
        raise
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", err=True)
        return 1
    
    # Load JSON files
    try:
        left_data = load_json_file(left_path)
        right_data = load_json_file(right_path)
    except click.BadParameter:
        raise
    except Exception as e:
        console.print(f"[bold red]Error loading JSON:[/bold red] {e}", err=True)
        return 1
    
    # Perform comparison
    try:
        ignore_paths = resolve_ignore_paths(list(ignore))
        diff_result = compare(
            left_data,
            right_data,
            ignore_order=ignore_order,
            ignore_paths=ignore_paths
        )
    except JsonDiffError as e:
        console.print(f"[bold red]Comparison error:[/bold red] {e}", err=True)
        return 1
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}", err=True)
        return 1
    
    # Handle JSON output mode (for scripting)
    if json_output:
        output_json = {
            'left_file': str(left_path),
            'right_file': str(right_path),
            'differences': diff_result.to_dict(),
            'has_differences': diff_result.has_differences,
            'summary': diff_result.summary
        }
        console.print(json.dumps(output_json, indent=2))
        return 0
    
    # Determine output based on format
    exit_code = 0
    if diff_result.has_differences:
        exit_code = 1
    
    # Configure console color based on --color flag
    if color is False:
        console = Console(force_terminal=False)
    
    # Output based on format
    if output == OutputFormat.TERMINAL:
        if not quiet:
            console.print(f"\n[bold]Comparing:[/bold] {left} ↔ {right}\n")
        render_diff(diff_result, console=console, show_stat=stat)
        
    elif output == OutputFormat.JSON_PATCH:
        json_patch = format_json_patch(diff_result)
        console.print(json.dumps(json_patch, indent=2))
        
    elif output == OutputFormat.SUMMARY:
        summary = format_summary(diff_result)
        console.print(summary)
    
    # Show statistics if requested
    if stat and output != OutputFormat.TERMINAL:
        stats = render_summary(diff_result)
        console.print(stats)
    
    # Return appropriate exit code
    return exit_code


def cli_main() -> int:
    """
    Entry point for the CLI application.
    
    Returns:
        Exit code (0 for no differences, 1 for differences found)
    """
    try:
        return main()
    except click.Abort:
        return 1
    except KeyboardInterrupt:
        console.print("\n[yellow]Aborted by user[/yellow]")
        return 130
    except Exception as e:
        console.print(f"[bold red]Fatal error:[/bold red] {e}", err=True)
        return 1


if __name__ == '__main__':
    sys.exit(cli_main())
