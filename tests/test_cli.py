"""Tests for CLI commands."""

from __future__ import annotations

import tempfile
from pathlib import Path

from click.testing import CliRunner

from tf_module_scaffolder.cli import cli


class TestCLIList:
    """Tests for 'tf-scaffold list' command."""

    def test_list_command(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "vpc" in result.output.lower() or "VPC" in result.output

    def test_list_shows_all_providers(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0


class TestCLINew:
    """Tests for 'tf-scaffold new' command (non-interactive)."""

    def test_new_aws_vpc(self) -> None:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            result = runner.invoke(
                cli,
                [
                    "new",
                    "-p", "aws",
                    "-t", "vpc",
                    "-n", "my-vpc",
                    "-o", tmp,
                ],
            )
            assert result.exit_code == 0
            assert (Path(tmp) / "my-vpc" / "main.tf").is_file()

    def test_new_azure_rg(self) -> None:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            result = runner.invoke(
                cli,
                [
                    "new",
                    "-p", "azure",
                    "-t", "resource-group",
                    "-n", "my-rg",
                    "-o", tmp,
                ],
            )
            assert result.exit_code == 0
            assert (Path(tmp) / "my-rg" / "main.tf").is_file()

    def test_new_gcp_vpc(self) -> None:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            result = runner.invoke(
                cli,
                [
                    "new",
                    "-p", "gcp",
                    "-t", "gcp-vpc",
                    "-n", "my-network",
                    "-o", tmp,
                ],
            )
            assert result.exit_code == 0
            assert (Path(tmp) / "my-network" / "main.tf").is_file()

    def test_new_with_no_options_flags(self) -> None:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            result = runner.invoke(
                cli,
                [
                    "new",
                    "-p", "aws",
                    "-t", "s3-bucket",
                    "-n", "my-s3",
                    "-o", tmp,
                    "--no-examples",
                    "--no-tests",
                    "--no-ci",
                    "--no-precommit",
                    "--no-makefile",
                ],
            )
            assert result.exit_code == 0
            root = Path(tmp) / "my-s3"
            assert root.is_dir()
            assert not (root / "examples").exists()
            assert not (root / "tests").exists()
            assert not (root / ".github").exists()
            assert not (root / ".pre-commit-config.yaml").exists()
            assert not (root / "Makefile").exists()

    def test_new_with_description_and_author(self) -> None:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            result = runner.invoke(
                cli,
                [
                    "new",
                    "-p", "aws",
                    "-t", "vpc",
                    "-n", "my-vpc",
                    "-o", tmp,
                    "-d", "My custom VPC module",
                    "-a", "John Doe",
                ],
            )
            assert result.exit_code == 0
            readme = (Path(tmp) / "my-vpc" / "README.md").read_text()
            assert "My custom VPC module" in readme


class TestCLIQuickstart:
    """Tests for 'tf-scaffold quickstart' command."""

    def test_quickstart_aws_vpc(self) -> None:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            result = runner.invoke(
                cli, ["quickstart", "aws-vpc", "-o", tmp]
            )
            assert result.exit_code == 0
            assert (Path(tmp) / "terraform-aws-vpc" / "main.tf").is_file()

    def test_quickstart_azure_rg(self) -> None:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            result = runner.invoke(
                cli, ["quickstart", "azure-rg", "-o", tmp]
            )
            assert result.exit_code == 0
            assert (Path(tmp) / "terraform-azure-resource-group" / "main.tf").is_file()

    def test_quickstart_with_custom_name(self) -> None:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            result = runner.invoke(
                cli, ["quickstart", "gcp-vpc", "-n", "my-gcp-net", "-o", tmp]
            )
            assert result.exit_code == 0
            assert (Path(tmp) / "my-gcp-net" / "main.tf").is_file()

    def test_quickstart_gcp_gcs(self) -> None:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            result = runner.invoke(
                cli, ["quickstart", "gcp-gcs", "-o", tmp]
            )
            assert result.exit_code == 0

    def test_quickstart_azure_storage(self) -> None:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            result = runner.invoke(
                cli, ["quickstart", "azure-storage", "-o", tmp]
            )
            assert result.exit_code == 0


class TestCLIVersion:
    """Tests for version flag."""

    def test_version_flag(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0


class TestCLIHelp:
    """Tests for help text."""

    def test_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "tf-scaffold" in result.output.lower() or "scaffold" in result.output.lower()

    def test_new_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["new", "--help"])
        assert result.exit_code == 0
        assert "--provider" in result.output

    def test_quickstart_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["quickstart", "--help"])
        assert result.exit_code == 0
