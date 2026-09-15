# Platform stack

| Layer | Technology | Repository evidence |
|---|---|---|
| application code | Python 3.11 | `src/oakbridge/` |
| distributed processing | PySpark / Spark Structured Streaming | `src/oakbridge/jobs/` |
| local data lake | Parquet | `runtime/lake/` at execution time |
| cloud lake | Amazon S3 | `infra/terraform/s3.tf` |
| event transport | Amazon Kinesis | `infra/terraform/kinesis.tf` |
| operational NoSQL | DynamoDB | `infra/terraform/dynamodb.tf` |
| catalog | AWS Glue | `infra/terraform/glue.tf` |
| event function | AWS Lambda | `infra/lambda/`, `infra/terraform/lambda.tf` |
| container workloads | Amazon ECS/Fargate | `infra/terraform/ecs.tf` |
| managed Spark alternative | EMR Serverless | `infra/terraform/emr_serverless.tf` |
| lakehouse deployment | Databricks + Unity Catalog patterns | `databricks.yml`, `resources/`, `src/oakbridge/databricks/` |
| workflow orchestration | Airflow | `orchestration/dags/` |
| SQL contracts | SQL / Delta DDL | `sql/` |
| infrastructure as code | Terraform | `infra/terraform/` |
| local reproducibility | Docker / Compose | `Dockerfile`, `docker-compose.yml` |
| CI | GitHub Actions | `.github/workflows/ci.yml` |
| development workspace | VS Code | `.vscode/`, `.code-workspace`, `.devcontainer/` |
| showcase | static web application | `site/`, `vercel.json` |
