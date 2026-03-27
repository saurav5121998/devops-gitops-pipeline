terraform {
  required_version = ">= 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.25"
    }
  }

  # Remote state — prevents "who ran terraform last?" disasters
  backend "s3" {
    bucket         = "your-terraform-state-bucket"   # change this
    key            = "gitops-pipeline/terraform.tfstate"
    region         = "ap-south-1"
    encrypt        = true
    dynamodb_table = "terraform-lock"                # prevents concurrent applies
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "devops-gitops-pipeline"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# ── VPC ──────────────────────────────────────────────────────────────────────

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.7.0"

  name = "${var.cluster_name}-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  enable_nat_gateway   = true
  single_nat_gateway   = var.environment != "prod"  # prod gets one per AZ
  enable_dns_hostnames = true

  # Required tags for EKS to discover subnets
  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
  }
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = "1"
  }
}

# ── EKS Cluster ──────────────────────────────────────────────────────────────

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "20.8.0"

  cluster_name    = var.cluster_name
  cluster_version = "1.29"

  vpc_id                         = module.vpc.vpc_id
  subnet_ids                     = module.vpc.private_subnets
  cluster_endpoint_public_access = true

  # Managed node group
  eks_managed_node_groups = {
    main = {
      name           = "main-node-group"
      instance_types = [var.node_instance_type]

      min_size     = var.environment == "prod" ? 2 : 1
      max_size     = var.environment == "prod" ? 5 : 3
      desired_size = var.environment == "prod" ? 2 : 1

      # Always use latest EKS optimised AMI
      use_latest_ami_release_version = true

      # IMDSv2 enforced — OPA policy requires this
      metadata_options = {
        http_endpoint               = "enabled"
        http_tokens                 = "required"   # IMDSv2 only
        http_put_response_hop_limit = 2
      }
    }
  }
}
