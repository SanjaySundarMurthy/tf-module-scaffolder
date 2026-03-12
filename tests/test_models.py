"""Tests for models module."""

from __future__ import annotations

from tf_module_scaffolder.models import (
    PROVIDER_MODULES,
    ModuleConfig,
    ModuleType,
    Provider,
    ScaffoldResult,
    TerraformOutput,
    TerraformVariable,
)


class TestProvider:
    """Tests for Provider enum."""

    def test_aws_properties(self) -> None:
        assert Provider.AWS.value == "aws"
        assert Provider.AWS.display_name == "Amazon Web Services (AWS)"
        assert Provider.AWS.short_name == "AWS"

    def test_azure_properties(self) -> None:
        assert Provider.AZURE.value == "azurerm"
        assert Provider.AZURE.display_name == "Microsoft Azure"
        assert Provider.AZURE.short_name == "Azure"

    def test_gcp_properties(self) -> None:
        assert Provider.GCP.value == "google"
        assert Provider.GCP.display_name == "Google Cloud Platform (GCP)"
        assert Provider.GCP.short_name == "GCP"

    def test_all_providers_have_modules(self) -> None:
        for provider in Provider:
            assert provider in PROVIDER_MODULES
            assert len(PROVIDER_MODULES[provider]) > 0


class TestModuleType:
    """Tests for ModuleType enum."""

    def test_total_module_types(self) -> None:
        assert len(ModuleType) == 16

    def test_provider_property(self) -> None:
        assert ModuleType.VPC.provider == Provider.AWS
        assert ModuleType.VNET.provider == Provider.AZURE
        assert ModuleType.GCP_VPC.provider == Provider.GCP
        assert ModuleType.BLANK.provider is None

    def test_description_is_nonempty(self) -> None:
        for mt in ModuleType:
            assert mt.description, f"{mt.value} has no description"

    def test_aws_modules(self) -> None:
        aws_modules = PROVIDER_MODULES[Provider.AWS]
        assert ModuleType.VPC in aws_modules
        assert ModuleType.S3_BUCKET in aws_modules
        assert len(aws_modules) == 5

    def test_azure_modules(self) -> None:
        azure_modules = PROVIDER_MODULES[Provider.AZURE]
        assert ModuleType.RESOURCE_GROUP in azure_modules
        assert ModuleType.VNET in azure_modules
        assert len(azure_modules) == 5

    def test_gcp_modules(self) -> None:
        gcp_modules = PROVIDER_MODULES[Provider.GCP]
        assert ModuleType.GCP_VPC in gcp_modules
        assert ModuleType.GCS_BUCKET in gcp_modules
        assert len(gcp_modules) == 5


class TestTerraformVariable:
    """Tests for TerraformVariable."""

    def test_basic_variable(self) -> None:
        v = TerraformVariable("name", "string", "The name")
        assert v.name == "name"
        assert v.type == "string"
        assert v.description == "The name"
        assert v.default is None
        assert v.required is True
        assert v.sensitive is False
        assert v.validation is None

    def test_optional_variable(self) -> None:
        v = TerraformVariable("region", "string", "Region", '"us-east-1"', required=False)
        assert v.default == '"us-east-1"'
        assert v.required is False

    def test_sensitive_variable(self) -> None:
        v = TerraformVariable("password", "string", "DB password", sensitive=True)
        assert v.sensitive is True

    def test_variable_with_validation(self) -> None:
        v = TerraformVariable(
            "cidr",
            "string",
            "CIDR block",
            validation='can(cidrhost(var.cidr, 0))',
        )
        assert v.validation is not None


class TestTerraformOutput:
    """Tests for TerraformOutput."""

    def test_basic_output(self) -> None:
        o = TerraformOutput("id", "The resource ID", "aws_vpc.main.id")
        assert o.name == "id"
        assert o.description == "The resource ID"
        assert o.value == "aws_vpc.main.id"
        assert o.sensitive is False

    def test_sensitive_output(self) -> None:
        o = TerraformOutput("key", "Access key", "module.key.value", sensitive=True)
        assert o.sensitive is True


class TestModuleConfig:
    """Tests for ModuleConfig."""

    def test_default_config(self) -> None:
        config = ModuleConfig(
            name="my-vpc",
            provider=Provider.AWS,
            module_type=ModuleType.VPC,
        )
        assert config.name == "my-vpc"
        assert config.provider == Provider.AWS
        assert config.enable_examples is True
        assert config.enable_tests is True
        assert config.enable_ci is True
        assert config.enable_precommit is True
        assert config.enable_makefile is True

    def test_module_path(self) -> None:
        config = ModuleConfig(
            name="my-vpc",
            provider=Provider.AWS,
            module_type=ModuleType.VPC,
            output_dir="/tmp",
        )
        assert str(config.module_path).endswith("my-vpc")

    def test_provider_source(self) -> None:
        assert ModuleConfig(
            name="x", provider=Provider.AWS, module_type=ModuleType.VPC
        ).provider_source == "hashicorp/aws"
        assert ModuleConfig(
            name="x", provider=Provider.AZURE, module_type=ModuleType.VNET
        ).provider_source == "hashicorp/azurerm"
        assert ModuleConfig(
            name="x", provider=Provider.GCP, module_type=ModuleType.GCP_VPC
        ).provider_source == "hashicorp/google"


class TestScaffoldResult:
    """Tests for ScaffoldResult."""

    def test_defaults(self) -> None:
        r = ScaffoldResult(
            module_name="test",
            module_path="/tmp/test",
            provider="aws",
            module_type="vpc",
        )
        assert r.files_created == []
        assert r.directories_created == []
        assert r.total_lines == 0
