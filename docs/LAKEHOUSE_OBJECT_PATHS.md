# Lakehouse object paths

## Local S3-compatible runtime

```text
s3a://oakbridge-landing/lending/application-events/event_date=YYYY-MM-DD/*.json
s3a://oakbridge-landing/treasury/ach-events/event_date=YYYY-MM-DD/*.json

s3a://oakbridge-bronze/lending/application_event/
s3a://oakbridge-bronze/treasury/ach_event/

s3a://oakbridge-silver/lending/loan_application_status_history/
s3a://oakbridge-silver/lending/loan_application/
s3a://oakbridge-silver/treasury/ach_transaction/

s3a://oakbridge-gold/lending/underwriting_readiness_queue/
s3a://oakbridge-gold/treasury/activity_daily/

s3a://oakbridge-quarantine/lending/application_event/dq_reason=<reason>/

s3a://oakbridge-checkpoints/lending/application_stream/
s3a://oakbridge-checkpoints/treasury/ach_stream/

s3a://oakbridge-ml-artifacts/
```

## Cloud resource mapping

```text
s3://oakbridge-prod-data-us-east-1/landing/lending/application-events/
s3://oakbridge-prod-data-us-east-1/landing/treasury/ach-events/
s3://oakbridge-prod-data-us-east-1/bronze/lending/loan_application_event_raw/
s3://oakbridge-prod-data-us-east-1/silver/lending/loan_application/
s3://oakbridge-prod-data-us-east-1/gold/lending/underwriting_readiness_queue/
s3://oakbridge-prod-data-us-east-1/quarantine/lending/application-events/
s3://oakbridge-prod-stream-state-us-east-1/checkpoints/
```

## Catalog contracts

```text
oakbridge_prod.bronze_lending.loan_application_event_raw
oakbridge_prod.bronze_treasury.ach_event_raw
oakbridge_prod.silver_lending.loan_application_status_history
oakbridge_prod.silver_lending.loan_application
oakbridge_prod.silver_customer.customer
oakbridge_prod.silver_customer.business
oakbridge_prod.silver_risk.identity_verification
oakbridge_prod.silver_treasury.ach_transaction
oakbridge_prod.gold_lending.underwriting_readiness_queue
oakbridge_prod.gold_treasury.activity_daily
oakbridge_prod.ops.pipeline_reconciliation
oakbridge_prod.ops.data_quality_result
```
