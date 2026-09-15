# Security controls

## Data handling

- generated data only in the repository and public demo
- no raw SSN, TIN or EIN values; sensitive identifiers are tokenized
- explicit data classifications for PII, financial and compliance fields
- no credentials in Git
- secrets supplied through environment variables or managed secret stores

## Access design

- least-privilege service identities
- separate landing, bronze, silver, gold, quarantine and checkpoint storage boundaries
- read-only BI access separated from ingestion and merge identities
- catalog/schema access aligned to data classification

## Reliability and change control

- versioned contracts
- schema registry
- idempotent producer configuration
- event-key deduplication
- checkpointed stream state
- replayable immutable inputs
- CI validation before deployment
- infrastructure as code
- observability and audit history

Local development credentials in Docker Compose are workstation defaults and must be overridden in shared environments.
