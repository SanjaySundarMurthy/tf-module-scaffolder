"""Terraform file templates — Jinja2-based HCL generation."""

from __future__ import annotations

# ══════════════════════════════════════════════════════════════════════
# VERSIONS.TF
# ══════════════════════════════════════════════════════════════════════

VERSIONS_TF = """\
terraform {
  required_version = ">= {{ min_terraform_version }}"

  required_providers {
    {{ provider }} = {
      source  = "{{ provider_source }}"
      version = ">= {{ min_provider_version }}"
    }
  }
}
"""

# ══════════════════════════════════════════════════════════════════════
# PROVIDER CONFIGS
# ══════════════════════════════════════════════════════════════════════

PROVIDER_AWS = """\
provider "aws" {
  region = var.region

  default_tags {
    tags = var.tags
  }
}
"""

PROVIDER_AZURE = """\
provider "azurerm" {
  features {}
}
"""

PROVIDER_GCP = """\
provider "google" {
  project = var.project_id
  region  = var.region
}
"""

# ══════════════════════════════════════════════════════════════════════
# BLANK MODULE
# ══════════════════════════════════════════════════════════════════════

BLANK_MAIN = """\
# {{ module_name }}
# {{ description }}
#
# This is a blank Terraform module scaffold.
# Add your resources below.

"""

BLANK_VARIABLES = """\
{% for var in variables %}
variable "{{ var.name }}" {
  description = "{{ var.description }}"
  type        = {{ var.type }}
{% if var.default is not none %}
  default     = {{ var.default }}
{% endif %}
{% if var.sensitive %}
  sensitive   = true
{% endif %}
{% if var.validation %}

  validation {
    {{ var.validation }}
  }
{% endif %}
}
{% endfor %}
"""

BLANK_OUTPUTS = """\
{% for out in outputs %}
output "{{ out.name }}" {
  description = "{{ out.description }}"
  value       = {{ out.value }}
{% if out.sensitive %}
  sensitive   = true
{% endif %}
}
{% endfor %}
"""

# ══════════════════════════════════════════════════════════════════════
# AWS TEMPLATES
# ══════════════════════════════════════════════════════════════════════

AWS_VPC_MAIN = """\
# {{ module_name }} — AWS VPC Module
# {{ description }}

data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  azs = slice(data.aws_availability_zones.available.names, 0, var.az_count)
}

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = merge(var.tags, {
    Name = var.name
  })
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = merge(var.tags, {
    Name = "${var.name}-igw"
  })
}

resource "aws_subnet" "public" {
  count = var.az_count

  vpc_id                  = aws_vpc.this.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = local.azs[count.index]
  map_public_ip_on_launch = true

  tags = merge(var.tags, {
    Name = "${var.name}-public-${local.azs[count.index]}"
    Tier = "Public"
  })
}

resource "aws_subnet" "private" {
  count = var.az_count

  vpc_id            = aws_vpc.this.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + var.az_count)
  availability_zone = local.azs[count.index]

  tags = merge(var.tags, {
    Name = "${var.name}-private-${local.azs[count.index]}"
    Tier = "Private"
  })
}

resource "aws_eip" "nat" {
  count  = var.enable_nat_gateway ? 1 : 0
  domain = "vpc"

  tags = merge(var.tags, {
    Name = "${var.name}-nat-eip"
  })
}

resource "aws_nat_gateway" "this" {
  count = var.enable_nat_gateway ? 1 : 0

  allocation_id = aws_eip.nat[0].id
  subnet_id     = aws_subnet.public[0].id

  tags = merge(var.tags, {
    Name = "${var.name}-nat"
  })

  depends_on = [aws_internet_gateway.this]
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }

  tags = merge(var.tags, {
    Name = "${var.name}-public-rt"
  })
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.this.id

  dynamic "route" {
    for_each = var.enable_nat_gateway ? [1] : []
    content {
      cidr_block     = "0.0.0.0/0"
      nat_gateway_id = aws_nat_gateway.this[0].id
    }
  }

  tags = merge(var.tags, {
    Name = "${var.name}-private-rt"
  })
}

resource "aws_route_table_association" "public" {
  count = var.az_count

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count = var.az_count

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

resource "aws_flow_log" "this" {
  count = var.enable_flow_logs ? 1 : 0

  vpc_id               = aws_vpc.this.id
  traffic_type         = "ALL"
  log_destination_type = "cloud-watch-logs"
  log_destination      = aws_cloudwatch_log_group.flow_logs[0].arn
  iam_role_arn         = aws_iam_role.flow_logs[0].arn
}

resource "aws_cloudwatch_log_group" "flow_logs" {
  count = var.enable_flow_logs ? 1 : 0

  name              = "/aws/vpc/flow-logs/${var.name}"
  retention_in_days = var.flow_log_retention_days
}

resource "aws_iam_role" "flow_logs" {
  count = var.enable_flow_logs ? 1 : 0

  name = "${var.name}-flow-logs-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "vpc-flow-logs.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "flow_logs" {
  count = var.enable_flow_logs ? 1 : 0

  name = "${var.name}-flow-logs-policy"
  role = aws_iam_role.flow_logs[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
      ]
      Effect   = "Allow"
      Resource = "*"
    }]
  })
}
"""

AWS_S3_MAIN = """\
# {{ module_name }} — AWS S3 Bucket Module
# {{ description }}

resource "aws_s3_bucket" "this" {
  bucket        = var.bucket_name
  force_destroy = var.force_destroy

  tags = merge(var.tags, {
    Name = var.bucket_name
  })
}

resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id

  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Suspended"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.kms_key_arn != "" ? "aws:kms" : "AES256"
      kms_master_key_id = var.kms_key_arn != "" ? var.kms_key_arn : null
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "this" {
  bucket = aws_s3_bucket.this.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "this" {
  count  = var.enable_lifecycle ? 1 : 0
  bucket = aws_s3_bucket.this.id

  rule {
    id     = "transition-to-ia"
    status = "Enabled"

    transition {
      days          = var.transition_ia_days
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = var.transition_glacier_days
      storage_class = "GLACIER"
    }

    expiration {
      days = var.expiration_days
    }

    noncurrent_version_expiration {
      noncurrent_days = var.noncurrent_expiration_days
    }
  }
}
"""

# ══════════════════════════════════════════════════════════════════════
# AZURE TEMPLATES
# ══════════════════════════════════════════════════════════════════════

AZURE_RG_MAIN = """\
# {{ module_name }} — Azure Resource Group Module
# {{ description }}

resource "azurerm_resource_group" "this" {
  name     = var.name
  location = var.location

  tags = merge(var.tags, {
    ManagedBy = "Terraform"
  })
}

resource "azurerm_management_lock" "this" {
  count = var.enable_delete_lock ? 1 : 0

  name       = "${var.name}-delete-lock"
  scope      = azurerm_resource_group.this.id
  lock_level = "CanNotDelete"
  notes      = "Resource group protected from accidental deletion"
}
"""

AZURE_VNET_MAIN = """\
# {{ module_name }} — Azure Virtual Network Module
# {{ description }}

resource "azurerm_virtual_network" "this" {
  name                = var.name
  location            = var.location
  resource_group_name = var.resource_group_name
  address_space       = var.address_space

  tags = merge(var.tags, {
    ManagedBy = "Terraform"
  })
}

resource "azurerm_subnet" "this" {
  for_each = var.subnets

  name                 = each.key
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.this.name
  address_prefixes     = [each.value.address_prefix]

  dynamic "delegation" {
    for_each = each.value.delegation != null ? [each.value.delegation] : []
    content {
      name = delegation.value.name
      service_delegation {
        name    = delegation.value.service
        actions = delegation.value.actions
      }
    }
  }
}

resource "azurerm_network_security_group" "this" {
  for_each = { for k, v in var.subnets : k => v if v.create_nsg }

  name                = "${each.key}-nsg"
  location            = var.location
  resource_group_name = var.resource_group_name

  tags = merge(var.tags, {
    Subnet = each.key
  })
}

resource "azurerm_subnet_network_security_group_association" "this" {
  for_each = { for k, v in var.subnets : k => v if v.create_nsg }

  subnet_id                 = azurerm_subnet.this[each.key].id
  network_security_group_id = azurerm_network_security_group.this[each.key].id
}
"""

AZURE_STORAGE_MAIN = """\
# {{ module_name }} — Azure Storage Account Module
# {{ description }}

resource "azurerm_storage_account" "this" {
  name                     = var.name
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = var.account_tier
  account_replication_type = var.replication_type
  account_kind             = var.account_kind
  min_tls_version          = "TLS1_2"
  https_traffic_only_enabled = true

  blob_properties {
    versioning_enabled = var.enable_versioning

    dynamic "delete_retention_policy" {
      for_each = var.soft_delete_days > 0 ? [1] : []
      content {
        days = var.soft_delete_days
      }
    }
  }

  dynamic "network_rules" {
    for_each = var.enable_network_rules ? [1] : []
    content {
      default_action             = "Deny"
      ip_rules                   = var.allowed_ip_ranges
      virtual_network_subnet_ids = var.allowed_subnet_ids
      bypass                     = ["AzureServices"]
    }
  }

  tags = merge(var.tags, {
    ManagedBy = "Terraform"
  })
}

resource "azurerm_storage_container" "this" {
  for_each = toset(var.containers)

  name                  = each.value
  storage_account_id    = azurerm_storage_account.this.id
  container_access_type = "private"
}

resource "azurerm_storage_management_policy" "this" {
  count = var.enable_lifecycle ? 1 : 0

  storage_account_id = azurerm_storage_account.this.id

  rule {
    name    = "move-to-cool"
    enabled = true

    filters {
      blob_types = ["blockBlob"]
    }

    actions {
      base_blob {
        tier_to_cool_after_days_since_modification_greater_than = var.cool_after_days
      }
    }
  }
}
"""

# ══════════════════════════════════════════════════════════════════════
# GCP TEMPLATES
# ══════════════════════════════════════════════════════════════════════

GCP_VPC_MAIN = """\
# {{ module_name }} — GCP VPC Network Module
# {{ description }}

resource "google_compute_network" "this" {
  name                    = var.name
  project                 = var.project_id
  auto_create_subnetworks = false
  routing_mode            = var.routing_mode
}

resource "google_compute_subnetwork" "this" {
  for_each = var.subnets

  name          = each.key
  project       = var.project_id
  region        = each.value.region
  network       = google_compute_network.this.id
  ip_cidr_range = each.value.cidr

  dynamic "secondary_ip_range" {
    for_each = each.value.secondary_ranges
    content {
      range_name    = secondary_ip_range.value.name
      ip_cidr_range = secondary_ip_range.value.cidr
    }
  }

  private_ip_google_access = true
}

resource "google_compute_router" "this" {
  count = var.enable_nat ? 1 : 0

  name    = "${var.name}-router"
  project = var.project_id
  region  = var.region
  network = google_compute_network.this.id
}

resource "google_compute_router_nat" "this" {
  count = var.enable_nat ? 1 : 0

  name                               = "${var.name}-nat"
  project                            = var.project_id
  router                             = google_compute_router.this[0].name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

resource "google_compute_firewall" "allow_internal" {
  name    = "${var.name}-allow-internal"
  project = var.project_id
  network = google_compute_network.this.id

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "icmp"
  }

  source_ranges = [for s in google_compute_subnetwork.this : s.ip_cidr_range]
}
"""

GCP_GCS_MAIN = """\
# {{ module_name }} — GCP Cloud Storage Bucket Module
# {{ description }}

resource "google_storage_bucket" "this" {
  name          = var.bucket_name
  project       = var.project_id
  location      = var.location
  storage_class = var.storage_class
  force_destroy = var.force_destroy

  uniform_bucket_level_access = true

  versioning {
    enabled = var.enable_versioning
  }

  dynamic "lifecycle_rule" {
    for_each = var.enable_lifecycle ? [1] : []
    content {
      action {
        type          = "SetStorageClass"
        storage_class = "NEARLINE"
      }
      condition {
        age = var.nearline_after_days
      }
    }
  }

  dynamic "lifecycle_rule" {
    for_each = var.expiration_days > 0 ? [1] : []
    content {
      action {
        type = "Delete"
      }
      condition {
        age = var.expiration_days
      }
    }
  }

  labels = var.labels
}

resource "google_storage_bucket_iam_member" "viewers" {
  for_each = toset(var.viewer_members)

  bucket = google_storage_bucket.this.name
  role   = "roles/storage.objectViewer"
  member = each.value
}
"""

# ══════════════════════════════════════════════════════════════════════
# SUPPORTING FILES
# ══════════════════════════════════════════════════════════════════════

MAKEFILE = """\
.PHONY: init validate plan fmt lint docs clean test

init:
\tterraform init

validate: init
\tterraform validate

plan: init
\tterraform plan

fmt:
\tterraform fmt -recursive

lint:
\ttflint --init
\ttflint

docs:
\tterraform-docs markdown table . > README.md

clean:
\trm -rf .terraform .terraform.lock.hcl

test:
\tcd tests && terraform init && terraform validate
"""

PRECOMMIT_CONFIG = """\
repos:
  - repo: https://github.com/antonbabenko/pre-commit-tf
    rev: v1.96.1
    hooks:
      - id: terraform_fmt
      - id: terraform_validate
      - id: terraform_tflint
        args:
          - --args=--config=__GIT_WORKING_DIR__/.tflint.hcl
      - id: terraform_docs
        args:
          - --hook-config=--path-to-file=README.md
          - --hook-config=--add-to-existing-file=true
          - --hook-config=--create-file-if-not-exist=true

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-merge-conflict
"""

TFLINT_CONFIG = """\
plugin "terraform" {
  enabled = true
  preset  = "recommended"
}

{% if provider == "aws" %}
plugin "aws" {
  enabled = true
  version = "0.33.0"
  source  = "github.com/terraform-linters/tflint-ruleset-aws"
}
{% elif provider == "azurerm" %}
plugin "azurerm" {
  enabled = true
  version = "0.27.0"
  source  = "github.com/terraform-linters/tflint-ruleset-azurerm"
}
{% elif provider == "google" %}
plugin "google" {
  enabled = true
  version = "0.30.0"
  source  = "github.com/terraform-linters/tflint-ruleset-google"
}
{% endif %}

rule "terraform_naming_convention" {
  enabled = true
}

rule "terraform_documented_variables" {
  enabled = true
}

rule "terraform_documented_outputs" {
  enabled = true
}
"""

TERRATEST_MAIN = """\
# Test configuration for {{ module_name }}
# Validates that the module initializes and plans successfully.

terraform {
  required_version = ">= {{ min_terraform_version }}"
}

module "test" {
  source = "../"

  {{ test_vars }}
}
"""

CI_GITHUB_ACTIONS = """\
name: Terraform Module CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  validate:
    name: Validate
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: "1.7"

      - name: Terraform Format
        run: terraform fmt -check -recursive

      - name: Terraform Init
        run: terraform init -backend=false

      - name: Terraform Validate
        run: terraform validate

  tflint:
    name: TFLint
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup TFLint
        uses: terraform-linters/setup-tflint@v4

      - name: Init TFLint
        run: tflint --init

      - name: Run TFLint
        run: tflint --format=compact

  docs:
    name: Docs Check
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: terraform-docs
        uses: terraform-docs/gh-actions@v1
        with:
          working-dir: .
          output-method: inject
          fail-on-diff: true
"""

EXAMPLE_MAIN = """\
# Example usage of {{ module_name }}

{{ provider_block }}

module "{{ module_slug }}" {
  source = "../"

  {{ example_vars }}
}

{{ example_outputs }}
"""

MODULE_README = """\
# {{ module_name }}

{{ description }}

## Usage

```hcl
module "{{ module_slug }}" {
  source = "{{ source_path }}"

  {{ example_vars }}
}
```

## Requirements

| Name | Version |
|------|---------|
| terraform | >= {{ min_terraform_version }} |
| {{ provider }} | >= {{ min_provider_version }} |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
{# fmt: off #}
{% for var in variables -%}
| {{ var.name }} | {{ var.description }} | `{{ var.type }}` | {{ "`" + var.default + "`" if var.default is not none else "n/a" }} | {{ "no" if not var.required else "yes" }} |
{% endfor %}

## Outputs

| Name | Description |
|------|-------------|
{% for out in outputs %}| {{ out.name }} | {{ out.description }} |
{% endfor %}

## License

MIT License

## Author

{{ author }}
"""
