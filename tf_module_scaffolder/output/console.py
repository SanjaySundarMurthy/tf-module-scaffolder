"""Rich console output for scaffold results."""

from __future__ import annotations

import io
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from ..models import ScaffoldResult


def _ensure_utf8() -> None:
    """Wrap stdout with UTF-8 to support Rich emoji on Windows."""
    if (
        hasattr(sys.stdout, "buffer")
        and not isinstance(sys.stdout, io.TextIOWrapper)
        or (isinstance(sys.stdout, io.TextIOWrapper) and sys.stdout.encoding != "utf-8")
    ):
        try:
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer, encoding="utf-8", errors="replace"
            )
        except Exception:
            pass


def render_scaffold_result(result: ScaffoldResult) -> None:
    """Display scaffold result in a beautiful Rich layout."""
    _ensure_utf8()
    console = Console()
    console.print()

    # ── Header ──────────────────────────────────────────────
    header = Text()
    header.append("  Terraform Module Scaffolded Successfully!", style="bold green")
    console.print(Panel(header, border_style="green", padding=(1, 2)))

    # ── Summary table ───────────────────────────────────────
    table = Table(show_header=False, border_style="cyan", padding=(0, 2))
    table.add_column("Key", style="bold white", min_width=18)
    table.add_column("Value", style="cyan")
    table.add_row("Module", result.module_name)
    table.add_row("Provider", result.provider.upper())
    table.add_row("Type", result.module_type)
    table.add_row("Location", str(result.module_path))
    table.add_row("Files Created", str(len(result.files_created)))
    table.add_row("Directories", str(len(result.directories_created)))
    table.add_row("Total Lines", f"{result.total_lines:,}")
    console.print(table)
    console.print()

    # ── File tree ───────────────────────────────────────────
    tree = Tree(
        f"[bold yellow] {result.module_name}/[/]",
        guide_style="dim",
    )
    _build_tree(tree, result)
    console.print(Panel(tree, title="[bold]Module Structure[/]", border_style="yellow"))
    console.print()

    # ── Next steps ──────────────────────────────────────────
    next_steps = Table(show_header=False, border_style="blue", padding=(0, 1))
    next_steps.add_column("Step", style="bold white", min_width=4)
    next_steps.add_column("Command", style="green")
    next_steps.add_row("1.", f"cd {result.module_path}")
    next_steps.add_row("2.", "terraform init")
    next_steps.add_row("3.", "terraform validate")
    next_steps.add_row("4.", "terraform plan")
    console.print(
        Panel(next_steps, title="[bold] Next Steps[/]", border_style="blue")
    )
    console.print()


def render_module_list(providers: dict) -> None:
    """Render available module templates in a Rich table."""
    _ensure_utf8()
    console = Console()
    console.print()

    provider_styles = {
        "AWS": ("bold yellow", "yellow"),
        "Azure": ("bold blue", "blue"),
        "GCP": ("bold red", "red"),
    }

    for provider, modules in providers.items():
        display = provider.display_name
        title_style, border_style = provider_styles.get(
            display, ("bold white", "white")
        )

        table = Table(
            title=f"  {display} Modules",
            title_style=title_style,
            border_style=border_style,
            show_lines=True,
        )
        table.add_column("Template", style="bold", min_width=20)
        table.add_column("Description", min_width=40)

        for mod in modules:
            table.add_row(mod.value, mod.description)

        console.print(table)
        console.print()


def _build_tree(tree: Tree, result: ScaffoldResult) -> None:
    """Build a nested tree structure from flat file list."""
    # Group files by directory
    dir_map: dict[str, list[str]] = {}
    for f in sorted(result.files_created):
        parts = f.replace("\\", "/").split("/")
        if len(parts) == 1:
            dir_map.setdefault(".", []).append(parts[0])
        else:
            dir_path = "/".join(parts[:-1])
            dir_map.setdefault(dir_path, []).append(parts[-1])

    # Add root files
    for f in dir_map.get(".", []):
        icon = _file_icon(f)
        tree.add(f"[green]{icon} {f}[/]")

    # Add subdirectories
    for dir_path in sorted(d for d in dir_map if d != "."):
        branch = tree
        parts = dir_path.split("/")
        for part in parts:
            # Find or create branch
            existing = None
            for child in branch.children:
                label_text = child.label
                if hasattr(label_text, "plain"):
                    label_text = label_text.plain
                if part in str(label_text):
                    existing = child
                    break
            if existing:
                branch = existing
            else:
                branch = branch.add(f"[bold yellow] {part}/[/]")

        # Add files under this directory
        for f in dir_map[dir_path]:
            icon = _file_icon(f)
            branch.add(f"[green]{icon} {f}[/]")


def _file_icon(filename: str) -> str:
    """Return an icon for the file type."""
    icon_map = {
        ".tf": "",
        ".yml": "",
        ".yaml": "",
        ".md": "",
        ".hcl": "",
        "Makefile": "",
    }
    for ext, icon in icon_map.items():
        if filename.endswith(ext) or filename == ext:
            return icon
    return ""
