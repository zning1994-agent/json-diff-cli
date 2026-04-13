"""Rich-based terminal renderer."""

from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from .differ import DiffResult


def render_diff(result: DiffResult) -> str:
    """
    Render diff result for terminal output.
    
    Args:
        result: The diff result to render
    
    Returns:
        Rendered string representation
    """
    if not result.has_changes():
        return "[green]✓ No differences found[/green]"
    
    lines = []
    lines.append("[bold]=== JSON Diff Results ===[/bold]\n")
    
    # Additions
    additions = result.additions
    if additions:
        lines.append("[bold green]📍 Additions:[/bold green]")
        for path, value in additions.items():
            lines.append(f"  {format_path(path)}: [green]{format_value(value)}[/green]")
        lines.append("")
    
    # Deletions
    deletions = result.deletions
    if deletions:
        lines.append("[bold red]📍 Deletions:[/bold red]")
        for path, value in deletions.items():
            lines.append(f"  {format_path(path)}: [red]{format_value(value)}[/red]")
        lines.append("")
    
    # Modifications
    modifications = result.modifications
    if modifications:
        lines.append("[bold yellow]📍 Modifications:[/bold yellow]")
        for path, change in modifications.items():
            old_val = change.get('old_value', 'N/A')
            new_val = change.get('new_value', 'N/A')
            lines.append(f"  {format_path(path)}:")
            lines.append(f"    [red]- {format_value(old_val)}[/red]")
            lines.append(f"    [green]+ {format_value(new_val)}[/green]")
        lines.append("")
    
    return "\n".join(lines)


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
    
    for path, value in result.additions.items():
        table.add_row("Addition", format_path(path), format_value(value))
    
    for path, value in result.deletions.items():
        table.add_row("Deletion", format_path(path), format_value(value))
    
    for path, change in result.modifications.items():
        old_val = change.get('old_value', 'N/A')
        new_val = change.get('new_value', 'N/A')
        table.add_row(
            "Modification",
            format_path(path),
            f"- {old_val} → + {new_val}"
        )
    
    return table


def render_tree(data: dict, title: str = "JSON Structure") -> Tree:
    """
    Render JSON data as a rich tree.
    
    Args:
        data: The JSON data to render
        title: Tree title
    
    Returns:
        Rich Tree object
    """
    tree = Tree(title)
    
    def add_nodes(parent, data, key=None):
        if isinstance(data, dict):
            for k, v in data.items():
                if key is None:
                    add_nodes(parent, v, k)
                else:
                    branch = parent.add(f"[cyan]{k}[/cyan]")
                    add_nodes(branch, v, k)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                branch = parent.add(f"[yellow][{i}][/yellow]")
                add_nodes(branch, item)
        else:
            if key is not None:
                parent.add(f"[white]{key}[/white]: [green]{format_value(data)}[/green]")
    
    add_nodes(tree, data)
    return tree


def format_path(path: str) -> str:
    """Format a deepdiff path for display."""
    # Convert "root['key']" to "key" or "root.key"
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
