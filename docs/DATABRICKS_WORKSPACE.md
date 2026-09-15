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

`databricks.yml` points the `dev` target at this workspace. The bundle deploys Unity Catalog schemas, Lakeflow pipelines, Workflows jobs, notebooks, and the packaged Python project.

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

## Unity Catalog schema resources

The development bundle defines the following schemas in the selected catalog:

```text
bronze_lending
bronze_treasury
bronze_customer
bronze_risk
silver_lending
silver_treasury
silver_customer
silver_risk
gold_lending
gold_treasury
gold_customer
feature_store
semantic
ops
```

## Lakeflow pipelines

The bundle defines these serverless pipeline resources:

```text
oakbridge-lending-bronze-dev
oakbridge-lending-silver-dev
oakbridge-treasury-bronze-dev
oakbridge-treasury-silver-dev
oakbridge-lending-gold-dev
oakbridge-treasury-gold-dev
oakbridge-platform-ops-dev
```

Pipeline source code is stored under:

```text
src/oakbridge/lakeflow/
```

The orchestration job `oakbridge-lakeflow-medallion-refresh-dev` refreshes Bronze -> Silver -> Gold and then the operations layer with explicit task dependencies.

## Workflow jobs

The original production-style jobs remain defined for application streaming, treasury streaming, identity ingestion, onboarding, Gold publication, and reconciliation.

Additional serverless jobs are defined for:

```text
oakbridge-development-bootstrap-dev
oakbridge-reconciliation-control-tower-dev
oakbridge-finance-management-dev
oakbridge-feature-model-monitoring-dev
oakbridge-full-development-refresh-dev
```

The development bootstrap creates generated lending, ACH, and identity records in Delta tables so the workspace has data to inspect without using customer data.

## Notebook sources

Databricks notebook sources are under:

```text
notebooks/databricks/
```

Current notebooks include platform walkthrough, lakehouse inspection, stream monitoring, MLflow inspection, contract compatibility, generated development data, reconciliation controls, finance profitability, feature engineering, model monitoring, management KPIs, and platform asset health.

The production application code remains under:

```text
src/oakbridge/
```

Notebooks are operational and analytical entry points; core pipeline logic remains in version-controlled Python modules.

## Cost behavior

Bundle deployment creates definitions. It does not require the continuous workloads to run. The Lakeflow pipelines are configured as triggered rather than continuous, and the operational jobs have no automatic schedule unless one is added explicitly.

Running notebooks, jobs, or pipeline refreshes may consume Databricks compute or serverless quota. Cloud storage and Kinesis resource names in this repository are project-owned generated architecture names; actual AWS resources should only be connected after IAM, budget, and storage controls have been reviewed.
