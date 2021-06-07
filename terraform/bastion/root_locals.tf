locals {
  environment = terraform.workspace
  assume_role = "arn:aws:iam::${var.tdr_account_number}:role/TDRScriptsTerraformRole${title(local.environment)}"
  common_tags = map(
    "Environment", local.environment,
    "Owner", "TDR",
    "Terraform", true,
    "TerraformSource", "https://github.com/nationalarchives/tdr-scripts/tree/master/terraform/bastion",
    "CostCentre", data.aws_ssm_parameter.cost_centre.value,
  )
}
