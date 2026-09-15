# Automations

The platform supports both user-triggered persistent internet demo automations and local production-equivalent services.

## Internet demo automations

- landing batch ingestion
- treasury event burst
- application risk scoring sweep
- customer interaction / sentiment generation
- event replay / duplicate handling
- invalid-event quarantine validation

Runs are written to `automation_runs` with timestamps, status and record counts.

## Local stack automations

- topic creation at environment startup
- JSON Schema registration at startup
- MinIO bucket creation and access policy initialization
- continuous Kafka to Spark streaming
- checkpointed Delta writes
- Prometheus service discovery
- Grafana dashboard provisioning
- MLflow experiment/model registration

Cloud infrastructure remains opt-in. Nothing in the local stack automatically provisions paid AWS or Databricks compute.
