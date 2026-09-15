# Production path mapping

The following names are architecture examples for this project.

```text
Kinesis
oakbridge-prod-us-east-1-lending-application-events-v1
oakbridge-prod-us-east-1-treasury-ach-events-v1

S3
s3://oakbridge-prod-data-us-east-1/landing/
s3://oakbridge-prod-data-us-east-1/bronze/
s3://oakbridge-prod-data-us-east-1/quarantine/
s3://oakbridge-prod-stream-state-us-east-1/checkpoints/

Unity Catalog / Delta
oakbridge_prod.silver_customer.business
oakbridge_prod.silver_customer.customer
oakbridge_prod.silver_lending.loan_application
oakbridge_prod.silver_lending.loan_application_status_history
oakbridge_prod.silver_risk.identity_verification
oakbridge_prod.silver_treasury.ach_transaction
oakbridge_prod.gold_lending.underwriting_readiness_queue
oakbridge_prod.gold_treasury.activity_daily
oakbridge_prod.ops.pipeline_reconciliation
```

These are illustrative project names, not private banking infrastructure.
