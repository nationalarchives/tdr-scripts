locals {
  environment       = terraform.workspace
  db_name           = replace(var.database, "-", "")
  user              = local.db_name == "consignmentapi" ? "consignment_api_user" : "keycloak_user"
  aws_region        = "eu-west-2"
  assume_role       = "arn:aws:iam::${var.tdr_account_number}:role/TDRRestoreDbTerraformRole${title(local.environment)}"
  ecs_task_role     = local.db_name == "keycloak" ? "KeycloakECSTaskRole${local.environment}" : "${local.db_name}_ecs_task_role_${local.environment}"
  subnet_group_name = "${var.database}-instance-main-${local.environment}"
  common_tags = tomap(
    {
      "Environment"     = local.environment,
      "Owner"           = "TDR",
      "Terraform"       = true,
      "TerraformSource" = "https://github.com/nationalarchives/tdr-scripts/tree/master/terraform/restore-database",
      "CostCentre"      = data.aws_ssm_parameter.cost_centre.value
    }
  )
}
