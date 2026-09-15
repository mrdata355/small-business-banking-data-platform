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

resource "aws_s3_bucket_public_access_block" "data" {
  bucket                  = aws_s3_bucket.data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "stream_state" {
  bucket                  = aws_s3_bucket.stream_state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id
  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.data.arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "stream_state" {
  bucket = aws_s3_bucket.stream_state.id
  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.data.arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_versioning" "stream_state" {
  bucket = aws_s3_bucket.stream_state.id
  versioning_configuration { status = "Enabled" }
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
