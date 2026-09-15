# Conformed dimensional warehouse

`warehouse/star_schema.sql` defines the analytical model used by generated banking data products.

## Conformed dimensions

| Dimension | Purpose |
|---|---|
| `dim_date` | shared reporting calendar |
| `dim_customer` | SCD2 customer state |
| `dim_business` | SCD2 business-borrower state |
| `dim_industry` | NAICS / public specialty mapping |
| `dim_product` | loan, deposit and treasury products |
| `dim_geography` | state, metro, county and region |
| `dim_channel` | digital, phone, file and service channels |
| `dim_status` | governed domain status values |
| `dim_document_type` | required/supporting document types |
| `dim_source_system` | source lineage and criticality |
| `dim_pipeline` | service tier, freshness and recovery objectives |
| `dim_model` | model/version lifecycle |
| `dim_department` | operating organization |
| `dim_stakeholder` | decision objective perspective |
| `dim_vendor` | external service/data provider |
| `dim_data_asset` | governed data-product catalog |

## Fact tables

The model includes lending applications and events, underwriting decisions, documents, daily balances, ACH transactions, treasury usage, customer interactions, pipeline runs, data-quality results, model predictions, deployments, work items, agent runs and management KPI snapshots.

The model separates operational current state from analytical event facts. For example:

```text
loan_application_event_raw
       -> application event history
       -> current application state
       -> fact_application_event
       -> fact_loan_application
       -> semantic lending KPIs
```

## Slowly changing dimensions

Customer and business dimensions are Type 2. The stable source key (`customer_id` or `business_id`) identifies the entity; `valid_from`, `valid_to`, `is_current` and `row_hash` preserve attribute history.

## Grain discipline

Every fact has an explicit grain. Common examples:

- `fact_loan_application`: one current analytical row per application.
- `fact_application_event`: one row per accepted delivered business event.
- `fact_ach_transaction`: one row per transaction identifier.
- `fact_account_daily_balance`: one row per account and date.
- `fact_pipeline_run`: one row per finite pipeline run.
- `fact_model_prediction`: one row per model prediction.
- `fact_work_item`: one row per collaboration work item.

The grain is part of the data contract. A grain or business-key change is treated as a breaking contract change by the Contract Genome engine.
