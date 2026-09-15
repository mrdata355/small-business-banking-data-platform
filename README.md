# Digital Small Business Banking Data Platform

[![CI](https://github.com/mrdata355/small-business-banking-data-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/mrdata355/small-business-banking-data-platform/actions/workflows/ci.yml)

A generated-data platform covering connected small-business banking domains:

- lending application state,
- digital business-account onboarding,
- identity-verification convergence,
- treasury / ACH activity,
- operational risk scoring,
- data-quality and pipeline observability,
- semantic analytics and BI.

All data in the repository and public application is generated. Resource names, environment paths, contracts and datasets are project-owned examples.

## Public control plane

- Platform: https://small-business-banking-data-platfor.vercel.app
- Live ingestion: https://small-business-banking-data-platfor.vercel.app/live.html
- Observability: https://small-business-banking-data-platfor.vercel.app/observability.html
- Automations: https://small-business-banking-data-platfor.vercel.app/automations.html
- MLOps: https://small-business-banking-data-platfor.vercel.app/mlops.html
- Semantic / BI: https://small-business-banking-data-platfor.vercel.app/semantic.html
- Streaming lakehouse: https://small-business-banking-data-platfor.vercel.app/lakehouse.html

The public application persists generated events, landing-object keys, stream arrivals, clean records, quarantine records, canonical state, model predictions, treasury activity, sentiment, automation runs, deployment records and operations comments in its live data backend.

## Full local streaming platform

Run the production-equivalent local stack without provisioning AWS or Databricks:

```bash
docker compose -f docker-compose.full.yml up --build
```

Services:

| Component | Local endpoint |
|---|---|
| Redpanda Kafka API | `localhost:19092` |
| Redpanda Console | `http://localhost:8080` |
| Schema Registry | `http://localhost:18081` |
| MinIO S3 API | `http://localhost:9000` |
| MinIO Console | `http://localhost:9001` |
| Stream Gateway API | `http://localhost:8000/docs` |
| Spark UI | `http://localhost:4040` |
| Spark metrics | `http://localhost:9108` |
| MLflow | `http://localhost:5000` |
| Model API | `http://localhost:8010/docs` |
| Prometheus | `http://localhost:9090` |
| Grafana | `http://localhost:3000` |

The stack bootstraps Kafka topics, registers JSON Schema contracts, creates S3-compatible buckets, starts the event gateway, consumes Kafka through Spark Structured Streaming, writes Delta Lake datasets, tracks streaming metrics, trains/registers ML models, serves champion models and provisions dashboards.

## Streaming data path

```text
producer
  -> JSON Schema validation
  -> S3-compatible landing object
  -> Kafka topic
  -> Spark Structured Streaming
  -> watermark + stable-key deduplication
  -> Bronze Delta
  -> DQ / quarantine
  -> Silver history + version-aware current-state MERGE
  -> Gold operational datasets
  -> reconciliation / monitoring
```

Lending paths:

```text
s3a://oakbridge-bronze/lending/application_event/
s3a://oakbridge-silver/lending/loan_application_status_history/
s3a://oakbridge-silver/lending/loan_application/
s3a://oakbridge-gold/lending/underwriting_readiness_queue/
s3a://oakbridge-quarantine/lending/application_event/
s3a://oakbridge-checkpoints/lending/application_stream/v1/
```

Treasury paths:

```text
s3a://oakbridge-bronze/treasury/ach_event/
s3a://oakbridge-silver/treasury/ach_transaction/
s3a://oakbridge-gold/treasury/activity_daily/
s3a://oakbridge-checkpoints/treasury/ach_stream/v1/
```

See [lakehouse object paths](docs/LAKEHOUSE_OBJECT_PATHS.md), [catalog namespaces](docs/SCHEMA_NAMES.md), [data contracts](docs/DATA_CONTRACTS.md) and [file naming](docs/FILE_NAMING.md).

## Event contracts

Versioned contracts live under `contracts/` and are registered into the local schema registry at startup.

Kafka topics:

```text
lending.application-events.v1
banking.business-onboarding.v1
risk.identity-verification.v1
treasury.ach-events.v1
customer.interactions.v1
ops.pipeline-events.v1
```

## MLOps

The local stack includes MLflow tracking/model registry and two generated-data model pipelines:

- `application_operational_risk`
- `ach_anomaly_detector`

`mlops/train_models.py` trains, logs and registers both models. Current registered versions receive the `champion` alias. `services/model_api.py` serves the champion aliases and exports Prometheus metrics.

See [MLOps architecture](docs/MLOPS.md).

## Observability

Prometheus scrapes the event gateway, Spark streaming listener and model API. Grafana is provisioned with the streaming platform dashboard. The public observability application adds persistent pipeline outcome timelines, heatmaps, readiness/data-quality radar, treasury anomaly charts, prediction distributions, sentiment, deployments, GitHub commits/CI runs and operations notes.

See [observability architecture](docs/OBSERVABILITY.md).

## Semantic layer and Power BI

The live PostgreSQL serving plane contains these semantic views:

```text
public.sem_application_funnel
public.sem_treasury_activity
public.sem_pipeline_quality
public.sem_customer_sentiment
public.sem_model_risk
```

Power BI assets are under `bi/powerbi/`:

- `oakbridge-live.pbids` — server/database definition, no credentials
- `PowerQuery.m` — semantic-view Power Query definitions

Authentication secrets are intentionally not stored in Git.

## VS Code

Open the complete repository in browser-based VS Code:

https://github.dev/mrdata355/small-business-banking-data-platform

The repository also contains `small-business-banking-data-platform.code-workspace`, `.vscode/` and `.devcontainer/` configuration.

## Databricks

The Asset Bundle builds a wheel and defines continuous lending/treasury jobs plus identity/onboarding convergence, Gold publishing and reconciliation. Cloud jobs are paused by default so deploying configuration does not automatically start continuous compute.

```bash
databricks bundle validate -t dev
databricks bundle deploy -t dev
```

Source notebooks:

```text
notebooks/databricks/00_platform_walkthrough.py
notebooks/databricks/01_lakehouse_tables.py
notebooks/databricks/02_stream_monitoring.py
notebooks/databricks/03_mlflow_models.py
```

See [Databricks deployment](docs/DATABRICKS.md). Workspace-specific deep links are created only after deployment into an authenticated workspace.

## AWS target architecture

Terraform covers Kinesis, S3, DynamoDB, Glue, Lambda, ECS/Fargate, EMR Serverless, CloudWatch/SNS, ECR and IAM patterns. Cloud provisioning is intentionally not automatic because provisioned services can incur charges.

See [cost controls](docs/COST_CONTROLS.md), [security controls](docs/SECURITY_CONTROLS.md), [production readiness](docs/PRODUCTION_READINESS.md) and [deployment targets](docs/DEPLOYMENT_TARGETS.md).

## Verified baseline pipeline

The repository's standard CI path installs Java/Python, runs lint/tests, executes the baseline Spark data platform, renders execution evidence and publishes verification artefacts. See [verification](docs/VERIFICATION.md) and GitHub Actions for the current run history.
