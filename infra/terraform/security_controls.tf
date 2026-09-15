resource "aws_kms_key" "data" {
  description             = "${local.name_prefix} generated-data encryption key"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  tags                    = merge(local.tags, { DataClassification = "Generated" })
}

resource "aws_kms_alias" "data" {
  name          = "alias/${local.name_prefix}-data"
  target_key_id = aws_kms_key.data.key_id
}

resource "aws_cloudwatch_log_group" "platform_audit" {
  name              = "/${local.name_prefix}/platform-audit"
  retention_in_days = 30
  kms_key_id        = aws_kms_key.data.arn
  tags              = local.tags
}

resource "aws_s3_bucket_lifecycle_configuration" "data" {
  bucket = aws_s3_bucket.data.id
  rule {
    id     = "generated-raw-retention"
    status = "Enabled"
    filter { prefix = "bronze/" }
    expiration { days = var.raw_retention_days }
    noncurrent_version_expiration { noncurrent_days = 14 }
  }
  rule {
    id     = "quarantine-retention"
    status = "Enabled"
    filter { prefix = "quarantine/" }
    expiration { days = var.quarantine_retention_days }
    noncurrent_version_expiration { noncurrent_days = 7 }
  }
}
