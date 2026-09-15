# Observability

## Local real-time stack

Prometheus scrapes:

- `stream-gateway:8000/metrics`
- `spark-streaming:9108/metrics`

Grafana automatically provisions the `Banking Streaming Platform` dashboard.

Metrics include:

- gateway events accepted by topic
- gateway validation rejects
- API latency
- Spark input rows/sec
- Spark processed rows/sec
- Spark trigger duration
- state-store row count

## Internet demo

The public observability page reads the persistent demo backend and refreshes continuously. It includes:

- ingestion and merge outcomes by minute
- quarantine reasons
- canonical application readiness
- treasury anomaly events
- model predictions
- generated customer-interaction sentiment
- automation run history
- deployment history
- pipeline heartbeats
- operator notes
- public GitHub commit and CI activity

## Health definition

`RUNNING` is not treated as sufficient health. The platform is healthy when event freshness, source lag, processing throughput, state growth, DQ rejection, target writes and reconciliation remain within policy.
