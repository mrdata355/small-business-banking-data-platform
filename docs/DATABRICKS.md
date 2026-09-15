# Databricks deployment

The Databricks Asset Bundle builds the Python package as a wheel and deploys three jobs:

- continuous lending application stream,
- continuous treasury / ACH stream,
- hourly identity/onboarding convergence, Gold publishing and reconciliation.

The streaming jobs are deployed paused by default. This prevents accidental compute spend during setup.

## Validate

```bash
databricks bundle validate -t dev
```

## Deploy

```bash
databricks bundle deploy -t dev
```

## Start intentionally

Use the Databricks Jobs UI or CLI only after the catalog, S3 paths, IAM and Kinesis streams exist and have been reviewed.

Production target values are declared separately from development values in `databricks.yml`.
