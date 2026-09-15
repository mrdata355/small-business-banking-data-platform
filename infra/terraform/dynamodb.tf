resource "aws_dynamodb_table" "ingestion_manifest" {
  name         = "oakbridge-${var.environment}-ingestion-manifest"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "file_id"

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  attribute {
    name = "file_id"
    type = "S"
  }
}
