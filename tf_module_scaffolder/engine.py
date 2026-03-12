"""Scaffold engine — generates Terraform module files from templates."""

from __future__ import annotations

from pathlib import Path

from jinja2 import BaseLoader, Environment

from .models import (
    ModuleConfig,
    ModuleType,
    Provider,
    ScaffoldResult,
    TerraformOutput,
    TerraformVariable,
)
from .templates.definitions import MODULE_DEFINITIONS
from .templates.hcl import (
    AWS_S3_MAIN,
    AWS_VPC_MAIN,
    AZURE_RG_MAIN,
    AZURE_STORAGE_MAIN,
    AZURE_VNET_MAIN,
    BLANK_MAIN,
    BLANK_OUTPUTS,
    BLANK_VARIABLES,
    CI_GITHUB_ACTIONS,
    EXAMPLE_MAIN,
    GCP_GCS_MAIN,
    GCP_VPC_MAIN,
    MAKEFILE,
    MODULE_README,
    PRECOMMIT_CONFIG,
    PROVIDER_AWS,
    PROVIDER_AZURE,
    PROVIDER_GCP,
    TERRATEST_MAIN,
    TFLINT_CONFIG,
    VERSIONS_TF,
)

# Map ModuleType → main.tf template
MAIN_TEMPLATES: dict[ModuleType, str] = {
    ModuleType.VPC: AWS_VPC_MAIN,
    ModuleType.S3_BUCKET: AWS_S3_MAIN,
    ModuleType.RESOURCE_GROUP: AZURE_RG_MAIN,
    ModuleType.VNET: AZURE_VNET_MAIN,
    ModuleType.STORAGE_ACCOUNT: AZURE_STORAGE_MAIN,
    ModuleType.GCP_VPC: GCP_VPC_MAIN,
    ModuleType.GCS_BUCKET: GCP_GCS_MAIN,
    ModuleType.BLANK: BLANK_MAIN,
}

PROVIDER_BLOCKS: dict[Provider, str] = {
    Provider.AWS: PROVIDER_AWS,
    Provider.AZURE: PROVIDER_AZURE,
    Provider.GCP: PROVIDER_GCP,
}


class ScaffoldEngine:
    """Generate Terraform module file structure."""

    def __init__(self) -> None:
        self.env = Environment(loader=BaseLoader(), keep_trailing_newline=True)

    def _render(self, template_str: str, context: dict) -> str:
        """Render a Jinja2 template string with context."""
        tmpl = self.env.from_string(template_str)
        return tmpl.render(**context)

    def scaffold(self, config: ModuleConfig) -> ScaffoldResult:
        """Generate the full module file tree."""
        result = ScaffoldResult(
            module_name=config.name,
            module_path=config.module_path,
            provider=config.provider.short_name,
            module_type=config.module_type.value,
        )

        # Get variable/output definitions
        variables, outputs = self._get_definitions(config)

        base_ctx = {
            "module_name": config.name,
            "description": config.description or config.module_type.description,
            "provider": config.provider.value,
            "provider_source": config.provider_source,
            "min_terraform_version": config.min_terraform_version,
            "min_provider_version": config.min_provider_version,
            "variables": variables,
            "outputs": outputs,
            "author": config.author,
            "module_slug": config.name.replace("-", "_"),
            "source_path": f"git::https://github.com/your-org/{config.name}.git",
        }

        root = config.module_path
        self._ensure_dir(root, result)

        # ── Core module files ──────────────────────────────────
        self._write(root / "versions.tf", self._render(VERSIONS_TF, base_ctx), result)
        self._write(root / "main.tf", self._render_main(config, base_ctx), result)
        self._write(
            root / "variables.tf", self._render(BLANK_VARIABLES, base_ctx), result
        )
        self._write(root / "outputs.tf", self._render(BLANK_OUTPUTS, base_ctx), result)
        self._write(root / "provider.tf", PROVIDER_BLOCKS[config.provider], result)

        # ── README ──────────────────────────────────────────────
        example_vars = self._build_example_vars(variables)
        readme_ctx = {**base_ctx, "example_vars": example_vars}
        self._write(root / "README.md", self._render(MODULE_README, readme_ctx), result)

        # ── .tflint.hcl ────────────────────────────────────────
        self._write(root / ".tflint.hcl", self._render(TFLINT_CONFIG, base_ctx), result)

        # ── Optional: examples ─────────────────────────────────
        if config.enable_examples:
            ex_dir = root / "examples" / "basic"
            self._ensure_dir(ex_dir, result)

            example_outputs = self._build_example_outputs(config, outputs)
            ex_ctx = {
                **base_ctx,
                "provider_block": PROVIDER_BLOCKS[config.provider],
                "example_vars": example_vars,
                "example_outputs": example_outputs,
            }
            self._write(ex_dir / "main.tf", self._render(EXAMPLE_MAIN, ex_ctx), result)

        # ── Optional: tests ────────────────────────────────────
        if config.enable_tests:
            test_dir = root / "tests"
            self._ensure_dir(test_dir, result)

            test_vars = self._build_test_vars(variables)
            test_ctx = {**base_ctx, "test_vars": test_vars}
            self._write(
                test_dir / "main.tf", self._render(TERRATEST_MAIN, test_ctx), result
            )

        # ── Optional: CI ───────────────────────────────────────
        if config.enable_ci:
            ci_dir = root / ".github" / "workflows"
            self._ensure_dir(ci_dir, result)
            self._write(ci_dir / "ci.yml", CI_GITHUB_ACTIONS, result)

        # ── Optional: pre-commit ───────────────────────────────
        if config.enable_precommit:
            self._write(root / ".pre-commit-config.yaml", PRECOMMIT_CONFIG, result)

        # ── Optional: Makefile ─────────────────────────────────
        if config.enable_makefile:
            self._write(root / "Makefile", MAKEFILE, result)

        # ── .gitignore ─────────────────────────────────────────
        self._write(root / ".gitignore", self._tf_gitignore(), result)

        # Count total lines
        result.total_lines = sum(
            self._count_lines(root / f) for f in result.files_created
        )

        return result

    def _get_definitions(
        self, config: ModuleConfig
    ) -> tuple[list[TerraformVariable], list[TerraformOutput]]:
        """Get variable/output definitions for the module type."""
        if config.module_type in MODULE_DEFINITIONS:
            return MODULE_DEFINITIONS[config.module_type]

        # Fallback: generate generic variables for the provider
        return self._generic_definitions(config.provider)

    def _generic_definitions(
        self, provider: Provider
    ) -> tuple[list[TerraformVariable], list[TerraformOutput]]:
        """Generate minimal generic variables for a blank/unsupported module type."""
        common_vars = {
            Provider.AWS: [
                TerraformVariable("name", "string", "Name of the resource"),
                TerraformVariable("region", "string", "AWS region", '"us-east-1"', required=False),
                TerraformVariable("tags", "map(string)", "Tags", "{}", required=False),
            ],
            Provider.AZURE: [
                TerraformVariable("name", "string", "Name of the resource"),
                TerraformVariable("location", "string", "Azure region", '"eastus"', required=False),
                TerraformVariable(
                    "resource_group_name", "string", "Resource group name"
                ),
                TerraformVariable("tags", "map(string)", "Tags", "{}", required=False),
            ],
            Provider.GCP: [
                TerraformVariable("name", "string", "Name of the resource"),
                TerraformVariable("project_id", "string", "GCP project ID"),
                TerraformVariable(
                    "region", "string", "GCP region",
                    '"us-central1"', required=False,
                ),
                TerraformVariable(
                    "labels", "map(string)", "Labels",
                    "{}", required=False,
                ),
            ],
        }
        return common_vars[provider], []

    def _render_main(self, config: ModuleConfig, ctx: dict) -> str:
        """Render the main.tf template for the module type."""
        template = MAIN_TEMPLATES.get(config.module_type, BLANK_MAIN)
        return self._render(template, ctx)

    def _build_example_vars(self, variables: list[TerraformVariable]) -> str:
        """Build example variable assignments for README/examples."""
        lines = []
        for v in variables:
            if v.name in ("tags", "labels"):
                continue
            if v.default is not None and not v.required:
                continue
            # Show required variables with placeholder values
            placeholder = self._placeholder(v)
            lines.append(f'{v.name} = {placeholder}')
        return "\n  ".join(lines)

    def _build_test_vars(self, variables: list[TerraformVariable]) -> str:
        """Build test variable assignments."""
        lines = []
        for v in variables:
            placeholder = self._test_value(v)
            lines.append(f'{v.name} = {placeholder}')
        return "\n  ".join(lines)

    def _build_example_outputs(
        self, config: ModuleConfig, outputs: list[TerraformOutput]
    ) -> str:
        """Build example output blocks."""
        slug = config.name.replace("-", "_")
        lines = []
        for o in outputs:
            if o.sensitive:
                continue
            lines.append(
                f'output "{o.name}" {{\n'
                f'  value = module.{slug}.{o.name}\n'
                f"}}"
            )
        return "\n\n".join(lines)

    def _placeholder(self, v: TerraformVariable) -> str:
        """Generate a placeholder value for a variable."""
        if v.default is not None:
            return v.default
        if "string" in v.type:
            return f'"my-{v.name}"'
        if v.type == "number":
            return "1"
        if v.type == "bool":
            return "true"
        if "list" in v.type:
            return "[]"
        if "map" in v.type:
            return "{}"
        return '""'

    def _test_value(self, v: TerraformVariable) -> str:
        """Generate a test value for a variable."""
        if v.default is not None:
            return v.default
        return self._placeholder(v)

    def _tf_gitignore(self) -> str:
        return """\
# Terraform
.terraform/
.terraform.lock.hcl
*.tfstate
*.tfstate.backup
*.tfplan
crash.log
override.tf
override.tf.json
*_override.tf
*_override.tf.json
.terraformrc
terraform.rc
"""

    def _ensure_dir(self, path: Path, result: ScaffoldResult) -> None:
        path.mkdir(parents=True, exist_ok=True)
        rel = str(path.relative_to(result.module_path))
        if rel != "." and rel not in result.directories_created:
            result.directories_created.append(rel)

    def _write(self, path: Path, content: str, result: ScaffoldResult) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        rel = str(path.relative_to(result.module_path))
        result.files_created.append(rel)

    def _count_lines(self, path: Path) -> int:
        try:
            full_path = path if path.is_absolute() else ScaffoldResult.module_path / path
            return full_path.read_text(encoding="utf-8").count("\n")
        except Exception:
            return 0
