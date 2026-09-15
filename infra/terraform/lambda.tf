data "archive_file" "file_arrival" {
  type        = "zip"
  source_file = "${path.module}/../lambda/file_arrival_handler.py"
  output_path = "${path.module}/file_arrival_handler.zip"
}

resource "aws_lambda_function" "file_arrival" {
  function_name    = "${local.prefix}-file-arrival"
  filename         = data.archive_file.file_arrival.output_path
  source_code_hash = data.archive_file.file_arrival.output_base64sha256
  role             = aws_iam_role.lambda.arn
  handler          = "file_arrival_handler.handler"
  runtime          = "python3.11"
  timeout          = 30
  memory_size      = 256

  environment {
    variables = {
      MANIFEST_TABLE = aws_dynamodb_table.ingestion_manifest.name
    }
  }
}
