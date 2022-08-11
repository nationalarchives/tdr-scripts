data "aws_ssm_parameter" "cost_centre" {
  name = "/mgmt/cost_centre"
}

data "aws_ami" "amazon_linux_ami" {
  owners      = ["amazon"]
  name_regex  = "^amzn2-ami-hvm-2.0.\\d{8}.0-x86_64-gp2$"
  most_recent = true
}

data "aws_rds_cluster" "consignment_api" {
  cluster_identifier = split(".", data.aws_ssm_parameter.database_url.value)[0]
}

data "aws_ssm_parameter" "database_url" {
  name = "/${local.environment}/${var.service}/database/url"
}

data "aws_ssm_parameter" "database_username" {
  name = "/${local.environment}/${var.service}/database/username"
}

data "aws_ssm_parameter" "database_password" {
  name = "/${local.environment}/${var.service}/database/password"
}

data "aws_ssm_parameter" "mgmt_account_number" {
  name = "/mgmt/management_account"
}

data "aws_subnet" "private_subnet" {
  tags = {
    "Name" = "tdr-efs-private-subnet-backend-checks-efs-0-${local.environment}"
  }
}

data "aws_caller_identity" "current" {}

data "aws_efs_file_system" "backend_checks_file_system" {
  tags = {
    Name = "tdr-backend-checks-efs-${local.environment}"
  }
}

data "aws_efs_file_system" "export_file_system" {
  tags = {
    Name = "tdr-export-efs-${local.environment}"
  }
}

data "aws_iam_role" "bastion_role" {
  name = "BastionEC2Role${title(local.environment)}"
}

data "aws_vpc" "vpc" {
  tags = {
    Name = "tdr-vpc-${local.environment}"
  }
}

data "aws_security_group" "db_security_group" {
  name = "tdr-consignment-api-database-instance-${local.environment}"
}

data "aws_security_group" "efs_backend_checks_security_group" {
  name = "backend-checks-efs-mount-target-security-group"
}

data "aws_security_group" "efs_export_security_group" {
  name = "export-efs-mount-target-security-group"
}
