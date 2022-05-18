data "aws_ssm_parameter" "cost_centre" {
  name = "/sandbox/cost_centre"
}

data "aws_route53_zone" "hosted_zone" {
  name = "tdr-sandbox.nationalarchives.gov.uk"
}
