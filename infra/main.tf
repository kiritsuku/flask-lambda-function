data "aws_region" "current" {}

locals {
  region = data.aws_region.current.name

  # Some default tags that should be added to all resources
  tags = {
    Description = "Managed by Terraform"
  }
}

provider "aws" {
  profile = "demo-user"
}

