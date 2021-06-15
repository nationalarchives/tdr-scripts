resource "aws_ssm_parameter" "database_url" {
  name      = "/${local.environment}/${local.db_name}/database/url"
  type      = "SecureString"
  value     = aws_rds_cluster.db_restore_cluster.endpoint
  overwrite = true
}

resource "random_string" "identifier" {
  length  = 4
  upper   = false
  special = false
}

resource "aws_rds_cluster" "db_restore_cluster" {
  restore_to_point_in_time {
    source_cluster_identifier  = var.cluster_identifier
    restore_type               = "copy-on-write"
    use_latest_restorable_time = var.restore_time == "" ? true : null
    restore_to_time            = var.restore_time == "" ? null : var.restore_time
  }
  vpc_security_group_ids              = [data.aws_security_group.db_security_group.id]
  engine                              = "aurora-postgresql"
  iam_database_authentication_enabled = true
  db_subnet_group_name                = data.aws_db_subnet_group.subnet_group.name
  database_name                       = local.db_name
  final_snapshot_identifier           = "restored-${var.database}-final-snapshot-${random_string.identifier.result}-${local.environment}"
  tags                                = local.common_tags
}

resource "aws_rds_cluster_instance" "atabase_instance" {
  count                = 1
  identifier_prefix    = "db-postgres-instance-${local.environment}"
  cluster_identifier   = aws_rds_cluster.db_restore_cluster.id
  engine               = "aurora-postgresql"
  engine_version       = "11.9"
  instance_class       = "db.t3.medium"
  db_subnet_group_name = data.aws_db_subnet_group.subnet_group.name
}

resource "aws_iam_policy" "iam_db_authentication_policy" {
  count  = local.attach_new_policy_count
  policy = templatefile("./tdr-terraform-modules/iam_policy/templates/restored_db_access.json.tpl", { cluster_arn = "arn:aws:rds-db:${local.aws_region}:${var.tdr_account_number}:dbuser:${aws_rds_cluster.db_restore_cluster.cluster_resource_id}/consignment_api_user" })
  name   = "RestoredDbAccessPolicy${title(local.environment)}"
}

resource "aws_iam_role_policy_attachment" "attach_db_authentication_policy" {
  count      = local.attach_new_policy_count
  policy_arn = aws_iam_policy.iam_db_authentication_policy[count.index].arn
  role       = data.aws_iam_role.task_role.id
}