data "aws_ssm_parameter" "cost_centre" {
  name = "/mgmt/cost_centre"
}

data "aws_security_group" "db_security_group" {
  name = "${local.db_name}-database-security-group-${local.environment}"
}

data "aws_db_subnet_group" "subnet_group" {
  name = local.subnet_group_name
}

data "aws_iam_role" "task_role" {
  name = "${local.db_name}_ecs_task_role_${local.environment}"
}
