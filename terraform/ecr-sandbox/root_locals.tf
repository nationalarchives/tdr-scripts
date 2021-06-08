locals {
  environment = var.environment
  aws_region  = "eu-west-2"
  common_tags = map(
    "Environment", var.environment,
    "Owner", "TDR",
    "Terraform", true,
    "TerraformSource", "https://github.com/nationalarchives/tdr-scripts/tree/master/terraform/ecr-sandbox",
    "CostCentre", data.aws_ssm_parameter.cost_centre.value
  )
}
