output "application_event_stream" {
  value = aws_kinesis_stream.application_events.name
}

output "ach_event_stream" {
  value = aws_kinesis_stream.ach_events.name
}

output "data_bucket" {
  value = aws_s3_bucket.data.bucket
}

output "stream_state_bucket" {
  value = aws_s3_bucket.stream_state.bucket
}

output "glue_database" {
  value = aws_glue_catalog_database.banking.name
}

output "emr_serverless_application_id" {
  value = aws_emrserverless_application.spark.id
}

output "ecs_cluster" {
  value = aws_ecs_cluster.platform.name
}
