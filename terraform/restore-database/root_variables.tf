variable "tdr_account_number" {}
variable "database" {
  description = "The database to restore. Either consignment-api or keycloak"
}

variable "restore_time" {
  description = "Date and time in UTC format to restore the database cluster to"
  default     = ""
}

variable "cluster_identifier" {
  description = "The cluster identifier. See the README for how to find this"
}

variable "engine_version" {
  description = "The version of the new cluster. See the README for how to find this"
}