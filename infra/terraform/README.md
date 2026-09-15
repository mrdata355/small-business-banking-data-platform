# AWS infrastructure

This directory maps the platform to AWS services.

| Service | Responsibility |
|---|---|
| Kinesis | real-time lending and ACH event transport |
| S3 | landing, Bronze, quarantine and checkpoint/state storage |
| DynamoDB | ingestion manifest / idempotency metadata |
| Glue Data Catalog + crawler | metadata discovery over the data lake |
| Lambda | lightweight file-arrival manifest registration |
| ECS/Fargate | containerized finite jobs such as reconciliation |
| EMR Serverless | optional managed Spark execution path |
| CloudWatch + SNS | logs, metrics and operational alerts |
| ECR | container image repository |

The local project does not require any AWS resources. `terraform apply` creates cloud resources and can incur charges.

Typical review flow:

```bash
terraform init
terraform fmt -check
terraform validate
terraform plan -var environment=dev
```

Only run `terraform apply` after reviewing the plan, IAM scope and cost implications.
