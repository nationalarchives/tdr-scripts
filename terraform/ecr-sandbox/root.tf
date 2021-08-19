resource "aws_ecr_repository" "sandbox_ecr_repository" {
  name = "sandbox_ecr_repository"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_iam_policy" "ecr_cross_account_permission" {
  name   = "TDRECRCrossAccountPermission${title(local.environment)}"
  policy = templatefile("${path.module}/templates/ecr_cross_account_policy.json.tpl", { account_id = data.aws_ssm_parameter.management_account.value })
}

resource "aws_ecr_repository_policy" "mgmt_account_permission" {
  policy     = aws_iam_policy.ecr_cross_account_permission.policy
  repository = aws_ecr_repository.sandbox_ecr_repository.name
}
