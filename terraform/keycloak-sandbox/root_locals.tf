locals {
  environment = var.environment
  tag_prefix  = "test-keycloak"
  aws_region  = "eu-west-2"
  # The default VPC in the Sandbox environment
  vpc_id = "vpc-05b63e6afa37144c9"
  # Public subnets in the default VPC
  subnet_ids = ["subnet-01f898273e7ae6970", "subnet-04ec47761b96a0a76", "subnet-02cebaa7c56e65a0d"]
  # We don't normally need to connect this Keycloak server to any other
  # services, so it's fine to use a placeholder URL
  frontend_url = "https://example.com"
  common_tags = tomap(
    {
      "Environment"     = var.environment,
      "Owner"           = "TDR",
      "Terraform"       = true,
      "TerraformSource" = "https://github.com/nationalarchives/tdr-scripts/tree/master/terraform/keycloak-sandbox",
      "CostCentre"      = data.aws_ssm_parameter.cost_centre.value
    }
  )
}
