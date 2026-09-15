# Digital Small Business Banking Data Platform

[![CI](https://github.com/mrdata355/small-business-banking-data-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/mrdata355/small-business-banking-data-platform/actions/workflows/ci.yml)

A local-first data engineering platform for connected small-business banking domains:

- small-business lending applications,
- digital business-account onboarding,
- identity-verification convergence,
- treasury / ACH payment activity.

The repository contains generated data only. Resource names, environment paths and datasets are project-owned examples.

## Evidence explorer

The deployable static site under `site/` links directly to the code, schemas, tests, infrastructure, Databricks bundle, notebook source and VS Code workspace.

- [Repository](https://github.com/mrdata355/small-business-banking-data-platform)
- [VS Code Web](https://github.dev/mrdata355/small-business-banking-data-platform)
- [CI runs](https://github.com/mrdata355/small-business-banking-data-platform/actions/workflows/ci.yml)
- [Architecture](docs/ARCHITECTURE.md)
- [Data flow](docs/DATA_FLOW.md)
- [Stack map](docs/STACK.md)
- [Databricks deployment](docs/DATABRICKS.md)

## What runs locally

The complete local workflow runs with Spark in local mode and writes Parquet datasets under `runtime/`.

```text
landing
  -> bronze ingestion
  -> schema / business-rule validation
  -> quarantine
  -> watermark-backed streaming deduplication
  -> canonical current state + event history
  -> identity convergence
  -> underwriting readiness
  -> ACH canonical state
  -> treasury daily aggregates
  -> source-to-target reconciliation
```

## Quick start

```bash
docker compose build
docker compose run --rm platform
docker compose run --rm platform python scripts/show_results.py
docker compose run --rm platform pytest -q
```

Runtime outputs:

```text
runtime/lake/bronze/
runtime/lake/quarantine/
runtime/lake/silver/
runtime/lake/gold/
runtime/lake/ops/
runtime/checkpoints/
```

## VS Code

Open `small-business-banking-data-platform.code-workspace`, or use the [browser VS Code workspace](https://github.dev/mrdata355/small-business-banking-data-platform).

Core application code lives under `src/oakbridge/`. The Databricks notebook source remains intentionally thin and references the packaged application design instead of replacing it.

## Databricks

The Asset Bundle builds a Python wheel and defines:

- continuous lending application stream,
- continuous treasury / ACH stream,
- scheduled identity/onboarding convergence,
- Gold publishing,
- reconciliation.

Cloud jobs are declared paused by default so deployment does not automatically start compute.

```bash
databricks bundle validate -t dev
databricks bundle deploy -t dev
```

See [docs/DATABRICKS.md](docs/DATABRICKS.md).

## AWS mapping

Terraform covers Kinesis, S3, DynamoDB, Glue, Lambda, ECS/Fargate, EMR Serverless, CloudWatch/SNS, ECR and least-privilege IAM patterns.

The local runtime does not require AWS. Review `terraform plan` before any cloud deployment because provisioned services can incur charges.
