# Operations

## Streaming health

A stream is healthy only when all of the following hold:

- source lag remains bounded,
- processed throughput keeps pace with input throughput,
- batch duration remains below the configured processing interval,
- state size remains controlled,
- data-quality rejection rate is within expected bounds,
- target writes succeed,
- freshness meets the service objective,
- reconciliation balances.

## Incident sequence

1. establish customer/data impact,
2. preserve raw data, checkpoint state, logs, and affected identifiers,
3. measure lag, throughput, batch duration, state, and sink health,
4. mitigate the consumer-facing problem,
5. isolate the defect,
6. deploy the smallest safe fix,
7. replay the affected bronze range,
8. reconcile source to target,
9. record root cause and prevention.

Deleting checkpoints is not a first-line recovery action.
