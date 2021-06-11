variable "tdr_account_number" {}
variable "database" {
  description = "The database to restore. Either consignment-api or keycloak"
  default = "consignment-api"
}

variable "restore_time" {
  default = ""
}