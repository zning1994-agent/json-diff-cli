"""CLI entry point for json-diff-cli."""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from . import DiffResult, compare, OutputFormat
from .formatter import format_diff
from .renderer import render_diff, render_tree, DiffRenderer
from .exceptions import JsonDiffError, FileReadError, InvalidJsonError


console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="json-diff")
def cli():
    """Compare two JSON files and display differences.
    
    A CLI tool for comparing JSON files with colorful terminal output.
    Supports deep comparison of nested structures with additions,
    deletions, and modifications highlighted.
    """
    pass


@cli.command()
@click.argument("left", type=click.Path(exists=True))
@click.argument("right", type=click.Path(exists=True))
@click.option(
    "--output", "-o",
    type=click.Choice(["terminal", "json-patch", "summary"], case_sensitive=False),
    default="terminal",
    help="Output format"
)
@click.option("--tree", "-t", is_flag=True, help="Render as hierarchical tree")
@click.option("--no-color", is_flag=True, help="Disable color output")
@click.option("--no-values", is_flag=True, help="Hide old/new values")
@click.option("--json", "json_output", is_flag=True, help="Output raw JSON")
def diff(
    left: str,
    right: str,
    output: str,
    tree: bool,
    no_color: bool,
    no_values: bool,
    json_output: bool
):
    """Compare two JSON files and display differences.
    
    LEFT: Path to the left (original) JSON file
    
    RIGHT: Path to the right (modified) JSON file
    """
    try:
        result = compare(left, right)
        
        if not result.has_differences:
            console.print("[green]✓ Files are identical![/green]")
            sys.exit(0)
        
        if output == "json-patch" or json_output:
            fmt = OutputFormat.JSON_PATCH if not json_output else OutputFormat.JSON_PATCH
            output_str = format_diff(result, fmt)
            console.print(output_str)
        elif output == "summary":
            console.print(format_diff(result, OutputFormat.SUMMARY))
        elif tree:
            renderer = DiffRenderer(show_values=not no_values)
            renderer.render_tree(result)
        else:
            renderer = DiffRenderer(show_values=not no_values)
            renderer.render_diff(result)
        
        sys.exit(1 if result.has_differences else 0)
        
    except FileReadError as e:
        console.print(f"[red]Error:[/red] {e}", err=True)
        sys.exit(2)
    except InvalidJsonError as e:
        console.print(f"[red]Error:[/red] {e}", err=True)
        sys.exit(3)
    except JsonDiffError as e:
        console.print(f"[red]Error:[/red] {e}", err=True)
        sys.exit(4)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}", err=True)
        sys.exit(5)


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
