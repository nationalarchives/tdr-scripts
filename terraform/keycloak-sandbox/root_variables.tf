variable "environment" {
  default = "sandbox"
}

variable "notification_sns_topic" {
  description = "SNS topic arn for notifications"
  default     = ""
}
