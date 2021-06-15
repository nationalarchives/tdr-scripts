variable "tdr_account_number" {}
variable "database" {
  description = "The database to restore. Either consignment-api or keycloak"
}

variable "restore_time" {
  description = "Date and time in UTC format to restore the database cluster to"
  default     = ""
}

variable "cluster_identifier" {
  default = "The cluster identifier. See the README for how to find this"
}
