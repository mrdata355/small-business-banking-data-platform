resource "aws_emrserverless_application" "spark" {
  name          = "${local.prefix}-spark"
  release_label = "emr-7.1.0"
  type          = "SPARK"

  auto_start_configuration {
    enabled = true
  }

  auto_stop_configuration {
    enabled              = true
    idle_timeout_minutes = 10
  }
}
