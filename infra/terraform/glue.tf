resource "aws_glue_catalog_database" "banking" {
  name        = "${replace(local.prefix, "-", "_")}_banking"
  description = "Catalog database for the small-business banking data platform."
}

resource "aws_glue_crawler" "bronze" {
  name          = "${local.prefix}-bronze-crawler"
  database_name = aws_glue_catalog_database.banking.name
  role          = aws_iam_role.glue.arn

  s3_target {
    path = "s3://${aws_s3_bucket.data.bucket}/bronze/"
  }

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }
}
