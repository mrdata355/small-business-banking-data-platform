# Full local platform

Run the entire streaming platform without provisioning AWS or Databricks:

```bash
docker compose -f docker-compose.full.yml up --build
```

## Service URLs

| Component | URL | Purpose |
|---|---|---|
| Redpanda Console | http://localhost:8080 | Kafka topics, partitions and records |
| Schema Registry | http://localhost:18081 | Versioned event contracts |
| MinIO Console | http://localhost:9001 | S3-compatible data-lake buckets and objects |
| Stream Gateway | http://localhost:8000/docs | Live event producer/API |
| Spark UI | http://localhost:4040 | Structured Streaming stages/jobs |
| MLflow | http://localhost:5000 | Experiments, metrics, models, registry |
| Prometheus | http://localhost:9090 | Raw metrics/querying |
| Grafana | http://localhost:3000 | Provisioned streaming dashboards |

## Data-lake buckets

```text
oakbridge-landing
oakbridge-bronze
oakbridge-silver
oakbridge-gold
oakbridge-quarantine
oakbridge-checkpoints
oakbridge-ml-artifacts
```

## Kafka topics

```text
lending.application-events.v1
banking.business-onboarding.v1
risk.identity-verification.v1
treasury.ach-events.v1
customer.interactions.v1
ops.pipeline-events.v1
```

## Application paths

```text
s3a://oakbridge-bronze/lending/application_event/
s3a://oakbridge-silver/lending/loan_application_status_history/
s3a://oakbridge-silver/lending/loan_application/
s3a://oakbridge-quarantine/lending/application_event/
s3a://oakbridge-bronze/treasury/ach_event/
s3a://oakbridge-silver/treasury/ach_transaction/
s3a://oakbridge-checkpoints/lending/application_stream/
s3a://oakbridge-checkpoints/treasury/ach_stream/
```

The environment uses generated data only. Local MinIO credentials are development defaults and should be overridden outside a workstation/demo environment.
