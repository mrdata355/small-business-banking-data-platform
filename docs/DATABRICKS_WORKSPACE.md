# Databricks workspace deployment

Workspace host:

```text
https://dbc-a81c7db4-9f41.cloud.databricks.com
```

Source repository:

```text
https://github.com/mrdata355/small-business-banking-data-platform
```

Active integration branch:

```text
principal-platform-v3-real5
```

## Git folder import

Clone the repository into a Databricks Git folder so the complete repository is present in the workspace, including `src/`, `notebooks/`, `resources/`, `dbt/`, `mlops/`, `agents/`, `digital_twin/`, `warehouse/`, `sql/`, `contracts/`, `monitoring/`, `orchestration/`, and infrastructure definitions.

After cloning, switch the Git folder to `principal-platform-v3-real5` until the branch is merged to `main`.

## Bundle deployment

`databricks.yml` is configured with this workspace as the `dev` target. It packages the Python project as a wheel and deploys the jobs defined under `resources/`.

From an authenticated terminal:

```bash
./scripts/databricks_deploy.sh dev
```

Equivalent commands:

```bash
databricks auth login --host https://dbc-a81c7db4-9f41.cloud.databricks.com --profile oakbridge-dev
databricks bundle validate --target dev --profile oakbridge-dev
databricks bundle deploy --target dev --profile oakbridge-dev
```

The deployed job definitions remain paused until explicitly started so importing the project does not unexpectedly create continuous-compute cost.

## Notebook sources

Databricks notebook sources are under:

```text
notebooks/databricks/
```

The production application code remains under:

```text
src/oakbridge/
```

Notebooks call packaged modules instead of owning the production transformation logic.

## Runtime resources

The bundle currently defines:

- application Structured Streaming job
- treasury Structured Streaming job
- identity-verification convergence task
- business-onboarding task
- Gold publication task
- reconciliation task

Cloud storage and Kinesis resource names are project-owned generated architecture names. Actual AWS resources should only be connected after IAM, budget and storage controls have been reviewed.
