"""Data models for Terraform module scaffolding."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Provider(str, Enum):
    """Supported cloud providers."""

    AWS = "aws"
    AZURE = "azurerm"
    GCP = "google"

    @property
    def display_name(self) -> str:
        return {
            Provider.AWS: "Amazon Web Services (AWS)",
            Provider.AZURE: "Microsoft Azure",
            Provider.GCP: "Google Cloud Platform (GCP)",
        }[self]

    @property
    def short_name(self) -> str:
        return {Provider.AWS: "AWS", Provider.AZURE: "Azure", Provider.GCP: "GCP"}[self]


class ModuleType(str, Enum):
    """Pre-built module templates."""

    # AWS
    VPC = "vpc"
    S3_BUCKET = "s3-bucket"
    EKS_CLUSTER = "eks-cluster"
    LAMBDA_FUNCTION = "lambda-function"
    RDS_INSTANCE = "rds-instance"

    # Azure
    RESOURCE_GROUP = "resource-group"
    VNET = "vnet"
    AKS_CLUSTER = "aks-cluster"
    STORAGE_ACCOUNT = "storage-account"
    APP_SERVICE = "app-service"

    # GCP
    GCP_VPC = "gcp-vpc"
    GKE_CLUSTER = "gke-cluster"
    GCS_BUCKET = "gcs-bucket"
    CLOUD_RUN = "cloud-run"
    CLOUD_SQL = "cloud-sql"

    # Generic
    BLANK = "blank"

    @property
    def provider(self) -> Provider | None:
        aws = {ModuleType.VPC, ModuleType.S3_BUCKET, ModuleType.EKS_CLUSTER,
               ModuleType.LAMBDA_FUNCTION, ModuleType.RDS_INSTANCE}
        azure = {ModuleType.RESOURCE_GROUP, ModuleType.VNET, ModuleType.AKS_CLUSTER,
                 ModuleType.STORAGE_ACCOUNT, ModuleType.APP_SERVICE}
        gcp = {ModuleType.GCP_VPC, ModuleType.GKE_CLUSTER, ModuleType.GCS_BUCKET,
               ModuleType.CLOUD_RUN, ModuleType.CLOUD_SQL}
        if self in aws:
            return Provider.AWS
        if self in azure:
            return Provider.AZURE
        if self in gcp:
            return Provider.GCP
        return None

    @property
    def description(self) -> str:
        descriptions = {
            ModuleType.VPC: "AWS VPC with public/private subnets, NAT gateway, and flow logs",
            ModuleType.S3_BUCKET: "AWS S3 bucket with versioning, encryption, and lifecycle rules",
            ModuleType.EKS_CLUSTER: "AWS EKS cluster with managed node groups and IRSA",
            ModuleType.LAMBDA_FUNCTION: "AWS Lambda function with IAM role and CloudWatch logs",
            ModuleType.RDS_INSTANCE: "AWS RDS instance with parameter groups and subnet group",
            ModuleType.RESOURCE_GROUP: "Azure resource group with tags and RBAC",
            ModuleType.VNET: "Azure VNet with subnets, NSGs, and peering support",
            ModuleType.AKS_CLUSTER: "Azure AKS cluster with node pools and monitoring",
            ModuleType.STORAGE_ACCOUNT: "Azure storage account with containers and lifecycle rules",
            ModuleType.APP_SERVICE: "Azure App Service with plan, slots, and diagnostics",
            ModuleType.GCP_VPC: "GCP VPC network with subnets and firewall rules",
            ModuleType.GKE_CLUSTER: "GCP GKE cluster with node pools and workload identity",
            ModuleType.GCS_BUCKET: "GCP Cloud Storage bucket with lifecycle and IAM",
            ModuleType.CLOUD_RUN: "GCP Cloud Run service with IAM and domain mapping",
            ModuleType.CLOUD_SQL: "GCP Cloud SQL instance with backups and replicas",
            ModuleType.BLANK: "Blank module with standard file structure",
        }
        return descriptions.get(self, "")


PROVIDER_MODULES: dict[Provider, list[ModuleType]] = {
    Provider.AWS: [
        ModuleType.VPC, ModuleType.S3_BUCKET, ModuleType.EKS_CLUSTER,
        ModuleType.LAMBDA_FUNCTION, ModuleType.RDS_INSTANCE,
    ],
    Provider.AZURE: [
        ModuleType.RESOURCE_GROUP, ModuleType.VNET, ModuleType.AKS_CLUSTER,
        ModuleType.STORAGE_ACCOUNT, ModuleType.APP_SERVICE,
    ],
    Provider.GCP: [
        ModuleType.GCP_VPC, ModuleType.GKE_CLUSTER, ModuleType.GCS_BUCKET,
        ModuleType.CLOUD_RUN, ModuleType.CLOUD_SQL,
    ],
}


@dataclass
class TerraformVariable:
    """A Terraform input variable."""

    name: str
    type: str
    description: str
    default: str | None = None
    required: bool = True
    sensitive: bool = False
    validation: str | None = None  # HCL validation block content


@dataclass
class TerraformOutput:
    """A Terraform output."""

    name: str
    description: str
    value: str
    sensitive: bool = False


@dataclass
class ModuleConfig:
    """Configuration for scaffolding a Terraform module."""

    name: str
    provider: Provider
    module_type: ModuleType
    description: str = ""
    author: str = ""
    min_terraform_version: str = "1.5"
    min_provider_version: str = "5.0"
    output_dir: str = "."
    enable_examples: bool = True
    enable_tests: bool = True
    enable_ci: bool = True
    enable_precommit: bool = True
    enable_makefile: bool = True
    tags: dict[str, str] = field(default_factory=dict)

    @property
    def module_path(self) -> Path:
        return Path(self.output_dir) / self.name

    @property
    def provider_source(self) -> str:
        sources = {
            Provider.AWS: "hashicorp/aws",
            Provider.AZURE: "hashicorp/azurerm",
            Provider.GCP: "hashicorp/google",
        }
        return sources[self.provider]


@dataclass
class ScaffoldResult:
    """Result of scaffolding a module."""

    module_name: str
    module_path: Path
    files_created: list[str] = field(default_factory=list)
    directories_created: list[str] = field(default_factory=list)
    total_lines: int = 0
    provider: str = ""
    module_type: str = ""
