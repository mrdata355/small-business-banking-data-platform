resource "aws_ecr_repository" "platform" {
  name                 = "${local.prefix}-banking-data-platform"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}
