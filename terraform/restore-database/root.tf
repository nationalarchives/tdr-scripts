resource "aws_ssm_parameter" "database_url" {
  name = "/${local.environment}/${local.db_name}/database/url"
  type = "SecureString"
  value = aws_rds_cluster.db_restore_cluster.endpoint
}

data "aws_security_group" "db_security_group" {
  name = "${local.db_name}-database-security-group-${local.environment}"
}

data "aws_db_subnet_group" "subnet_group" {
  name = local.subnet_group_name
}

resource "random_string" "identifier" {
  length = 4
  upper   = false
  special = false
}

resource "aws_rds_cluster" "db_restore_cluster" {
  restore_to_point_in_time {
    source_cluster_identifier  = "${var.database}-db-postgres-${local.environment}20200403143753331900000001"
    restore_type               = "copy-on-write"
    use_latest_restorable_time = var.restore_time == "" ? true : null
    restore_to_time = var.restore_time == "" ? null : var.restore_time
  }
  vpc_security_group_ids              = [data.aws_security_group.db_security_group.id]
  db_subnet_group_name                = data.aws_db_subnet_group.subnet_group.name
  final_snapshot_identifier = "restored-${var.database}-db-final-snapshot-${random_string.identifier.result}-${local.environment}"
  tags = local.common_tags
}

resource "aws_iam_policy" "iam_db_authentication_policy" {
  count = local.attach_new_policy_count
  policy = templatefile("./tdr-terraform-modules/iam_policy/templates/restored_db_access.json.tpl", {cluster_arn = aws_rds_cluster.db_restore_cluster.arn})
  name          = "RestoredDbAccessPolicy${title(local.environment)}"
}


data "aws_iam_role" task_role {
  name = "${local.db_name}_ecs_task_role_${local.environment}"
}

resource "aws_iam_role_policy_attachment" "attach_db_authentication_policy" {
  count = local.attach_new_policy_count
  policy_arn = aws_iam_policy.iam_db_authentication_policy[count.index].arn
  role = data.aws_iam_role.task_role.id
}