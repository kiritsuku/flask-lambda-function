variable "stack_name" {
  type        = string
  description = "The name of the stack that is used as a prefix for all resource names in order to identify resources that belong together."
  default     = "teststack"
}

variable "cloudwatch_logs_retention_in_days" {
  type    = number
  default = 30
}
