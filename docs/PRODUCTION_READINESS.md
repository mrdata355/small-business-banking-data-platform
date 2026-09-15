# Production readiness checklist

## Data contracts
- explicit schemas and nullability
- stable delivery/business keys
- backward/forward compatibility policy
- schema registry subjects

## Streaming correctness
- event-time semantics
- watermark policy
- duplicate delivery handling
- checkpoint durability
- deterministic transformations
- replay-safe current-state writes

## Lakehouse
- immutable raw landing/bronze
- canonical silver entities
- consumer-specific gold datasets
- quarantine with reason codes
- reconciliation proving source-to-target accounting

## Operations
- freshness and lag SLOs
- throughput and trigger duration
- state growth
- DQ rejection rate
- sink errors
- runbooks and recovery procedures
- deployment and rollback evidence

## Security
- least privilege
- tokenization/masking
- secret management
- encryption
- auditable access

## Cost
- autoscaling bounds
- storage lifecycle policies
- compaction/file-size policy
- compute shutdown/suspend defaults
- cloud provisioning disabled by default in this repository
