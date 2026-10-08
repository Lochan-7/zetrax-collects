terraform {
  required_version = ">= 1.10"

  backend "s3" {
    bucket       = "zetrax-tfstate-794692801848"
    key          = "zetrax-collects/terraform.tfstate"
    region       = "ap-southeast-1"
    encrypt      = true
    use_lockfile = true # native S3 locking, no DynamoDB table needed
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project   = "zetrax-collects"
      ManagedBy = "terraform"
    }
  }
}
