# Semantic layer

The semantic layer exposes stable business definitions independently from raw transport schemas.

Core business entities:

- `dim_business`
- `dim_customer`
- `fct_loan_application`
- `fct_ach_transaction`
- `fct_pipeline_quality`

Core measures:

- applications_submitted
- applications_ready_for_underwriting
- total_requested_amount
- ach_credit_amount
- ach_debit_amount
- ach_return_rate
- quarantine_rate
- duplicate_delivery_rate
- p95_freshness_seconds

The SQL definitions under `semantic/sql/` are the source of truth for BI tools. Power BI connection material is under `bi/powerbi/`.
