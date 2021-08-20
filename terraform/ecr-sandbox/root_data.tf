data "aws_ssm_parameter" "cost_centre" {
  name = "/sandbox/cost_centre"
}

data "aws_ssm_parameter" "management_account" {
  name = "/mgmt/management_account"
}
