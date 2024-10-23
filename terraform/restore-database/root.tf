module "global_parameters" {
  source = "./tdr-configurations/terraform"
}

resource "aws_ssm_parameter" "database_url" {
  name  = "/${local.environment}/${local.db_name}/database/url"
  type  = "SecureString"
  value = aws_db_instance.restore_db_instance.endpoint
}

resource "random_string" "identifier" {
  length  = 10
  upper   = false
  special = false
}

resource "aws_db_instance" "restore_db_instance" {
  restore_to_point_in_time {
    source_db_instance_identifier = var.instance_identifier
    use_latest_restorable_time    = var.restore_time == "" ? true : null
    restore_time                  = var.restore_time == "" ? null : var.restore_time
  }
  identifier_prefix                   = var.database
  identifier                          = random_string.identifier.result
  instance_class                      = "db.t3.medium"
  db_subnet_group_name                = data.aws_db_subnet_group.subnet_group.name
  db_name                             = var.restore_time == "" ? local.db_name : null
  final_snapshot_identifier           = "restored-${var.database}-final-snapshot-${random_string.identifier.result}-${local.environment}"
  iam_database_authentication_enabled = true
  vpc_security_group_ids              = [data.aws_security_group.db_security_group.id]
  availability_zone                   = var.instance_availability_zone
}

resource "aws_iam_policy" "iam_db_authentication_policy" {
  policy = templatefile("./tdr-terraform-modules/iam_policy/templates/restored_db_access.json.tpl", { cluster_arn = "arn:aws:rds-db:${local.aws_region}:${var.tdr_account_number}:dbuser:${aws_db_instance.restore_db_instance.resource_id}/${local.user}" })
  name   = "RestoredDbAccessPolicy${title(local.environment)}"
}

resource "aws_iam_role_policy_attachment" "attach_db_authentication_policy" {
  policy_arn = aws_iam_policy.iam_db_authentication_policy[count.index].arn
  role       = data.aws_iam_role.task_role.id
}
