# Architecture

## Domains

### Lending applications
Real-time application state changes are modeled as events. `application_id` is the business key, `event_id` is the delivery-deduplication key, and `event_version` plus `event_ts` determine current-state precedence.

### Digital business onboarding
Generated customer/business onboarding records include identity, EIN/TIN tokens, NAICS, formation data, addresses, account product, and KYC state. Raw tax identifiers are intentionally not included.

### Treasury / ACH
Generated ACH payment events are keyed by `transaction_id` and include business/account identifiers, amount, direction, SEC code, status, and tokenized counterparty reference.

## Layers

```text
landing
  -> bronze
  -> quarantine (invalid records)
  -> silver canonical/current state
  -> gold operational/aggregate outputs
  -> ops reconciliation
```

## Local and cloud adapters

The local profile uses filesystem streams and Parquet so the complete workflow runs without cloud resources.

The AWS/Databricks profile maps the same logical contracts to Kinesis, S3, Delta/Unity Catalog, and managed job orchestration.

## Correctness controls

- explicit schemas
- stable business and delivery keys
- watermark-backed streaming deduplication
- canonical precedence using event version/time
- quarantine rather than silent dropping
- replayable bronze data
- source-to-target reconciliation
- idempotent current-state writes
- testable Python modules outside notebooks
