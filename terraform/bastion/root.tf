module "encryption_key" {
  source      = "./tdr-terraform-modules/kms"
  project     = var.project
  function    = "bastion-encryption"
  environment = local.environment
  common_tags = local.common_tags
}

resource "aws_iam_role" "bastion_db_connect_role" {
  name               = "TDRBastionAccessDbRole${title(local.environment)}"
  assume_role_policy = templatefile("${path.module}/templates/bastion_access_db_assume_role.json.tpl", { account_id = data.aws_caller_identity.current.account_id, environment = title(local.environment) })
}

resource "aws_iam_policy" "bastion_db_connect_policy" {
  name   = "TDRBastionAccessDbPolicy${title(local.environment)}"
  policy = templatefile("${path.module}/templates/bastion_access_db_policy.json.tpl", { account_id = data.aws_caller_identity.current.account_id, cluster_id = data.aws_rds_cluster.consignment_api.cluster_resource_id })
}

resource "aws_iam_role_policy_attachment" "db_connect_policy_attach" {
  policy_arn = aws_iam_policy.bastion_db_connect_policy.arn
  role       = aws_iam_role.bastion_db_connect_role.id
}

resource "aws_iam_policy" "bastion_assume_role_policy" {
  name   = "TDRBastionAssumeDbRolePolicy${title(local.environment)}"
  policy = templatefile("${path.module}/templates/bastion_assume_role.json.tpl", { role_arn = aws_iam_role.bastion_db_connect_role.arn })
}

data "aws_db_instance" "instance" {
  db_instance_identifier = tolist(data.aws_rds_cluster.consignment_api.cluster_members)[0]
}

resource "aws_iam_role_policy_attachment" "bastion_assumne_db_role_attach" {
  policy_arn = aws_iam_policy.bastion_assume_role_policy.arn
  role       = module.bastion_ec2_instance.role_id
}

resource "aws_iam_role" "tdr_jenkins_run_ssm_document_role" {
  name               = "TDRJenkinsRunDocumentRole${title(local.environment)}"
  assume_role_policy = templatefile("${path.module}/templates/assume_role_policy.json.tpl", { account_id = data.aws_ssm_parameter.mgmt_account_number.value })
}

resource "aws_iam_policy" "tdr_jenkins_run_ssm_document_policy" {
  name   = "TDRJenkinsRunDocumentPolicy${title(local.environment)}"
  policy = templatefile("${path.module}/templates/run_ssm_delete_user.json.tpl", { account_id = data.aws_caller_identity.current.account_id })
}

resource "aws_iam_role" "jenkins_describe_ec2_role" {
  name               = "TDRJenkinsDescribeEC2Role${title(local.environment)}"
  assume_role_policy = templatefile("${path.module}/templates/assume_role_policy.json.tpl", { account_id = data.aws_ssm_parameter.mgmt_account_number.value })
}

resource "aws_iam_policy" "jenkins_describe_ec2_policy" {
  name   = "TDRJenkinsDescribeEC2Policy${title(local.environment)}"
  policy = templatefile("${path.module}/templates/run_ec2_describe.json.tpl", {})
}

resource "aws_iam_role_policy_attachment" "jenkins_describe_ec2_attach" {
  policy_arn = aws_iam_policy.jenkins_describe_ec2_policy.arn
  role       = aws_iam_role.jenkins_describe_ec2_role.id
}

resource "aws_iam_role_policy_attachment" "tdr_jenkins_run_ssm_attach" {
  policy_arn = aws_iam_policy.tdr_jenkins_run_ssm_document_policy.arn
  role       = aws_iam_role.tdr_jenkins_run_ssm_document_role.id
}

module "bastion_ami" {
  source      = "./tdr-terraform-modules/ami"
  project     = var.project
  function    = "bastion-ec2"
  environment = local.environment
  common_tags = local.common_tags
  region      = var.default_aws_region
  kms_key_id  = module.encryption_key.kms_key_arn
  source_ami  = data.aws_ami.amazon_linux_ami.id
}


module "bastion_ec2_instance" {
  source              = "./tdr-terraform-modules/ec2"
  common_tags         = local.common_tags
  environment         = local.environment
  name                = "bastion"
  user_data           = "user_data_postgres"
  user_data_variables = { db_host = split(":", data.aws_db_instance.instance.endpoint)[0], account_number = data.aws_caller_identity.current.account_id, environment = title(local.environment) }
  ami_id              = module.bastion_ami.encrypted_ami_id
  security_group_id   = data.aws_security_group.db_security_group.id
  subnet_id           = data.aws_subnet.private_subnet.id
  public_key          = var.public_key
}

module "bastion_delete_user_document" {
  source              = "./tdr-terraform-modules/ssm_document"
  content_template    = "bastion_delete_user"
  document_name       = "deleteuser"
  template_parameters = { db_host = data.aws_ssm_parameter.database_url.value, db_username = data.aws_ssm_parameter.database_username.value, db_password = data.aws_ssm_parameter.database_password.value }
}
