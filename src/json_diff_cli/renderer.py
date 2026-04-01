"""Rich-based terminal renderer for JSON diff output.

This module provides colorful terminal output using the rich library.
It supports two main rendering modes:
- render_diff(): Renders a flat list of differences with color coding
- render_tree(): Renders differences in a hierarchical tree structure
"""

from typing import Optional, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from rich.console import Console, ConsoleOptions, RenderResult
from rich.text import Text
from rich.table import Table
from rich.tree import Tree
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markup import escape
from rich.style import Style

from . import DiffResult


class ChangeType(Enum):
    """Types of differences."""
    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"


@dataclass
class StyledChange:
    """A styled change entry."""
    path: str
    change_type: ChangeType
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None


class DiffTheme:
    """Color theme for diff rendering."""
    
    # Primary colors
    ADDED_COLOR = "green"
    REMOVED_COLOR = "red"
    CHANGED_COLOR = "yellow"
    
    # Secondary colors
    PATH_COLOR = "cyan"
    HEADER_COLOR = "bold blue"
    SUMMARY_COLOR = "bold white"
    
    # Value colors
    OLD_VALUE_COLOR = "red dim"
    NEW_VALUE_COLOR = "green dim"
    STRING_COLOR = "magenta"
    NUMBER_COLOR = "cyan"
    BOOL_COLOR = "yellow"
    NULL_COLOR = "dim"


class DiffRenderer:
    """Renderer for displaying JSON differences using rich.
    
    This class handles the rendering of DiffResult objects to the terminal
    with colorful, readable output.
    
    Attributes:
        console: Rich Console instance for output
        theme: DiffTheme for color configuration
        show_values: Whether to show old/new values for changes
        max_depth: Maximum depth for tree rendering (0 = unlimited)
    """
    
    def __init__(
        self,
        console: Optional[Console] = None,
        theme: Optional[DiffTheme] = None,
        show_values: bool = True,
        max_depth: int = 0
    ):
        """Initialize the diff renderer.
        
        Args:
            console: Rich Console instance (creates new if not provided)
            theme: DiffTheme for colors (uses default if not provided)
            show_values: Whether to display old/new values for changes
            max_depth: Maximum tree depth (0 = unlimited)
        """
        self.console = console or Console()
        self.theme = theme or DiffTheme()
        self.show_values = show_values
        self.max_depth = max_depth
    
    def _get_change_symbol(self, change_type: ChangeType) -> str:
        """Get the symbol for a change type.
        
        Args:
            change_type: Type of change
            
        Returns:
            Unicode symbol for the change type
        """
        symbols = {
            ChangeType.ADDED: "+",
            ChangeType.REMOVED: "-",
            ChangeType.CHANGED: "~",
        }
        return symbols.get(change_type, "?")
    
    def _get_change_style(self, change_type: ChangeType) -> Style:
        """Get the rich Style for a change type.
        
        Args:
            change_type: Type of change
            
        Returns:
            Rich Style object
        """
        color_map = {
            ChangeType.ADDED: self.theme.ADDED_COLOR,
            ChangeType.REMOVED: self.theme.REMOVED_COLOR,
            ChangeType.CHANGED: self.theme.CHANGED_COLOR,
        }
        return Style(color=color_map.get(change_type), bold=True)
    
    def _format_path(self, path: str) -> Text:
        """Format a path string with styling.
        
        Args:
            path: JSON path string
            
        Returns:
            Styled Text object
        """
        return Text(path, style=self.theme.PATH_COLOR)
    
    def _format_value(self, value: Any) -> Text:
        """Format a value with appropriate color.
        
        Args:
            value: The value to format
            
        Returns:
            Styled Text object
        """
        if value is None:
            return Text("null", style=self.theme.NULL_COLOR)
        elif isinstance(value, bool):
            return Text(str(value), style=self.theme.BOOL_COLOR)
        elif isinstance(value, (int, float)):
            return Text(str(value), style=self.theme.NUMBER_COLOR)
        elif isinstance(value, str):
            display = f'"{value}"' if len(value) <= 50 else f'"{value[:47]}..."'
            return Text(display, style=self.theme.STRING_COLOR)
        else:
            return Text(str(value), style="")
    
    def _create_change_row(self, change: StyledChange) -> Tuple[Text, ...]:
        """Create a table row for a single change.
        
        Args:
            change: StyledChange to render
            
        Returns:
            Tuple of Text objects for the table row
        """
        symbol = Text(
            f" {self._get_change_symbol(change.change_type)} ",
            style=self._get_change_style(change.change_type)
        )
        path = self._format_path(change.path)
        
        if self.show_values and change.change_type == ChangeType.CHANGED:
            old_val = self._format_value(change.old_value)
            arrow = Text(" → ", style="dim")
            new_val = self._format_value(change.new_value)
            return (symbol, path, old_val, arrow, new_val)
        elif self.show_values and change.change_type == ChangeType.ADDED:
            value = self._format_value(change.new_value)
            return (symbol, path, Text(""), Text(""), value)
        elif self.show_values and change.change_type == ChangeType.REMOVED:
            value = self._format_value(change.old_value)
            return (symbol, path, value, Text(""), Text(""))
        else:
            return (symbol, path)
    
    def _build_changes_list(self, diff_result: DiffResult) -> List[StyledChange]:
        """Build a list of styled changes from diff result.
        
        Args:
            diff_result: The diff result to process
            
        Returns:
            List of StyledChange objects
        """
        changes = []
        
        for path in sorted(diff_result.added):
            diff_value = diff_result.differences.get('dictionary_item_added', {})
            new_value = diff_value.get(path) if isinstance(diff_value, dict) else None
            changes.append(StyledChange(
                path=path,
                change_type=ChangeType.ADDED,
                new_value=new_value
            ))
        
        for path in sorted(diff_result.removed):
            diff_value = diff_result.differences.get('dictionary_item_removed', {})
            old_value = diff_value.get(path) if isinstance(diff_value, dict) else None
            changes.append(StyledChange(
                path=path,
                change_type=ChangeType.REMOVED,
                old_value=old_value
            ))
        
        for path in sorted(diff_result.changed):
            diff_value = diff_result.differences.get('values_changed', {})
            change_data = diff_value.get(path, {})
            if isinstance(change_data, dict):
                old_value = change_data.get('old_value')
                new_value = change_data.get('new_value')
            else:
                old_value = None
                new_value = None
            changes.append(StyledChange(
                path=path,
                change_type=ChangeType.CHANGED,
                old_value=old_value,
                new_value=new_value
            ))
        
        return changes
    
    def render_diff(self, diff_result: DiffResult) -> None:
        """Render differences as a formatted table.
        
        This method renders the differences using a rich Table with
        color-coded rows for additions, deletions, and modifications.
        
        Args:
            diff_result: The DiffResult to render
        """
        if not diff_result.has_differences:
            self._render_no_diff()
            return
        
        # Header
        self.console.print()
        header = Text()
        header.append(f"Comparing: ", style=self.theme.HEADER_COLOR)
        header.append(diff_result.left_path, style="bold white")
        header.append("  vs  ", style="dim")
        header.append(diff_result.right_path, style="bold white")
        self.console.print(header)
        self.console.print()
        
        # Build table
        table = Table(
            show_header=True,
            header_style="bold",
            border_style="dim",
            pad_edge=False,
            box=None,
        )
        
        table.add_column(" ", width=3, no_wrap=True)
        table.add_column("Path", style=self.theme.PATH_COLOR)
        
        if self.show_values:
            table.add_column("Old Value", style=self.theme.OLD_VALUE_COLOR)
            table.add_column("", width=3)
            table.add_column("New Value", style=self.theme.NEW_VALUE_COLOR)
        
        # Add rows
        changes = self._build_changes_list(diff_result)
        for change in changes:
            row = self._create_change_row(change)
            table.add_row(*row)
        
        self.console.print(table)
        
        # Summary
        self._render_summary(diff_result)
    
    def _render_no_diff(self) -> None:
        """Render message when no differences found."""
        panel = Panel(
            "[bold green]✓[/bold green] No differences found!",
            title="Result",
            border_style="green",
            padding=(1, 2),
        )
        self.console.print(panel)
    
    def _render_summary(self, diff_result: DiffResult) -> None:
        """Render a summary of changes.
        
        Args:
            diff_result: The diff result to summarize
        """
        self.console.print()
        
        summary_parts = []
        
        if diff_result.added:
            count = len(diff_result.added)
            summary_parts.append(
                f"[{self.theme.ADDED_COLOR}]{count} addition{'s' if count > 1 else ''}[/]"
            )
        
        if diff_result.removed:
            count = len(diff_result.removed)
            summary_parts.append(
                f"[{self.theme.REMOVED_COLOR}]{count} removal{'s' if count > 1 else ''}[/]"
            )
        
        if diff_result.changed:
            count = len(diff_result.changed)
            summary_parts.append(
                f"[{self.theme.CHANGED_COLOR}]{count} modification{'s' if count > 1 else ''}[/]"
            )
        
        summary_text = " | ".join(summary_parts) if summary_parts else "No changes"
        
        self.console.print(
            f"[dim]Total:[/dim] {summary_text}",
            justify="center"
        )
        self.console.print()
    
    def _parse_path_to_tree(self, path: str) -> List[str]:
        """Parse a JSON path into tree node names.
        
        Args:
            path: DeepDiff style path like "root['key']['subkey']"
            
        Returns:
            List of node names for tree hierarchy
        """
        import re
        
        parts = re.findall(r"\['([^']+)'\]|\[(\d+)\]", path)
        result = []
        
        for match in parts:
            for group in match:
                if group:
                    result.append(group)
        
        return result if result else [path]
    
    def _create_value_label(self, value: Any) -> str:
        """Create a label for a value in tree view.
        
        Args:
            value: The value to label
            
        Returns:
            Formatted label string
        """
        if value is None:
            return "[dim]null[/dim]"
        elif isinstance(value, bool):
            return f"[yellow]{value}[/yellow]"
        elif isinstance(value, (int, float)):
            return f"[cyan]{value}[/cyan]"
        elif isinstance(value, str):
            display = f'"{value[:30]}"' if len(value) <= 30 else f'"{value[:27]}..."'
            return f"[magenta]{display}[/magenta]"
        else:
            return str(value)
    
    def render_tree(self, diff_result: DiffResult) -> None:
        """Render differences as a hierarchical tree structure.
        
        This method renders the differences using a rich Tree, organizing
        changes by their JSON path hierarchy for better visualization of
        nested structures.
        
        Args:
            diff_result: The DiffResult to render
        """
        if not diff_result.has_differences:
            self._render_no_diff()
            return
        
        # Header
        self.console.print()
        header = Text()
        header.append(f"Comparing: ", style=self.theme.HEADER_COLOR)
        header.append(diff_result.left_path, style="bold white")
        header.append("  vs  ", style="dim")
        header.append(diff_result.right_path, style="bold white")
        self.console.print(header)
        self.console.print()
        
        # Group changes by root key
        changes_by_root: dict = {
            ChangeType.ADDED: {},
            ChangeType.REMOVED: {},
            ChangeType.CHANGED: {},
        }
        
        changes = self._build_changes_list(diff_result)
        
        for change in changes:
            parts = self._parse_path_to_tree(change.path)
            if not parts:
                continue
            
            root = parts[0]
            rest_path = parts[1:] if len(parts) > 1 else []
            
            if root not in changes_by_root[change.change_type]:
                changes_by_root[change.change_type][root] = []
            
            changes_by_root[change.change_type][root].append({
                'full_path': parts,
                'rest_path': rest_path,
                'change': change
            })
        
        # Build and render tree
        if changes_by_root[ChangeType.ADDED]:
            added_tree = Tree(
                "[green]+ ADDITIONS[/green]",
                guide_style="green dim"
            )
            self._build_tree_branch(added_tree, changes_by_root[ChangeType.ADDED])
            self.console.print(added_tree)
            self.console.print()
        
        if changes_by_root[ChangeType.REMOVED]:
            removed_tree = Tree(
                "[red]- DELETIONS[/red]",
                guide_style="red dim"
            )
            self._build_tree_branch(removed_tree, changes_by_root[ChangeType.REMOVED])
            self.console.print(removed_tree)
            self.console.print()
        
        if changes_by_root[ChangeType.CHANGED]:
            changed_tree = Tree(
                "[yellow]~ MODIFICATIONS[/yellow]",
                guide_style="yellow dim"
            )
            self._build_tree_branch(changed_tree, changes_by_root[ChangeType.CHANGED])
            self.console.print(changed_tree)
            self.console.print()
        
        # Summary
        self._render_summary(diff_result)
    
    def _build_tree_branch(
        self,
        tree: Tree,
        changes: dict,
        prefix: str = ""
    ) -> None:
        """Build a tree branch recursively.
        
        Args:
            tree: The parent Tree node
            changes: Dictionary of changes by path
            prefix: Current path prefix for depth tracking
        """
        for key in sorted(changes.keys()):
            items = changes[key]
            
            if all(item['rest_path'] == [] for item in items):
                # Leaf node
                for item in items:
                    change = item['change']
                    style = self._get_change_style(change.change_type)
                    symbol = self._get_change_symbol(change.change_type)
                    
                    if self.show_values:
                        if change.change_type == ChangeType.ADDED:
                            label = f"{symbol} {key} = {self._create_value_label(change.new_value)}"
                        elif change.change_type == ChangeType.REMOVED:
                            label = f"{symbol} {key} = {self._create_value_label(change.old_value)}"
                        else:
                            old_display = self._create_value_label(change.old_value)
                            new_display = self._create_value_label(change.new_value)
                            label = f"{symbol} {key}: {old_display} → {new_display}"
                    else:
                        label = f"{symbol} {key}"
                    
                    tree.add(label, style=style)
            else:
                # Branch node - need to further split
                sub_tree = tree.add(f"[bold]{key}[/bold]")
                sub_changes: dict = {}
                
                for item in items:
                    rest = item['rest_path']
                    if rest:
                        next_key = rest[0]
                        remaining = rest[1:]
                        if next_key not in sub_changes:
                            sub_changes[next_key] = []
                        sub_changes[next_key].append({
                            'rest_path': remaining,
                            'change': item['change']
                        })
                
                if sub_changes:
                    self._build_sub_tree(sub_tree, sub_changes)


# Module-level convenience functions

_default_renderer: Optional[DiffRenderer] = None


def get_renderer(
    console: Optional[Console] = None,
    theme: Optional[DiffTheme] = None,
    show_values: bool = True,
    max_depth: int = 0
) -> DiffRenderer:
    """Get or create a default renderer instance.
    
    Args:
        console: Rich Console instance
        theme: DiffTheme for colors
        show_values: Whether to show values
        max_depth: Maximum tree depth
        
    Returns:
        DiffRenderer instance
    """
    global _default_renderer
    
    if console is not None or theme is not None:
        return DiffRenderer(
            console=console,
            theme=theme,
            show_values=show_values,
            max_depth=max_depth
        )
    
    if _default_renderer is None:
        _default_renderer = DiffRenderer(
            show_values=show_values,
            max_depth=max_depth
        )
    
    return _default_renderer


def render_diff(diff_result: DiffResult, **kwargs) -> None:
    """Render differences as a formatted table (convenience function).
    
    This is the main entry point for rendering differences in table format.
    
    Args:
        diff_result: The DiffResult to render
        **kwargs: Additional arguments passed to DiffRenderer
        
    Example:
        >>> from json_diff_cli import compare
        >>> from json_diff_cli.renderer import render_diff
        >>> result = compare("left.json", "right.json")
        >>> render_diff(result)
    """
    renderer = get_renderer(**kwargs)
    renderer.render_diff(diff_result)


def render_tree(diff_result: DiffResult, **kwargs) -> None:
    """Render differences as a hierarchical tree (convenience function).
    
    This is the main entry point for rendering differences in tree format.
    
    Args:
        diff_result: The DiffResult to render
        **kwargs: Additional arguments passed to DiffRenderer
        
    Example:
        >>> from json_diff_cli import compare
        >>> from json_diff_cli.renderer import render_tree
        >>> result = compare("left.json", "right.json")
        >>> render_tree(result)
    """
    renderer = get_renderer(**kwargs)
    renderer.render_tree(diff_result)
