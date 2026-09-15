# Domain model

## Lending

`loan_application`
- one current row per `application_id`
- event history retained separately
- readiness derived from canonical prerequisites

`loan_application_status_history`
- one row per accepted state event
- delivery key `event_id`
- event version and event time retained for replay and audit

## Customer / business

`customer`
- customer identity and KYC state
- sensitive attributes restricted and masked/tokenized in lower-trust environments

`business`
- legal entity, NAICS, formation and account relationship attributes

`guarantor_relationship`
- relationship bridge between customer and business entities

## Risk

`identity_verification`
- latest identity-verification result per application/customer

## Treasury

`ach_transaction`
- one accepted payment event per `transaction_id`
- direction, amount, SEC code, status and tokenized counterparty

## Operations

`data_quality_result`
- contract and business-rule outcomes

`pipeline_reconciliation`
- source/target accounting by domain and run

`stream_health`
- lag, freshness, throughput, state and sink status

`model_monitoring`
- model version, prediction distribution, latency and drift/quality metrics
