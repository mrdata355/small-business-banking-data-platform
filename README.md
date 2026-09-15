# Digital Small Business Banking Data Platform

[![CI](https://github.com/mrdata355/small-business-banking-data-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/mrdata355/small-business-banking-data-platform/actions/workflows/ci.yml)

A generated-data platform covering connected small-business banking domains:

- lending application state,
- digital business-account onboarding,
- identity-verification convergence,
- treasury / ACH activity,
- operational risk scoring,
- finance and risk-adjusted profitability,
- data-quality and pipeline observability,
- cross-department work orchestration,
- MLOps and model governance,
- semantic analytics and BI,
- deterministic scale testing and counterfactual simulation.

All data in the repository and public application is generated. Resource names, environment paths, contracts and datasets are project-owned examples.

## Public control plane

- Platform: https://small-business-banking-data-platfor.vercel.app
- Live ingestion: https://small-business-banking-data-platfor.vercel.app/live.html
- Observability: https://small-business-banking-data-platfor.vercel.app/observability.html
- Automations: https://small-business-banking-data-platfor.vercel.app/automations.html
- MLOps: https://small-business-banking-data-platfor.vercel.app/mlops.html
- Semantic / BI: https://small-business-banking-data-platfor.vercel.app/semantic.html
- Streaming lakehouse: https://small-business-banking-data-platfor.vercel.app/lakehouse.html
- Collaboration: https://small-business-banking-data-platfor.vercel.app/collaboration.html
- Digital twin: https://small-business-banking-data-platfor.vercel.app/twin.html
- Agent council: https://small-business-banking-data-platfor.vercel.app/agents.html
- Engineering tools: https://small-business-banking-data-platfor.vercel.app/tools.html

The public application persists generated events, landing-object keys, stream arrivals, clean records, quarantine records, canonical state, model predictions, treasury activity, sentiment, automation runs, deployment records, work-management metadata and operations comments in its live serving plane.

## Full local streaming platform

Run the full local stack without provisioning AWS or Databricks:

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

The stack bootstraps Kafka topics, registers JSON Schema contracts, creates S3-compatible buckets, starts the event gateway, consumes Kafka through Spark Structured Streaming, writes Delta Lake datasets, exports streaming metrics, trains/registers ML models, serves champion models and provisions dashboards.

## Streaming data path

```text
producer
  -> JSON Schema validation
  -> S3-compatible landing object
  -> Kafka topic
  -> Spark Structured Streaming
  -> event time + watermark + stable-key deduplication
  -> Bronze Delta
  -> DQ / quarantine
  -> Silver history + version-aware current-state MERGE
  -> Gold operational datasets
  -> dbt marts / feature store / BI
  -> reconciliation / monitoring / work recommendations
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

The canonical application state machine is under `src/oakbridge/domain/`. It separates delivery deduplication from business-version precedence and derives readiness from canonical prerequisites rather than arrival order.

## Finance, Risk, Quality and Reconciliation

Reusable production modules now live under:

```text
src/oakbridge/finance/          risk-adjusted profitability and attribution
src/oakbridge/risk/             exposure, concentration and stress analytics
src/oakbridge/quality/          reusable data-quality rules and scorecards
src/oakbridge/reconciliation/   row/amount/key reconciliation controls
src/oakbridge/observability/    stream metrics, SLOs and error-budget logic
```

Cross-department products and ownership are documented in [department deliverables](docs/DEPARTMENT_DELIVERABLES.md).

## dbt analytics project

`dbt/` is organized as governed sources -> staging -> incremental core -> marts -> semantic models. Current examples include lending lifecycle, ACH normalization, finance profitability, risk exposure and enterprise KPI models. Shared macros centralize safe division, freshness, boolean-rate and priority calculations.

## MLOps

The local stack includes MLflow tracking/model registry and generated-data model pipelines including:

- `application_operational_risk`
- `ach_anomaly_detector`

The MLOps layer also includes feature definitions, drift monitoring and champion/challenger promotion policy. Model promotion requires measurable quality, calibration, serving, drift and governance evidence.

See [MLOps architecture](docs/MLOPS.md).

## Observability

Prometheus scrapes the event gateway, Spark streaming listener and model API. Grafana is provisioned with the streaming platform dashboard. `src/oakbridge/observability/slo_engine.py` evaluates freshness, source lag, throughput headroom, trigger utilization, DQ reject rate and sink errors instead of treating `RUNNING` as proof of health.

The public observability application adds persistent pipeline outcome timelines, heatmaps, readiness/data-quality radar, treasury anomaly charts, prediction distributions, sentiment, deployments, GitHub commits/CI runs and operations notes.

See [observability architecture](docs/OBSERVABILITY.md).

## Collaboration and work graph

The live collaboration plane persists:

```text
departments
stakeholder_profiles
work_items
work_item_dependencies
work_item_events
work_item_comments
department_recommendations
agent_runs
```

The connected Linear project provides an external delivery surface:

https://linear.app/mrdata355/project/banking-data-platform-cross-department-delivery-ea0554167dc5

GitHub remains the code and verification system of record. The collaboration recommendation layer ranks work using business value, risk reduction, urgency, effort and dependency pressure.

## Agent mesh and digital twin

`agents/` defines 128 evidence-backed operating profiles across 16 domains and eight specialties. Core policy is deterministic; natural-language interfaces are not allowed to silently change production thresholds.

`digital_twin/` provides deterministic discrete-event simulation, paired counterfactual experiments, contract compatibility analysis, lineage blast radius and stakeholder utility gates.

## One-trillion transaction scale evidence

The repository includes a deterministic **1,000,000,000,000-record address space** in `scale/transaction_universe.py`. Any transaction ordinal can be regenerated directly without storing every previous row. CI materializes a bounded sample and publishes a manifest, root hash and determinism evidence.

This is intentionally **not** represented as one trillion physically stored development-database rows. That would consume large amounts of storage without providing better engineering evidence.

See [scale evidence](docs/SCALE_EVIDENCE.md) and `.github/workflows/scale-evidence.yml`.

## Semantic layer and Power BI

The live PostgreSQL serving plane contains semantic views for application funnel, treasury activity, pipeline quality, customer sentiment, model risk, work queue and department recommendations. The warehouse and dbt projects add governed finance/risk/management data products above those operational views.

Power BI assets are under `bi/powerbi/`:

- `oakbridge-live.pbids` — server/database definition, no credentials
- `PowerQuery.m` — semantic-view Power Query definitions

Authentication secrets are intentionally not stored in Git.

## VS Code

Open the complete repository in browser-based VS Code:

https://github.dev/mrdata355/small-business-banking-data-platform

The repository includes `small-business-banking-data-platform.code-workspace`, `.vscode/tasks.json`, `.vscode/launch.json`, `.vscode/extensions.json`, `.vscode/settings.json` and `.devcontainer/` configuration. Tasks expose baseline execution, tests, validation, full-stack Docker controls, scale evidence and Terraform verification.

## Databricks

The Asset Bundle builds a wheel and defines continuous lending/treasury jobs plus identity/onboarding convergence, Gold publishing and reconciliation. Cloud jobs are paused by default so configuration deployment does not silently start continuous paid compute.

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
notebooks/databricks/04_contract_genome.py
```

See [Databricks deployment](docs/DATABRICKS.md). Workspace-specific deep links are created only after an authenticated workspace deployment; the project does not invent links to objects that do not exist.

## AWS target architecture

Terraform covers Kinesis, S3, DynamoDB, Glue, Lambda, ECS/Fargate, EMR Serverless, CloudWatch/SNS, ECR, IAM, KMS, retention controls, budget alarms and cost-anomaly detection. Cloud provisioning is intentionally opt-in because provisioned services can incur charges.

See [cost controls](docs/COST_CONTROLS.md), [security controls](docs/SECURITY_CONTROLS.md), [production readiness](docs/PRODUCTION_READINESS.md) and [deployment targets](docs/DEPLOYMENT_TARGETS.md).

## Verification

The CI path installs Java/Python, validates repository contracts, lints code, runs unit/integration tests, executes the local Spark platform, renders execution evidence and publishes artifacts. Separate workflows validate Terraform, the Kafka -> Spark -> Delta stack and deterministic scale evidence.

PR verification is intentionally allowed to fail while defects are being fixed; the platform is only called verified after the corresponding check is green.

## All links

See [Engineering links](docs/TOOL_LINKS.md) for the consolidated list of public application routes, repository/PR/Actions/VS Code/Linear links, external tool entry points and local service consoles.
