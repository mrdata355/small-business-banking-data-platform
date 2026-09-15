resource "aws_kinesis_stream" "application_events" {
  name            = "oakbridge-${var.environment}-${var.aws_region}-lending-application-events-v1"
  encryption_type = "KMS"
  kms_key_id      = "alias/aws/kinesis"

  stream_mode_details {
    stream_mode = "ON_DEMAND"
  }
}

resource "aws_kinesis_stream" "ach_events" {
  name            = "oakbridge-${var.environment}-${var.aws_region}-treasury-ach-events-v1"
  encryption_type = "KMS"
  kms_key_id      = "alias/aws/kinesis"

  stream_mode_details {
    stream_mode = "ON_DEMAND"
  }
}
