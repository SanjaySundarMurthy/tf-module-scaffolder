"""Tests for template definitions."""

from __future__ import annotations

from tf_module_scaffolder.models import ModuleType, TerraformOutput, TerraformVariable
from tf_module_scaffolder.templates.definitions import MODULE_DEFINITIONS


class TestModuleDefinitions:
    """Tests for MODULE_DEFINITIONS registry."""

    def test_all_expected_modules_have_definitions(self) -> None:
        expected = [
            ModuleType.VPC,
            ModuleType.S3_BUCKET,
            ModuleType.RESOURCE_GROUP,
            ModuleType.VNET,
            ModuleType.STORAGE_ACCOUNT,
            ModuleType.GCP_VPC,
            ModuleType.GCS_BUCKET,
        ]
        for mt in expected:
            assert mt in MODULE_DEFINITIONS, f"{mt.value} missing from MODULE_DEFINITIONS"

    def test_definitions_are_tuples(self) -> None:
        for mt, defn in MODULE_DEFINITIONS.items():
            assert isinstance(defn, tuple), f"{mt.value} should be a tuple"
            assert len(defn) == 2, f"{mt.value} tuple should have 2 elements"

    def test_variables_are_terraform_variable(self) -> None:
        for mt, (variables, _) in MODULE_DEFINITIONS.items():
            assert isinstance(variables, list)
            for v in variables:
                assert isinstance(v, TerraformVariable), (
                    f"{mt.value}: {v} is not TerraformVariable"
                )

    def test_outputs_are_terraform_output(self) -> None:
        for mt, (_, outputs) in MODULE_DEFINITIONS.items():
            assert isinstance(outputs, list)
            for o in outputs:
                assert isinstance(o, TerraformOutput), (
                    f"{mt.value}: {o} is not TerraformOutput"
                )

    def test_all_variables_have_required_fields(self) -> None:
        for mt, (variables, _) in MODULE_DEFINITIONS.items():
            for v in variables:
                assert v.name, f"{mt.value}: variable missing name"
                assert v.type, f"{mt.value}: {v.name} missing type"
                assert v.description, f"{mt.value}: {v.name} missing description"


class TestAWSVPCDefinitions:
    """Tests for AWS VPC variable/output definitions."""

    def test_vpc_has_cidr_variable(self) -> None:
        variables, _ = MODULE_DEFINITIONS[ModuleType.VPC]
        names = [v.name for v in variables]
        assert "vpc_cidr" in names

    def test_vpc_has_outputs(self) -> None:
        _, outputs = MODULE_DEFINITIONS[ModuleType.VPC]
        assert len(outputs) >= 3
        names = [o.name for o in outputs]
        assert "vpc_id" in names


class TestAzureDefinitions:
    """Tests for Azure variable/output definitions."""

    def test_rg_variables(self) -> None:
        variables, _ = MODULE_DEFINITIONS[ModuleType.RESOURCE_GROUP]
        names = [v.name for v in variables]
        assert "name" in names
        assert "location" in names

    def test_storage_account_has_many_variables(self) -> None:
        variables, _ = MODULE_DEFINITIONS[ModuleType.STORAGE_ACCOUNT]
        assert len(variables) >= 10


class TestGCPDefinitions:
    """Tests for GCP variable/output definitions."""

    def test_gcp_vpc_has_project_id(self) -> None:
        variables, _ = MODULE_DEFINITIONS[ModuleType.GCP_VPC]
        names = [v.name for v in variables]
        assert "project_id" in names

    def test_gcs_has_bucket_name(self) -> None:
        variables, _ = MODULE_DEFINITIONS[ModuleType.GCS_BUCKET]
        names = [v.name for v in variables]
        assert "bucket_name" in names
