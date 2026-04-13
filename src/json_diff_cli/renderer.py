"""Rich-based terminal renderer."""

import enum
from io import StringIO
from typing import Any, Optional, Set

from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from .differ import DiffResult


class ChangeType(enum.Enum):
    """Type of difference change."""
    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"


class DiffTheme:
    """Color theme for diff rendering."""

    ADDED_COLOR = "green"
    REMOVED_COLOR = "red"
    CHANGED_COLOR = "yellow"
    PATH_COLOR = "cyan"

    def __init__(self,
                 added_color: str = "green",
                 removed_color: str = "red",
                 changed_color: str = "yellow",
                 path_color: str = "cyan"):
        self.ADDED_COLOR = added_color
        self.REMOVED_COLOR = removed_color
        self.CHANGED_COLOR = changed_color
        self.PATH_COLOR = path_color


class DiffRenderer:
    """Rich-based diff renderer with theme support."""

    def __init__(
        self,
        console: Optional[Console] = None,
        theme: Optional[DiffTheme] = None,
        show_values: bool = True,
        max_depth: int = 0
    ):
        self.console = console or Console(file=StringIO())
        self.theme = theme or DiffTheme()
        self.show_values = show_values
        self.max_depth = max_depth

    def _get_change_symbol(self, change_type: ChangeType) -> str:
        """Get the symbol for a change type."""
        symbols = {
            ChangeType.ADDED: "+",
            ChangeType.REMOVED: "-",
            ChangeType.CHANGED: "~"
        }
        return symbols.get(change_type, "?")

    def _get_change_style(self, change_type: ChangeType) -> str:
        """Get the rich style for a change type."""
        styles = {
            ChangeType.ADDED: self.theme.ADDED_COLOR,
            ChangeType.REMOVED: self.theme.REMOVED_COLOR,
            ChangeType.CHANGED: self.theme.CHANGED_COLOR
        }
        return styles.get(change_type, "white")

    def _format_value(self, value: Any) -> str:
        """Format a value for display."""
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "True" if value else "False"
        elif isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, (list, dict)):
            s = str(value)
            if len(s) > 50:
                return s[:47] + "..."
            return s
        else:
            return str(value)

    def _parse_path_to_tree(self, path: str) -> list:
        """Parse a deepdiff path into a list of parts."""
        path = path.replace('root', '')
        path = path.replace("['", '/')
        path = path.replace("']", '')
        path = path.replace('[', '/')
        path = path.replace(']', '')

        if path.startswith('/'):
            path = path[1:]

        return [p for p in path.split('/') if p]

    def render_diff(self, result: DiffResult) -> None:
        """Render diff result to console."""
        if not result.has_differences:
            self.console.print("[green]✓ No differences found[/green]")
            return

        left = str(result.left_path) if result.left_path else 'N/A'
        right = str(result.right_path) if result.right_path else 'N/A'
        self.console.print(f"[bold]Comparing {left} → {right}[/bold]\n")

        additions = result.additions
        deletions = result.deletions
        modifications = result.modifications

        if additions:
            self.console.print(f"[bold green]📍 ADDITIONS ({len(additions)}):[/bold green]")
            for path, value in additions.items():
                p = format_path(str(path))
                v = self._format_value(value) if value is not None else ""
                if v:
                    self.console.print(f"  + {p}: [green]{v}[/green]")
                else:
                    self.console.print(f"  + {p}")
            self.console.print("")

        if deletions:
            self.console.print(f"[bold red]📍 REMOVED ({len(deletions)}):[/bold red]")
            for path, value in deletions.items():
                p = format_path(str(path))
                v = self._format_value(value) if value is not None else ""
                if v:
                    self.console.print(f"  - {p}: [red]{v}[/red]")
                else:
                    self.console.print(f"  - {p}")
            self.console.print("")

        if modifications:
            self.console.print(f"[bold yellow]📍 MODIFICATIONS ({len(modifications)}):[/bold yellow]")
            for path, change in modifications.items():
                p = format_path(str(path))
                old_v = self._format_value(change.get('old_value', 'N/A'))
                new_v = self._format_value(change.get('new_value', 'N/A'))
                self.console.print(f"  ~ {p}:")
                self.console.print(f"    [red]- {old_v}[/red]")
                self.console.print(f"    [green]+ {new_v}[/green]")
            self.console.print("")

    def render_tree(self, result: DiffResult) -> None:
        """Render diff result as a tree to console."""
        if not result.has_differences:
            self.console.print("[green]✓ No differences found[/green]")
            return

        additions = result.additions
        deletions = result.deletions
        modifications = result.modifications

        left = str(result.left_path) if result.left_path else 'N/A'
        right = str(result.right_path) if result.right_path else 'N/A'
        self.console.print(f"[bold]Comparing {left} → {right}[/bold]\n")

        if additions:
            self.console.print("[bold green]📍 ADDITIONS:[/bold green]")
            for path in additions:
                self.console.print(f"  + {format_path(str(path))}")
            self.console.print("")

        if deletions:
            self.console.print("[bold red]📍 REMOVED:[/bold red]")
            for path in deletions:
                self.console.print(f"  - {format_path(str(path))}")
            self.console.print("")

        if modifications:
            self.console.print("[bold yellow]📍 MODIFICATIONS:[/bold yellow]")
            for path in modifications:
                self.console.print(f"  ~ {format_path(str(path))}")
            self.console.print("")


def render_diff(result: DiffResult, console: Optional[Console] = None, show_values: bool = True) -> str:
    """
    Render diff result to console and return as string (module-level function).

    Args:
        result: The DiffResult to render
        console: Optional Console instance
        show_values: Whether to show values

    Returns:
        The rendered diff as string
    """
    from io import StringIO
    if console is None:
        c = Console(file=StringIO())
        renderer = DiffRenderer(console=c, show_values=show_values)
        renderer.render_diff(result)
        return c.file.getvalue()
    else:
        renderer = DiffRenderer(console=console, show_values=show_values)
        renderer.render_diff(result)
        return ""


def render_tree(result: DiffResult, console: Optional[Console] = None) -> None:
    """
    Render diff result as tree to console (module-level function).

    Args:
        result: The DiffResult to render
        console: Optional Console instance
    """
    c = console or Console()
    renderer = DiffRenderer(console=c)
    renderer.render_tree(result)


def render_diff_table(result: DiffResult) -> Table:
    """
    Render diff result as a rich table.

    Args:
        result: The diff result to render

    Returns:
        Rich Table object
    """
    table = Table(title="JSON Diff Results")

    table.add_column("Type", style="bold")
    table.add_column("Path", style="cyan")
    table.add_column("Value", style="white")

    diff = getattr(result, '_differences', {})
    additions = getattr(result, 'added', set())
    removals = getattr(result, 'removed', set())
    changes = getattr(result, 'changed', set())

    for path in additions:
        p = format_path(str(path))
        diff_data = diff.get('dictionary_item_added', {}).get(str(path), "")
        table.add_row("Addition", p, format_value(diff_data))

    for path in removals:
        p = format_path(str(path))
        table.add_row("Removal", p, "")

    for path in changes:
        p = format_path(str(path))
        vals = diff.get('values_changed', {}).get(str(path), {})
        table.add_row("Modification", p, f"- {vals.get('old_value')} → + {vals.get('new_value')}")

    return table


def format_path(path: str) -> str:
    """Format a deepdiff path for display."""
    path = path.replace('root', '')
    path = path.replace("['", '.')
    path = path.replace("']", '')
    path = path.replace('[', '.')
    path = path.replace(']', '')

    if path.startswith('.'):
        path = path[1:]

    return path or '/'


def format_value(value: Any) -> str:
    """Format a value for display."""
    if value is None:
        return "null"
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, str):
        if len(value) > 50:
            return f'"{value[:47]}..."'
        return f'"{value}"'
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, (list, dict)):
        s = str(value)
        if len(s) > 50:
            return s[:47] + "..."
        return s
    else:
        return str(value)
