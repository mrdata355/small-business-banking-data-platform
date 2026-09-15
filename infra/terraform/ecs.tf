resource "aws_ecs_cluster" "platform" {
  name = "${local.prefix}-data-platform"
}

resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/${local.prefix}-data-platform"
  retention_in_days = 14
}

resource "aws_ecs_task_definition" "reconciliation" {
  family                   = "${local.prefix}-reconciliation"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.platform_task.arn

  container_definitions = jsonencode([
    {
      name      = "reconciliation"
      image     = var.container_image
      essential = true
      command   = ["python", "-m", "oakbridge.jobs.reconciliation"]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.ecs.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "reconciliation"
        }
      }
    }
  ])
}
