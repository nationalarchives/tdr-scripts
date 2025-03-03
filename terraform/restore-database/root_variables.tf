variable "tdr_account_number" {}
variable "database" {
  description = "The database to restore. Either consignment-api or keycloak"
}

variable "restore_time" {
  description = "Date and time in UTC format to restore the database cluster to"
  default     = ""
}

variable "instance_identifier" {
  description = "The instance identifier. See the README for how to find this"
}

variable "instance_availability_zone" {
  description = "Availability zone of the instance being restored. Either 'eu-west-2a' or 'eu-west-2b'"
}
