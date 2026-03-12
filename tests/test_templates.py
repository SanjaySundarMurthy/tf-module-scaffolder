"""Tests for HCL templates."""

from __future__ import annotations

from jinja2 import BaseLoader, Environment

from tf_module_scaffolder.models import TerraformOutput, TerraformVariable
from tf_module_scaffolder.templates.hcl import (
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

env = Environment(loader=BaseLoader(), keep_trailing_newline=True)


def _render(tmpl: str, ctx: dict | None = None) -> str:
    ctx = ctx or {}
    return env.from_string(tmpl).render(**ctx)


class TestVersionsTF:
    def test_contains_terraform_block(self) -> None:
        result = _render(
            VERSIONS_TF,
            {
                "min_terraform_version": ">= 1.5",
                "provider": "aws",
                "provider_source": "hashicorp/aws",
                "min_provider_version": ">= 5.0",
            },
        )
        assert "terraform {" in result
        assert "required_version" in result
        assert "hashicorp/aws" in result


class TestProviderBlocks:
    def test_aws_provider(self) -> None:
        assert "provider \"aws\"" in PROVIDER_AWS

    def test_azure_provider(self) -> None:
        assert "provider \"azurerm\"" in PROVIDER_AZURE
        assert "features" in PROVIDER_AZURE

    def test_gcp_provider(self) -> None:
        assert "provider \"google\"" in PROVIDER_GCP


class TestBlankTemplates:
    def test_blank_main(self) -> None:
        result = _render(BLANK_MAIN, {"module_name": "test", "description": "A test"})
        assert "test" in result

    def test_blank_variables(self) -> None:
        variables = [
            TerraformVariable("name", "string", "Name"),
            TerraformVariable("count_val", "number", "Count", "1", required=False),
        ]
        result = _render(BLANK_VARIABLES, {"variables": variables})
        assert 'variable "name"' in result
        assert "string" in result

    def test_blank_outputs(self) -> None:
        outputs = [
            TerraformOutput("id", "The ID", "module.main.id"),
        ]
        result = _render(BLANK_OUTPUTS, {"outputs": outputs})
        assert 'output "id"' in result


class TestAWSTemplates:
    def test_vpc_main(self) -> None:
        result = _render(AWS_VPC_MAIN, {"module_name": "test-vpc"})
        assert "aws_vpc" in result
        assert "aws_subnet" in result
        assert "aws_internet_gateway" in result

    def test_s3_main(self) -> None:
        result = _render(AWS_S3_MAIN, {"module_name": "test-s3"})
        assert "aws_s3_bucket" in result
        assert "versioning" in result


class TestAzureTemplates:
    def test_rg_main(self) -> None:
        result = _render(AZURE_RG_MAIN, {"module_name": "test-rg"})
        assert "azurerm_resource_group" in result

    def test_vnet_main(self) -> None:
        result = _render(AZURE_VNET_MAIN, {"module_name": "test-vnet"})
        assert "azurerm_virtual_network" in result

    def test_storage_main(self) -> None:
        result = _render(AZURE_STORAGE_MAIN, {"module_name": "test-storage"})
        assert "azurerm_storage_account" in result


class TestGCPTemplates:
    def test_vpc_main(self) -> None:
        result = _render(GCP_VPC_MAIN, {"module_name": "test-vpc"})
        assert "google_compute_network" in result

    def test_gcs_main(self) -> None:
        result = _render(GCP_GCS_MAIN, {"module_name": "test-gcs"})
        assert "google_storage_bucket" in result


class TestSupportingTemplates:
    def test_makefile(self) -> None:
        assert "terraform init" in MAKEFILE
        assert "terraform validate" in MAKEFILE

    def test_precommit(self) -> None:
        assert "pre-commit" in PRECOMMIT_CONFIG or "repo:" in PRECOMMIT_CONFIG

    def test_tflint(self) -> None:
        result = _render(TFLINT_CONFIG, {"provider": "aws"})
        assert "tflint" in result.lower() or "plugin" in result.lower()

    def test_ci_github_actions(self) -> None:
        assert "terraform" in CI_GITHUB_ACTIONS.lower()
        assert "validate" in CI_GITHUB_ACTIONS.lower()

    def test_module_readme(self) -> None:
        result = _render(
            MODULE_README,
            {
                "module_name": "test",
                "description": "A test module",
                "provider": "aws",
                "provider_source": "hashicorp/aws",
                "min_terraform_version": ">= 1.5",
                "min_provider_version": ">= 5.0",
                "variables": [TerraformVariable("name", "string", "Name")],
                "outputs": [TerraformOutput("id", "The ID", "aws_vpc.main.id")],
                "example_vars": 'name = "my-test"',
                "author": "Test Author",
                "source_path": "git::https://github.com/test/test.git",
            },
        )
        assert "test" in result
        assert "name" in result

    def test_example_main(self) -> None:
        result = _render(
            EXAMPLE_MAIN,
            {
                "module_name": "test",
                "module_slug": "test",
                "provider_block": PROVIDER_AWS,
                "example_vars": 'name = "test"',
                "example_outputs": "",
                "source_path": "../..",
            },
        )
        assert "module" in result

    def test_terratest_main(self) -> None:
        result = _render(
            TERRATEST_MAIN,
            {
                "module_name": "test",
                "module_slug": "test",
                "test_vars": 'name = "test"',
                "provider": "aws",
                "provider_source": "hashicorp/aws",
                "min_terraform_version": ">= 1.5",
                "min_provider_version": ">= 5.0",
            },
        )
        assert "module" in result
