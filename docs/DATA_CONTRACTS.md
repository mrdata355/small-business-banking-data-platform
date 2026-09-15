# Data contracts

## Lending application event

Schema: `contracts/application_event_v1.schema.json`

Kafka subject: `lending.application-events.v1-value`

Kafka topic: `lending.application-events.v1`

Landing object convention:

```text
landing/lending/application-events/event_date=2026-09-15/application_id=APP-3F12A9A1/EVT-8D2A66CEB201.json
```

Bronze Delta table:

```text
oakbridge_prod.bronze_lending.loan_application_event_raw
```

Current-state Silver table:

```text
oakbridge_prod.silver_lending.loan_application
```

History table:

```text
oakbridge_prod.silver_lending.loan_application_status_history
```

Primary business key: `application_id`

Delivery deduplication key: `event_id`

State precedence: `event_version DESC, event_ts DESC`

Event-time column: `event_ts`

Checkpoint:

```text
s3://oakbridge-prod-stream-state-us-east-1/checkpoints/lending/application_stream/v1/
```

## Treasury ACH event

Schema: `contracts/ach_event_v1.schema.json`

Kafka subject: `treasury.ach-events.v1-value`

Kafka topic: `treasury.ach-events.v1`

Landing object convention:

```text
landing/treasury/ach-events/event_date=2026-09-15/business_id=BIZ-9D34B101/ACH-A73BE10F6D2C.json
```

Bronze Delta table:

```text
oakbridge_prod.bronze_treasury.ach_event_raw
```

Silver table:

```text
oakbridge_prod.silver_treasury.ach_transaction
```

Delivery deduplication key: `transaction_id`

Event-time column: `event_ts`

Checkpoint:

```text
s3://oakbridge-prod-stream-state-us-east-1/checkpoints/treasury/ach_stream/v1/
```

## Data quality

Invalid records are retained rather than silently dropped. The quarantine record contains the original payload, source metadata, event key, ingestion time and `dq_reason`.

Quarantine prefix:

```text
s3://oakbridge-prod-data-us-east-1/quarantine/<domain>/<entity>/dq_reason=<reason>/event_date=YYYY-MM-DD/
```
