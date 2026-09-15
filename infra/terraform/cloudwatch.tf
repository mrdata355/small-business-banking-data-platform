resource "aws_sns_topic" "data_platform_alerts" {
  name = "${local.prefix}-data-platform-alerts"
}

resource "aws_sns_topic_subscription" "email" {
  count     = var.alert_email == "" ? 0 : 1
  topic_arn = aws_sns_topic.data_platform_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${local.prefix}-file-arrival"
  retention_in_days = 14
}

resource "aws_cloudwatch_metric_alarm" "kinesis_write_throttle" {
  alarm_name          = "${local.prefix}-kinesis-write-throttle"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "WriteProvisionedThroughputExceeded"
  namespace           = "AWS/Kinesis"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_actions       = [aws_sns_topic.data_platform_alerts.arn]

  dimensions = {
    StreamName = aws_kinesis_stream.application_events.name
  }
}
