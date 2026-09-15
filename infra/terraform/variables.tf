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

variable "monthly_budget_usd" {
  type        = number
  description = "Monthly budget guardrail for optional cloud deployment."
  default     = 100
  validation {
    condition     = var.monthly_budget_usd > 0 && var.monthly_budget_usd <= 5000
    error_message = "monthly_budget_usd must be greater than 0 and no more than 5000 for this reference environment."
  }
}

variable "cost_anomaly_threshold_usd" {
  type        = number
  description = "Absolute anomaly impact that triggers cost investigation."
  default     = 20
}

variable "raw_retention_days" {
  type        = number
  description = "Default project retention for generated raw data."
  default     = 90
}

variable "quarantine_retention_days" {
  type        = number
  description = "Default project retention for generated quarantined records."
  default     = 30
}
