provider "aws" {
  region = local.aws_region
  assume_role {
    role_arn     = local.assume_role
    session_name = "restore-db"
    external_id  = module.global_parameters.external_ids.restore_db
  }
}
