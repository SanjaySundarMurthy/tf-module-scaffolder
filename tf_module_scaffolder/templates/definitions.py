"""Variable and output definitions for each module type."""

from __future__ import annotations

from ..models import ModuleType, TerraformOutput, TerraformVariable

# ══════════════════════════════════════════════════════════════════════
# COMMON / SHARED VARIABLES
# ══════════════════════════════════════════════════════════════════════

_AWS_COMMON = [
    TerraformVariable("region", "string", "AWS region", '"us-east-1"', required=False),
    TerraformVariable(
        "tags", "map(string)", "Tags to apply to all resources", "{}", required=False
    ),
]

_AZURE_COMMON = [
    TerraformVariable("location", "string", "Azure region", '"eastus"', required=False),
    TerraformVariable(
        "tags", "map(string)", "Tags to apply to all resources", "{}", required=False
    ),
]

_GCP_COMMON = [
    TerraformVariable("project_id", "string", "GCP project ID"),
    TerraformVariable("region", "string", "GCP region", '"us-central1"', required=False),
    TerraformVariable(
        "labels", "map(string)", "Labels to apply to all resources", "{}", required=False
    ),
]


# ══════════════════════════════════════════════════════════════════════
# AWS MODULE DEFINITIONS
# ══════════════════════════════════════════════════════════════════════

AWS_VPC_VARS = _AWS_COMMON + [
    TerraformVariable("name", "string", "Name of the VPC"),
    TerraformVariable(
        "vpc_cidr", "string", "CIDR block for the VPC", '"10.0.0.0/16"', required=False,
        validation=(
            'condition     = can(cidrhost(var.vpc_cidr, 0))'
            '\n    error_message = "Must be a valid CIDR block."'
        ),
    ),
    TerraformVariable("az_count", "number", "Number of availability zones", "3", required=False),
    TerraformVariable(
        "enable_nat_gateway", "bool", "Enable NAT Gateway for private subnets", "true",
        required=False,
    ),
    TerraformVariable(
        "enable_flow_logs", "bool", "Enable VPC Flow Logs", "true", required=False
    ),
    TerraformVariable(
        "flow_log_retention_days", "number", "CloudWatch log retention in days", "30",
        required=False,
    ),
]

AWS_VPC_OUTPUTS = [
    TerraformOutput("vpc_id", "The ID of the VPC", "aws_vpc.this.id"),
    TerraformOutput("vpc_cidr", "The CIDR block of the VPC", "aws_vpc.this.cidr_block"),
    TerraformOutput(
        "public_subnet_ids", "List of public subnet IDs", "aws_subnet.public[*].id"
    ),
    TerraformOutput(
        "private_subnet_ids", "List of private subnet IDs", "aws_subnet.private[*].id"
    ),
    TerraformOutput(
        "nat_gateway_id", "ID of the NAT Gateway",
        'try(aws_nat_gateway.this[0].id, "")',
    ),
]

AWS_S3_VARS = _AWS_COMMON + [
    TerraformVariable("bucket_name", "string", "Name of the S3 bucket"),
    TerraformVariable(
        "enable_versioning", "bool", "Enable bucket versioning", "true", required=False
    ),
    TerraformVariable(
        "kms_key_arn", "string", "KMS key ARN for encryption",
        '""', required=False,
    ),
    TerraformVariable(
        "force_destroy", "bool", "Allow bucket force destroy",
        "false", required=False,
    ),
    TerraformVariable(
        "enable_lifecycle", "bool", "Enable lifecycle rules", "false", required=False
    ),
    TerraformVariable(
        "transition_ia_days", "number", "Days before IA transition", "90", required=False
    ),
    TerraformVariable(
        "transition_glacier_days", "number", "Days before Glacier transition", "180",
        required=False,
    ),
    TerraformVariable(
        "expiration_days", "number", "Days before object expiration", "365", required=False
    ),
    TerraformVariable(
        "noncurrent_expiration_days", "number", "Days for noncurrent version expiration",
        "90", required=False,
    ),
]

AWS_S3_OUTPUTS = [
    TerraformOutput("bucket_id", "The name of the bucket", "aws_s3_bucket.this.id"),
    TerraformOutput("bucket_arn", "The ARN of the bucket", "aws_s3_bucket.this.arn"),
    TerraformOutput(
        "bucket_domain_name", "The domain name of the bucket",
        "aws_s3_bucket.this.bucket_domain_name",
    ),
]


# ══════════════════════════════════════════════════════════════════════
# AZURE MODULE DEFINITIONS
# ══════════════════════════════════════════════════════════════════════

AZURE_RG_VARS = _AZURE_COMMON + [
    TerraformVariable("name", "string", "Name of the resource group"),
    TerraformVariable(
        "enable_delete_lock", "bool", "Enable delete lock on resource group", "false",
        required=False,
    ),
]

AZURE_RG_OUTPUTS = [
    TerraformOutput("id", "The ID of the resource group", "azurerm_resource_group.this.id"),
    TerraformOutput(
        "name", "The name of the resource group", "azurerm_resource_group.this.name"
    ),
    TerraformOutput(
        "location", "The location of the resource group",
        "azurerm_resource_group.this.location",
    ),
]

AZURE_VNET_VARS = _AZURE_COMMON + [
    TerraformVariable("name", "string", "Name of the virtual network"),
    TerraformVariable("resource_group_name", "string", "Name of the resource group"),
    TerraformVariable(
        "address_space", "list(string)", "Address space for the VNet",
        '["10.0.0.0/16"]', required=False,
    ),
    TerraformVariable(
        "subnets",
        (
            'map(object({\n    address_prefix = string'
            '\n    create_nsg     = optional(bool, true)'
            '\n    delegation     = optional(object({'
            '\n      name    = string\n      service = string'
            '\n      actions = list(string)\n    }))\n  }))'
        ),
        "Subnet configurations",
        "{}",
        required=False,
    ),
]

AZURE_VNET_OUTPUTS = [
    TerraformOutput("id", "The ID of the VNet", "azurerm_virtual_network.this.id"),
    TerraformOutput("name", "The name of the VNet", "azurerm_virtual_network.this.name"),
    TerraformOutput(
        "subnet_ids", "Map of subnet name to ID",
        "{for k, v in azurerm_subnet.this : k => v.id}",
    ),
]

AZURE_STORAGE_VARS = _AZURE_COMMON + [
    TerraformVariable(
        "name", "string", "Name of the storage account (3-24 chars, lowercase alphanumeric)",
        validation=(
            'condition     = can(regex("^[a-z0-9]{3,24}$", var.name))'
            '\n    error_message = "Storage account name must be'
            ' 3-24 lowercase alphanumeric characters."'
        ),
    ),
    TerraformVariable("resource_group_name", "string", "Name of the resource group"),
    TerraformVariable(
        "account_tier", "string", "Performance tier (Standard or Premium)", '"Standard"',
        required=False,
    ),
    TerraformVariable(
        "replication_type", "string", "Replication type", '"LRS"', required=False,
        validation=(
            'condition     = contains('
            '["LRS", "GRS", "RAGRS", "ZRS", "GZRS", "RAGZRS"],'
            ' var.replication_type)'
            '\n    error_message = "Must be one of:'
            ' LRS, GRS, RAGRS, ZRS, GZRS, RAGZRS."'
        ),
    ),
    TerraformVariable(
        "account_kind", "string", "Storage account kind", '"StorageV2"', required=False
    ),
    TerraformVariable(
        "enable_versioning", "bool", "Enable blob versioning", "true", required=False
    ),
    TerraformVariable(
        "soft_delete_days", "number", "Blob soft delete retention days (0 to disable)", "7",
        required=False,
    ),
    TerraformVariable(
        "containers", "list(string)", "List of blob containers to create", "[]",
        required=False,
    ),
    TerraformVariable(
        "enable_lifecycle", "bool", "Enable lifecycle management", "false", required=False
    ),
    TerraformVariable(
        "cool_after_days", "number", "Days before moving blobs to cool tier", "30",
        required=False,
    ),
    TerraformVariable(
        "enable_network_rules", "bool", "Enable network rules (firewall)", "false",
        required=False,
    ),
    TerraformVariable(
        "allowed_ip_ranges", "list(string)", "Allowed IP ranges", "[]", required=False
    ),
    TerraformVariable(
        "allowed_subnet_ids", "list(string)", "Allowed subnet IDs", "[]", required=False
    ),
]

AZURE_STORAGE_OUTPUTS = [
    TerraformOutput("id", "The ID of the storage account", "azurerm_storage_account.this.id"),
    TerraformOutput(
        "name", "The name of the storage account", "azurerm_storage_account.this.name"
    ),
    TerraformOutput(
        "primary_blob_endpoint", "Primary blob endpoint",
        "azurerm_storage_account.this.primary_blob_endpoint",
    ),
    TerraformOutput(
        "primary_access_key", "Primary access key",
        "azurerm_storage_account.this.primary_access_key",
        sensitive=True,
    ),
]


# ══════════════════════════════════════════════════════════════════════
# GCP MODULE DEFINITIONS
# ══════════════════════════════════════════════════════════════════════

GCP_VPC_VARS = _GCP_COMMON + [
    TerraformVariable("name", "string", "Name of the VPC network"),
    TerraformVariable(
        "routing_mode", "string", "Network routing mode", '"GLOBAL"', required=False,
        validation=(
            'condition     = contains('
            '["GLOBAL", "REGIONAL"], var.routing_mode)'
            '\n    error_message = "Must be GLOBAL or REGIONAL."'
        ),
    ),
    TerraformVariable(
        "subnets",
        (
            'map(object({\n    region           = string'
            '\n    cidr             = string'
            '\n    secondary_ranges = optional(list(object({'
            '\n      name = string\n      cidr = string'
            '\n    })), [])\n  }))'
        ),
        "Subnet definitions",
        "{}",
        required=False,
    ),
    TerraformVariable("enable_nat", "bool", "Enable Cloud NAT", "true", required=False),
]

GCP_VPC_OUTPUTS = [
    TerraformOutput("network_id", "The ID of the VPC network", "google_compute_network.this.id"),
    TerraformOutput(
        "network_name", "The name of the VPC network", "google_compute_network.this.name"
    ),
    TerraformOutput(
        "subnet_ids", "Map of subnet name to ID",
        "{for k, v in google_compute_subnetwork.this : k => v.id}",
    ),
]

GCP_GCS_VARS = _GCP_COMMON + [
    TerraformVariable("bucket_name", "string", "Globally unique bucket name"),
    TerraformVariable("location", "string", "Bucket location", '"US"', required=False),
    TerraformVariable(
        "storage_class", "string", "Storage class", '"STANDARD"', required=False,
        validation=(
            'condition     = contains('
            '["STANDARD", "NEARLINE", "COLDLINE", "ARCHIVE"],'
            ' var.storage_class)'
            '\n    error_message = "Must be STANDARD,'
            ' NEARLINE, COLDLINE, or ARCHIVE."'
        ),
    ),
    TerraformVariable(
        "enable_versioning", "bool", "Enable object versioning", "true", required=False
    ),
    TerraformVariable(
        "force_destroy", "bool", "Allow bucket force destroy",
        "false", required=False,
    ),
    TerraformVariable(
        "enable_lifecycle", "bool", "Enable lifecycle rules",
        "false", required=False,
    ),
    TerraformVariable(
        "nearline_after_days", "number", "Days before nearline transition", "90",
        required=False,
    ),
    TerraformVariable(
        "expiration_days", "number", "Days before deletion (0 to disable)", "0", required=False
    ),
    TerraformVariable(
        "viewer_members", "list(string)", "IAM members with objectViewer role", "[]",
        required=False,
    ),
]

GCP_GCS_OUTPUTS = [
    TerraformOutput(
        "bucket_name", "The name of the bucket", "google_storage_bucket.this.name"
    ),
    TerraformOutput("bucket_url", "The URL of the bucket", "google_storage_bucket.this.url"),
    TerraformOutput(
        "bucket_self_link", "The self link of the bucket",
        "google_storage_bucket.this.self_link",
    ),
]


# ══════════════════════════════════════════════════════════════════════
# REGISTRY — map ModuleType to (variables, outputs)
# ══════════════════════════════════════════════════════════════════════

MODULE_DEFINITIONS: dict[
    ModuleType, tuple[list[TerraformVariable], list[TerraformOutput]]
] = {
    ModuleType.VPC: (AWS_VPC_VARS, AWS_VPC_OUTPUTS),
    ModuleType.S3_BUCKET: (AWS_S3_VARS, AWS_S3_OUTPUTS),
    ModuleType.RESOURCE_GROUP: (AZURE_RG_VARS, AZURE_RG_OUTPUTS),
    ModuleType.VNET: (AZURE_VNET_VARS, AZURE_VNET_OUTPUTS),
    ModuleType.STORAGE_ACCOUNT: (AZURE_STORAGE_VARS, AZURE_STORAGE_OUTPUTS),
    ModuleType.GCP_VPC: (GCP_VPC_VARS, GCP_VPC_OUTPUTS),
    ModuleType.GCS_BUCKET: (GCP_GCS_VARS, GCP_GCS_OUTPUTS),
}
