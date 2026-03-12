"""CLI entry point for tf-module-scaffolder."""

from __future__ import annotations

import click
from rich.console import Console

from .engine import ScaffoldEngine
from .models import PROVIDER_MODULES, ModuleConfig, ModuleType, Provider
from .output.console import render_module_list, render_scaffold_result

console = Console()

# ── Reverse look-ups ──────────────────────────────────────
_PROVIDER_BY_SHORT: dict[str, Provider] = {
    p.short_name.lower(): p for p in Provider
}
_MODULE_BY_VALUE: dict[str, ModuleType] = {m.value: m for m in ModuleType}


@click.group()
@click.version_option(package_name="tf-module-scaffolder")
def cli() -> None:
    """tf-scaffold — Terraform Module Scaffolding CLI.

    Generate production-ready Terraform modules with best-practice
    structure, CI/CD, linting, and documentation out of the box.
    """


# ──────────────────────────────────────────────────────────
#  tf-scaffold list
# ──────────────────────────────────────────────────────────
@cli.command("list")
def list_modules() -> None:
    """List available module templates."""
    render_module_list(PROVIDER_MODULES)


# ──────────────────────────────────────────────────────────
#  tf-scaffold new
# ──────────────────────────────────────────────────────────
@cli.command()
@click.option(
    "-p",
    "--provider",
    "provider_name",
    type=click.Choice(["aws", "azure", "gcp"], case_sensitive=False),
    help="Cloud provider (aws / azure / gcp).",
)
@click.option(
    "-t",
    "--template",
    "template_name",
    type=str,
    help="Module template name (e.g. vpc, s3-bucket). Use 'tf-scaffold list' to see all.",
)
@click.option("-n", "--name", "module_name", type=str, help="Module name (e.g. my-vpc).")
@click.option(
    "-o",
    "--output-dir",
    type=click.Path(),
    default=".",
    help="Directory to create the module in.",
)
@click.option("-d", "--description", type=str, default=None, help="Module description.")
@click.option("-a", "--author", type=str, default=None, help="Author name.")
@click.option("--no-examples", is_flag=True, help="Skip examples directory.")
@click.option("--no-tests", is_flag=True, help="Skip tests directory.")
@click.option("--no-ci", is_flag=True, help="Skip CI workflow.")
@click.option("--no-precommit", is_flag=True, help="Skip pre-commit config.")
@click.option("--no-makefile", is_flag=True, help="Skip Makefile.")
def new(  # noqa: PLR0913
    provider_name: str | None,
    template_name: str | None,
    module_name: str | None,
    output_dir: str,
    description: str | None,
    author: str | None,
    no_examples: bool,
    no_tests: bool,
    no_ci: bool,
    no_precommit: bool,
    no_makefile: bool,
) -> None:
    """Scaffold a new Terraform module.

    Run without options for interactive mode, or supply --provider,
    --template, --name for non-interactive scaffolding.
    """
    # ── Resolve provider ───────────────────────────────────
    if provider_name is None:
        provider_name = _prompt_provider()
    provider = _PROVIDER_BY_SHORT[provider_name.lower()]

    # ── Resolve template ───────────────────────────────────
    if template_name is None:
        template_name = _prompt_template(provider)
    module_type = _resolve_module_type(template_name, provider)

    # ── Resolve name ───────────────────────────────────────
    if module_name is None:
        default = f"terraform-{provider.short_name.lower()}-{module_type.value}"
        module_name = click.prompt(
            click.style("  Module name", fg="cyan"),
            default=default,
        )

    # Build config
    config = ModuleConfig(
        name=module_name,
        provider=provider,
        module_type=module_type,
        description=description or module_type.description,
        author=author or "",
        output_dir=output_dir,
        enable_examples=not no_examples,
        enable_tests=not no_tests,
        enable_ci=not no_ci,
        enable_precommit=not no_precommit,
        enable_makefile=not no_makefile,
    )

    # Scaffold
    engine = ScaffoldEngine()
    result = engine.scaffold(config)
    render_scaffold_result(result)


# ──────────────────────────────────────────────────────────
#  tf-scaffold quickstart  — one-command shortcuts
# ──────────────────────────────────────────────────────────
@cli.command()
@click.argument(
    "preset",
    type=click.Choice(
        ["aws-vpc", "aws-s3", "azure-rg", "azure-vnet", "azure-storage", "gcp-vpc", "gcp-gcs"],
        case_sensitive=False,
    ),
)
@click.option("-n", "--name", "module_name", type=str, default=None, help="Module name.")
@click.option(
    "-o",
    "--output-dir",
    type=click.Path(),
    default=".",
    help="Directory to create the module in.",
)
def quickstart(preset: str, module_name: str | None, output_dir: str) -> None:
    """Quick-scaffold a module from a preset.

    \b
    Presets: aws-vpc, aws-s3, azure-rg, azure-vnet, azure-storage, gcp-vpc, gcp-gcs
    """
    preset_map: dict[str, tuple[Provider, ModuleType]] = {
        "aws-vpc": (Provider.AWS, ModuleType.VPC),
        "aws-s3": (Provider.AWS, ModuleType.S3_BUCKET),
        "azure-rg": (Provider.AZURE, ModuleType.RESOURCE_GROUP),
        "azure-vnet": (Provider.AZURE, ModuleType.VNET),
        "azure-storage": (Provider.AZURE, ModuleType.STORAGE_ACCOUNT),
        "gcp-vpc": (Provider.GCP, ModuleType.GCP_VPC),
        "gcp-gcs": (Provider.GCP, ModuleType.GCS_BUCKET),
    }
    provider, module_type = preset_map[preset.lower()]
    name = module_name or f"terraform-{provider.short_name.lower()}-{module_type.value}"

    config = ModuleConfig(
        name=name,
        provider=provider,
        module_type=module_type,
        description=module_type.description,
        output_dir=output_dir,
    )
    engine = ScaffoldEngine()
    result = engine.scaffold(config)
    render_scaffold_result(result)


# ──────────────────────────────────────────────────────────
#  Interactive helpers
# ──────────────────────────────────────────────────────────
def _prompt_provider() -> str:
    """Interactive provider selection."""
    console.print()
    console.print("  [bold cyan]Select a cloud provider:[/]")
    providers = list(Provider)
    for i, p in enumerate(providers, 1):
        console.print(f"    [bold]{i}.[/] {p.display_name}")

    choice = click.prompt(
        click.style("  Choice", fg="cyan"),
        type=click.IntRange(1, len(providers)),
    )
    return providers[choice - 1].short_name


def _prompt_template(provider: Provider) -> str:
    """Interactive template selection."""
    modules = PROVIDER_MODULES[provider]
    console.print()
    console.print(f"  [bold cyan]Select a module template ({provider.display_name}):[/]")
    for i, m in enumerate(modules, 1):
        console.print(f"    [bold]{i}.[/] {m.value:20s} — {m.description}")

    # Add blank option
    blank_idx = len(modules) + 1
    console.print(f"    [bold]{blank_idx}.[/] {'blank':20s} — Empty module (start from scratch)")

    choice = click.prompt(
        click.style("  Choice", fg="cyan"),
        type=click.IntRange(1, blank_idx),
    )
    if choice == blank_idx:
        return "blank"
    return modules[choice - 1].value


def _resolve_module_type(template_name: str, provider: Provider) -> ModuleType:
    """Resolve template name → ModuleType."""
    if template_name.lower() == "blank":
        return ModuleType.BLANK

    # Direct match
    if template_name in _MODULE_BY_VALUE:
        return _MODULE_BY_VALUE[template_name]

    # Try with provider prefix for GCP types
    prefixed = f"gcp-{template_name}"
    if prefixed in _MODULE_BY_VALUE:
        return _MODULE_BY_VALUE[prefixed]

    # Fuzzy search across provider's modules
    provider_modules = PROVIDER_MODULES[provider]
    for m in provider_modules:
        if template_name.lower() in m.value.lower():
            return m

    raise click.ClickException(
        f"Unknown template '{template_name}' for {provider.display_name}. "
        f"Run 'tf-scaffold list' to see available templates."
    )
