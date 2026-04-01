"""CLI entry point for json-diff-cli."""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from .differ import compare, DiffResult
from .exceptions import JsonDiffError, FileReadError, InvalidJsonError
from .formatter import OutputFormat, format_diff


console = Console()


@click.command()
@click.argument('left', type=click.Path(exists=True, path_type=Path))
@click.argument('right', type=click.Path(exists=True, path_type=Path))
@click.option(
    '--output', '-o',
    type=click.Choice(['terminal', 'json-patch', 'summary'], case_sensitive=False),
    default='terminal',
    help='Output format (default: terminal)'
)
@click.option(
    '--color/--no-color',
    default=None,
    help='Force enable/disable color output [default: auto-detect]'
)
@click.option(
    '--stat', '-s',
    is_flag=True,
    help='Show statistics summary'
)
@click.version_option(version='0.1.0', prog_name='json-diff')
def main(
    left: Path,
    right: Path,
    output: str,
    color: Optional[bool],
    stat: bool
) -> int:
    """
    Compare two JSON files and display differences.

    LEFT: Path to the left (original) JSON file
    RIGHT: Path to the right (modified) JSON file
    """
    try:
        # Determine output format
        fmt = OutputFormat(output.lower())
        
        # Compare files
        result = compare(left, right)
        
        # Configure console color
        if color is False:
            console.color = False
        elif color is True:
            console.color = True
        # None means auto-detect based on terminal
        
        # Format and output
        output_text = format_diff(result, fmt)
        
        if fmt == OutputFormat.TERMINAL:
            console.print(output_text)
        else:
            console.print(output_text, no_color=color is False)
        
        # Show statistics if requested
        if stat:
            summary = result.summary
            console.print(f"\n[bold]Statistics:[/bold]")
            console.print(f"  Additions: {summary['additions']}")
            console.print(f"  Deletions: {summary['deletions']}")
            console.print(f"  Modifications: {summary['modifications']}")
            console.print(f"  Total changes: {summary['total']}")
        
        # Exit code based on differences
        if result.has_differences:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except FileReadError as e:
        console.print(f"[red]Error:[/red] {e}", err=True)
        sys.exit(2)
    except InvalidJsonError as e:
        console.print(f"[red]Error:[/red] {e}", err=True)
        sys.exit(3)
    except JsonDiffError as e:
        console.print(f"[red]Error:[/red] {e}", err=True)
        sys.exit(4)


if __name__ == '__main__':
    main()
