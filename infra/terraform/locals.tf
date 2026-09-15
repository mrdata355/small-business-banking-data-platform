locals {
  prefix = "oakbridge-${var.environment}"
  common_tags = {
    Project     = "small-business-banking-data-platform"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}
