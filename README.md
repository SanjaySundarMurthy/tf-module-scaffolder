# tf-module-scaffolder

<p align="center">
  <strong>Generate production-ready Terraform modules in seconds</strong>
</p>

<p align="center">
  <a href="https://github.com/SanjaySundarMurthy/tf-module-scaffolder/actions"><img src="https://github.com/SanjaySundarMurthy/tf-module-scaffolder/workflows/CI/badge.svg" alt="CI"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.9%2B-blue.svg" alt="Python 3.9+"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License"></a>
</p>

---

## Overview

**tf-module-scaffolder** is a CLI tool that generates best-practice Terraform module structures with a single command. It creates complete, production-ready module scaffolds with proper file layout, documentation, CI/CD pipelines, linting configuration, and example code — all following HashiCorp and community conventions.

### Why?

Starting a new Terraform module involves creating 10-15+ files with boilerplate and best practices. This tool does it in seconds while ensuring consistency across your module library.

## Features

- **Multi-Cloud Support** — AWS, Azure, and GCP module templates
- **16 Module Templates** — Pre-built for VPC, S3, VNet, Storage Account, GCS, and more
- **Production-Ready Structure** — `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`, `provider.tf`
- **Variable Validation** — Built-in validation rules for common patterns (CIDR, naming, etc.)
- **CI/CD Pipeline** — GitHub Actions workflow for `terraform validate` + `tflint`
- **Pre-commit Hooks** — `terraform fmt`, `validate`, `tflint`, `terraform-docs`
- **TFLint Configuration** — Provider-specific linting rules out of the box
- **Example Code** — Ready-to-use example configurations
- **Test Scaffolding** — Terratest structure for module testing
- **Beautiful CLI** — Rich terminal output with file tree visualization
- **Three Modes** — Interactive wizard, CLI flags, or quickstart presets

## Installation

```bash
# Clone the repository
git clone https://github.com/SanjaySundarMurthy/tf-module-scaffolder.git
cd tf-module-scaffolder

# Install in development mode
pip install -e ".[dev]"
```

## Quick Start

### Quickstart Presets

```bash
# Scaffold an AWS VPC module
tf-scaffold quickstart aws-vpc

# Scaffold an Azure Storage Account module
tf-scaffold quickstart azure-storage

# Scaffold a GCP VPC module with custom name
tf-scaffold quickstart gcp-vpc -n my-network
```

### Non-Interactive Mode

```bash
# AWS S3 bucket module
tf-scaffold new -p aws -t s3-bucket -n my-s3-module

# Azure VNet module with custom options
tf-scaffold new -p azure -t vnet -n my-vnet -d "Production VNet" -a "Platform Team"

# GCP module with minimal scaffold
tf-scaffold new -p gcp -t gcs-bucket -n my-bucket --no-ci --no-precommit
```

### Interactive Mode

```bash
tf-scaffold new
```

This launches an interactive wizard that guides you through:
1. Selecting a cloud provider (AWS / Azure / GCP)
2. Choosing a module template
3. Naming your module
4. Generating the complete file structure

## Available Templates

### AWS
| Template | Description |
|----------|-------------|
| `vpc` | VPC with public/private subnets, NAT Gateway, and flow logs |
| `s3-bucket` | S3 bucket with versioning, encryption, and lifecycle rules |
| `eks-cluster` | EKS cluster with managed node groups |
| `lambda-function` | Lambda function with IAM role and CloudWatch |
| `rds-instance` | RDS instance with parameter groups and subnet groups |

### Azure
| Template | Description |
|----------|-------------|
| `resource-group` | Resource group with management lock |
| `vnet` | Virtual network with subnets and NSGs |
| `aks-cluster` | AKS cluster with node pools |
| `storage-account` | Storage account with containers and lifecycle |
| `app-service` | App Service with plan and deployment slots |

### GCP
| Template | Description |
|----------|-------------|
| `gcp-vpc` | VPC network with subnets, Cloud NAT, and firewall |
| `gke-cluster` | GKE cluster with node pools |
| `gcs-bucket` | Cloud Storage bucket with lifecycle and IAM |
| `cloud-run` | Cloud Run service with IAM |
| `cloud-sql` | Cloud SQL instance with databases |

## Generated Structure

```
terraform-aws-vpc/
├── main.tf                    # Core resources
├── variables.tf               # Input variable definitions
├── outputs.tf                 # Output value definitions
├── versions.tf                # Terraform & provider version constraints
├── provider.tf                # Provider configuration
├── README.md                  # Module documentation
├── Makefile                   # Common Terraform commands
├── .gitignore                 # Terraform-specific ignores
├── .tflint.hcl                # TFLint configuration
├── .pre-commit-config.yaml    # Pre-commit hooks
├── .github/
│   └── workflows/
│       └── ci.yml             # GitHub Actions CI/CD
├── examples/
│   └── basic/
│       └── main.tf            # Example usage
└── tests/
    └── main.tf                # Test configuration
```

## CLI Reference

```
Usage: tf-scaffold [OPTIONS] COMMAND [ARGS]...

Commands:
  list        List available module templates
  new         Scaffold a new Terraform module
  quickstart  Quick-scaffold a module from a preset

Options:
  --version  Show the version and exit
  --help     Show this message and exit
```

### `tf-scaffold new` Options

| Option | Description |
|--------|-------------|
| `-p, --provider` | Cloud provider: `aws`, `azure`, `gcp` |
| `-t, --template` | Module template name |
| `-n, --name` | Module name |
| `-o, --output-dir` | Output directory (default: current) |
| `-d, --description` | Module description |
| `-a, --author` | Author name |
| `--no-examples` | Skip examples directory |
| `--no-tests` | Skip tests directory |
| `--no-ci` | Skip CI workflow |
| `--no-precommit` | Skip pre-commit config |
| `--no-makefile` | Skip Makefile |

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest -v

# Lint
ruff check .

# Format check
ruff format --check .
```

## Architecture

```
tf_module_scaffolder/
├── models.py            # Data models (Provider, ModuleType, Config)
├── engine.py            # Scaffold engine (file generation)
├── cli.py               # Click CLI commands
├── templates/
│   ├── hcl.py           # Jinja2 HCL templates
│   └── definitions.py   # Variable/output definitions
└── output/
    └── console.py       # Rich console rendering
```

## Author

**Sanjay S** — Senior DevOps Engineer  
[GitHub](https://github.com/SanjaySundarMurthy) · [Portfolio](https://sanjaysundarmurthy-portfolio.vercel.app/)

## License

MIT License — see [LICENSE](LICENSE) for details.
