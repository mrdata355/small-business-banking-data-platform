# Engineering links

## Public platform surfaces

- Platform home: https://small-business-banking-data-platfor.vercel.app
- Live ingestion/event evidence: https://small-business-banking-data-platfor.vercel.app/live.html
- Observability: https://small-business-banking-data-platfor.vercel.app/observability.html
- Automations: https://small-business-banking-data-platfor.vercel.app/automations.html
- Streaming lakehouse: https://small-business-banking-data-platfor.vercel.app/lakehouse.html
- MLOps: https://small-business-banking-data-platfor.vercel.app/mlops.html
- Semantic / BI: https://small-business-banking-data-platfor.vercel.app/semantic.html
- Collaboration: https://small-business-banking-data-platfor.vercel.app/collaboration.html
- Digital twin: https://small-business-banking-data-platfor.vercel.app/twin.html
- Agent council: https://small-business-banking-data-platfor.vercel.app/agents.html
- Tool portal: https://small-business-banking-data-platfor.vercel.app/tools.html

## Source and delivery

- GitHub repository: https://github.com/mrdata355/small-business-banking-data-platform
- Platform expansion PR: https://github.com/mrdata355/small-business-banking-data-platform/pull/1
- GitHub Actions: https://github.com/mrdata355/small-business-banking-data-platform/actions
- VS Code Web: https://github.dev/mrdata355/small-business-banking-data-platform
- Linear delivery project: https://linear.app/mrdata355/project/banking-data-platform-cross-department-delivery-ea0554167dc5

## External product entry points

- Databricks account console: https://accounts.cloud.databricks.com/
- Power BI: https://app.powerbi.com/
- AWS Console: https://console.aws.amazon.com/console/home?region=us-east-1

## Local full-stack endpoints

These URLs resolve after `docker compose -f docker-compose.full.yml up --build` runs on the same machine:

- Redpanda Console: http://localhost:8080
- Schema Registry: http://localhost:18081
- MinIO S3 API: http://localhost:9000
- MinIO Console: http://localhost:9001
- Stream Gateway OpenAPI: http://localhost:8000/docs
- Spark UI: http://localhost:4040
- Spark metrics: http://localhost:9108/metrics
- MLflow: http://localhost:5000
- Model API: http://localhost:8010/docs
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

Workspace-specific Databricks notebook deep links are only valid after an authenticated bundle deployment creates those notebook/workspace objects. The repository never invents a workspace URL that does not exist.
