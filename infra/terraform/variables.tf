variable "environment" {
  type        = string
  description = "Environment name used in project-owned resource names."
  default     = "dev"
}

variable "aws_region" {
  type        = string
  description = "AWS deployment region."
  default     = "us-east-1"
}

variable "container_image" {
  type        = string
  description = "Container image used by the ECS reconciliation task."
  default     = "public.ecr.aws/docker/library/python:3.11-slim"
}

variable "alert_email" {
  type        = string
  description = "Optional operations email for SNS alarms. Leave empty to skip subscription."
  default     = ""
}
