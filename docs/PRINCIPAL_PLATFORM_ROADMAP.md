# Platform capability map

This document tracks implemented platform capabilities and their executable entry points.

## Runtime planes

- Live internet demo: Vercel + Neon Data API
- Local streaming: Redpanda (Kafka API) + Spark Structured Streaming
- Local object lake: MinIO (S3 API)
- Lakehouse tables: Delta Lake Bronze / Silver / Gold / Quarantine / Ops
- Orchestration: Airflow DAGs and task entry points
- MLOps: MLflow experiment tracking, registered models, batch scoring jobs
- Observability: Prometheus metrics, Grafana dashboards, live web observability page
- Contracts: versioned JSON Schema + Redpanda Schema Registry bootstrap
- Semantic layer: dbt models/metrics + curated SQL views
- BI: Power BI connection templates and semantic view definitions

## Safety / cost defaults

Cloud infrastructure is represented as code but is not automatically provisioned. The complete streaming path can be run locally using Docker Compose. Persistent public demo data is generated only by user actions in the web console.
