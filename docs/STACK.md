# Platform stack

| Layer | Technology | Repository evidence |
|---|---|---|
| application code | Python 3.11 | `src/oakbridge/`, `services/` |
| distributed processing | PySpark / Spark Structured Streaming | `src/oakbridge/jobs/` |
| local event transport | Redpanda (Kafka API) | `docker-compose.full.yml`, `infra/local/redpanda-init.sh` |
| schema registry | Redpanda Schema Registry + JSON Schema | `contracts/`, `infra/local/register-schemas.py` |
| local object lake | MinIO (S3 API) | `docker-compose.full.yml`, `infra/local/minio-init.sh` |
| lakehouse format | Delta Lake | `src/oakbridge/jobs/kafka_lakehouse_stream.py` |
| live public serving plane | Neon PostgreSQL + Data API | `sql/live/`, `site/` |
| cloud lake | Amazon S3 | `infra/terraform/s3.tf` |
| cloud event transport | Amazon Kinesis | `infra/terraform/kinesis.tf` |
| operational NoSQL | DynamoDB | `infra/terraform/dynamodb.tf` |
| catalog | AWS Glue | `infra/terraform/glue.tf` |
| event function | AWS Lambda | `infra/lambda/`, `infra/terraform/lambda.tf` |
| container workloads | Amazon ECS/Fargate | `infra/terraform/ecs.tf` |
| managed Spark alternative | EMR Serverless | `infra/terraform/emr_serverless.tf` |
| lakehouse deployment | Databricks Asset Bundles + Unity Catalog patterns | `databricks.yml`, `resources/`, `src/oakbridge/databricks/`, `notebooks/databricks/` |
| workflow orchestration | Airflow | `orchestration/dags/` |
| model tracking / registry | MLflow | `mlops/`, `docker-compose.full.yml` |
| model serving | FastAPI + MLflow champion aliases | `services/model_api.py` |
| model training | scikit-learn | `mlops/train_models.py` |
| metrics | Prometheus | `monitoring/prometheus/` |
| dashboards | Grafana | `monitoring/grafana/` |
| live observability | Vercel + Neon + Chart.js | `site/observability.html`, `site/observability.js` |
| automation console | Vercel + Neon functions | `site/automations.html`, `site/automations.js` |
| semantic layer | PostgreSQL semantic views + metric definitions | `semantic/` |
| BI integration | Power BI `.pbids` + Power Query M | `bi/powerbi/` |
| SQL contracts | SQL / Delta DDL | `sql/` |
| infrastructure as code | Terraform | `infra/terraform/` |
| local reproducibility | Docker / Compose | `Dockerfile`, `docker-compose.yml`, `docker-compose.full.yml` |
| CI | GitHub Actions | `.github/workflows/ci.yml` |
| development workspace | VS Code | `.vscode/`, `.code-workspace`, `.devcontainer/` |
| public platform | static web application | `site/`, `vercel.json` |
