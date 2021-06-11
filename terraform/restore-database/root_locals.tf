locals {
  environment = terraform.workspace
  db_name = replace(var.database,"-","")
  attach_new_policy_count = var.database == "consignment-api" ? 1 : 0
  aws_region  = "eu-west-2"
  assume_role = "arn:aws:iam::${var.tdr_account_number}:role/TDRRestoreDbTerraformRole${title(local.environment)}"
  subnet_group_name = var.database == "keyckloak" ? "main-${local.environment}" : "tdr-${local.environment}"
  common_tags = map(
    "Environment", local.environment,
    "Owner", "TDR",
    "Terraform", true,
    "TerraformSource", "https://github.com/nationalarchives/tdr-scripts/tree/master/terraform/restore-database",
    "CostCentre", data.aws_ssm_parameter.cost_centre.value
  )
}
