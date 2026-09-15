locals {
  prefix      = "oakbridge-${var.environment}"
  name_prefix = local.prefix

  common_tags = {
    Project        = "small-business-banking-data-platform"
    Environment    = var.environment
    ManagedBy      = "terraform"
    DataClass      = "Generated"
    CostAllocation = "oakbridge"
  }

  tags = local.common_tags
}
