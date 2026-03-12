"""Tests for the scaffold engine."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from tf_module_scaffolder.engine import ScaffoldEngine
from tf_module_scaffolder.models import ModuleConfig, ModuleType, Provider


@pytest.fixture
def engine() -> ScaffoldEngine:
    return ScaffoldEngine()


@pytest.fixture
def tmp_dir() -> Path:
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


class TestScaffoldEngine:
    """Tests for ScaffoldEngine."""

    def test_scaffold_creates_module_directory(
        self, engine: ScaffoldEngine, tmp_dir: Path
    ) -> None:
        config = ModuleConfig(
            name="test-vpc",
            provider=Provider.AWS,
            module_type=ModuleType.VPC,
            output_dir=str(tmp_dir),
        )
        result = engine.scaffold(config)
        assert (tmp_dir / "test-vpc").is_dir()
        assert result.module_name == "test-vpc"

    def test_scaffold_creates_core_files(
        self, engine: ScaffoldEngine, tmp_dir: Path
    ) -> None:
        config = ModuleConfig(
            name="test-vpc",
            provider=Provider.AWS,
            module_type=ModuleType.VPC,
            output_dir=str(tmp_dir),
        )
        engine.scaffold(config)
        root = tmp_dir / "test-vpc"
        assert (root / "main.tf").is_file()
        assert (root / "variables.tf").is_file()
        assert (root / "outputs.tf").is_file()
        assert (root / "versions.tf").is_file()
        assert (root / "provider.tf").is_file()
        assert (root / "README.md").is_file()

    def test_scaffold_creates_examples(
        self, engine: ScaffoldEngine, tmp_dir: Path
    ) -> None:
        config = ModuleConfig(
            name="test-vpc",
            provider=Provider.AWS,
            module_type=ModuleType.VPC,
            output_dir=str(tmp_dir),
            enable_examples=True,
        )
        engine.scaffold(config)
        assert (tmp_dir / "test-vpc" / "examples" / "basic" / "main.tf").is_file()

    def test_scaffold_creates_tests(
        self, engine: ScaffoldEngine, tmp_dir: Path
    ) -> None:
        config = ModuleConfig(
            name="test-vpc",
            provider=Provider.AWS,
            module_type=ModuleType.VPC,
            output_dir=str(tmp_dir),
            enable_tests=True,
        )
        engine.scaffold(config)
        assert (tmp_dir / "test-vpc" / "tests" / "main.tf").is_file()

    def test_scaffold_creates_ci(
        self, engine: ScaffoldEngine, tmp_dir: Path
    ) -> None:
        config = ModuleConfig(
            name="test-vpc",
            provider=Provider.AWS,
            module_type=ModuleType.VPC,
            output_dir=str(tmp_dir),
            enable_ci=True,
        )
        engine.scaffold(config)
        assert (tmp_dir / "test-vpc" / ".github" / "workflows" / "ci.yml").is_file()

    def test_scaffold_creates_precommit(
        self, engine: ScaffoldEngine, tmp_dir: Path
    ) -> None:
        config = ModuleConfig(
            name="test-vpc",
            provider=Provider.AWS,
            module_type=ModuleType.VPC,
            output_dir=str(tmp_dir),
            enable_precommit=True,
        )
        engine.scaffold(config)
        assert (tmp_dir / "test-vpc" / ".pre-commit-config.yaml").is_file()

    def test_scaffold_creates_makefile(
        self, engine: ScaffoldEngine, tmp_dir: Path
    ) -> None:
        config = ModuleConfig(
            name="test-vpc",
            provider=Provider.AWS,
            module_type=ModuleType.VPC,
            output_dir=str(tmp_dir),
            enable_makefile=True,
        )
        engine.scaffold(config)
        assert (tmp_dir / "test-vpc" / "Makefile").is_file()

    def test_scaffold_creates_gitignore(
        self, engine: ScaffoldEngine, tmp_dir: Path
    ) -> None:
        config = ModuleConfig(
            name="test-vpc",
            provider=Provider.AWS,
            module_type=ModuleType.VPC,
            output_dir=str(tmp_dir),
        )
        engine.scaffold(config)
        assert (tmp_dir / "test-vpc" / ".gitignore").is_file()

    def test_scaffold_no_examples(
        self, engine: ScaffoldEngine, tmp_dir: Path
    ) -> None:
        config = ModuleConfig(
            name="test-vpc",
            provider=Provider.AWS,
            module_type=ModuleType.VPC,
            output_dir=str(tmp_dir),
            enable_examples=False,
        )
        engine.scaffold(config)
        assert not (tmp_dir / "test-vpc" / "examples").exists()

    def test_scaffold_no_tests(
        self, engine: ScaffoldEngine, tmp_dir: Path
    ) -> None:
        config = ModuleConfig(
            name="test-vpc",
            provider=Provider.AWS,
            module_type=ModuleType.VPC,
            output_dir=str(tmp_dir),
            enable_tests=False,
        )
        engine.scaffold(config)
        assert not (tmp_dir / "test-vpc" / "tests").exists()

    def test_scaffold_no_ci(
        self, engine: ScaffoldEngine, tmp_dir: Path
    ) -> None:
        config = ModuleConfig(
            name="test-vpc",
            provider=Provider.AWS,
            module_type=ModuleType.VPC,
            output_dir=str(tmp_dir),
            enable_ci=False,
        )
        engine.scaffold(config)
        assert not (tmp_dir / "test-vpc" / ".github").exists()


class TestProviderScaffolding:
    """Test scaffolding for each provider."""

    @pytest.mark.parametrize(
        "provider,module_type",
        [
            (Provider.AWS, ModuleType.VPC),
            (Provider.AWS, ModuleType.S3_BUCKET),
            (Provider.AZURE, ModuleType.RESOURCE_GROUP),
            (Provider.AZURE, ModuleType.VNET),
            (Provider.AZURE, ModuleType.STORAGE_ACCOUNT),
            (Provider.GCP, ModuleType.GCP_VPC),
            (Provider.GCP, ModuleType.GCS_BUCKET),
        ],
    )
    def test_scaffold_per_provider(
        self,
        engine: ScaffoldEngine,
        tmp_dir: Path,
        provider: Provider,
        module_type: ModuleType,
    ) -> None:
        config = ModuleConfig(
            name=f"test-{module_type.value}",
            provider=provider,
            module_type=module_type,
            output_dir=str(tmp_dir),
        )
        result = engine.scaffold(config)
        root = tmp_dir / f"test-{module_type.value}"
        assert root.is_dir()
        assert (root / "main.tf").is_file()
        assert (root / "versions.tf").is_file()
        assert result.total_lines > 0
        assert len(result.files_created) >= 6

    def test_scaffold_blank_module(
        self, engine: ScaffoldEngine, tmp_dir: Path
    ) -> None:
        config = ModuleConfig(
            name="test-blank",
            provider=Provider.AWS,
            module_type=ModuleType.BLANK,
            output_dir=str(tmp_dir),
        )
        engine.scaffold(config)
        assert (tmp_dir / "test-blank" / "main.tf").is_file()

    def test_scaffold_unsupported_module_type_uses_generic(
        self, engine: ScaffoldEngine, tmp_dir: Path
    ) -> None:
        """Unsupported module types should still scaffold with generic vars."""
        config = ModuleConfig(
            name="test-eks",
            provider=Provider.AWS,
            module_type=ModuleType.EKS_CLUSTER,
            output_dir=str(tmp_dir),
        )
        result = engine.scaffold(config)
        root = tmp_dir / "test-eks"
        assert root.is_dir()
        assert (root / "main.tf").is_file()
        assert len(result.files_created) >= 6


class TestMainTFContent:
    """Test that main.tf content is correct for each type."""

    def test_aws_vpc_main_has_vpc_resource(
        self, engine: ScaffoldEngine, tmp_dir: Path
    ) -> None:
        config = ModuleConfig(
            name="v",
            provider=Provider.AWS,
            module_type=ModuleType.VPC,
            output_dir=str(tmp_dir),
        )
        engine.scaffold(config)
        content = (tmp_dir / "v" / "main.tf").read_text()
        assert "aws_vpc" in content

    def test_azure_rg_main_has_rg_resource(
        self, engine: ScaffoldEngine, tmp_dir: Path
    ) -> None:
        config = ModuleConfig(
            name="r",
            provider=Provider.AZURE,
            module_type=ModuleType.RESOURCE_GROUP,
            output_dir=str(tmp_dir),
        )
        engine.scaffold(config)
        content = (tmp_dir / "r" / "main.tf").read_text()
        assert "azurerm_resource_group" in content

    def test_gcp_vpc_main_has_network_resource(
        self, engine: ScaffoldEngine, tmp_dir: Path
    ) -> None:
        config = ModuleConfig(
            name="n",
            provider=Provider.GCP,
            module_type=ModuleType.GCP_VPC,
            output_dir=str(tmp_dir),
        )
        engine.scaffold(config)
        content = (tmp_dir / "n" / "main.tf").read_text()
        assert "google_compute_network" in content


class TestResultTracking:
    """Test that ScaffoldResult tracks correctly."""

    def test_result_file_count(
        self, engine: ScaffoldEngine, tmp_dir: Path
    ) -> None:
        config = ModuleConfig(
            name="test",
            provider=Provider.AWS,
            module_type=ModuleType.VPC,
            output_dir=str(tmp_dir),
        )
        result = engine.scaffold(config)
        # With all options enabled: main.tf, variables.tf, outputs.tf, versions.tf,
        # provider.tf, README.md, .tflint.hcl, examples/basic/main.tf,
        # tests/main.tf, .github/workflows/ci.yml, .pre-commit-config.yaml,
        # Makefile, .gitignore = 13 files
        assert len(result.files_created) >= 10

    def test_result_directory_count(
        self, engine: ScaffoldEngine, tmp_dir: Path
    ) -> None:
        config = ModuleConfig(
            name="test",
            provider=Provider.AWS,
            module_type=ModuleType.VPC,
            output_dir=str(tmp_dir),
        )
        result = engine.scaffold(config)
        assert len(result.directories_created) >= 3

    def test_total_lines_positive(
        self, engine: ScaffoldEngine, tmp_dir: Path
    ) -> None:
        config = ModuleConfig(
            name="test",
            provider=Provider.AWS,
            module_type=ModuleType.VPC,
            output_dir=str(tmp_dir),
        )
        result = engine.scaffold(config)
        assert result.total_lines > 50
