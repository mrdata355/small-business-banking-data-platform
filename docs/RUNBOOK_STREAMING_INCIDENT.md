# Streaming incident runbook

1. Confirm customer/data impact and affected domains.
2. Capture source offsets, checkpoint path, event ids, deployment sha and current freshness/lag metrics.
3. Preserve raw landing and Bronze objects; do not delete stream checkpoints as a first response.
4. Compare input rate with processed rate, trigger duration, state rows, partition/task skew and sink latency.
5. If a specific malformed contract is responsible, quarantine it while leaving healthy traffic moving.
6. If duplicate delivery is responsible, verify the dedupe key and current-state merge predicate before replay.
7. Deploy the smallest safe correction through the normal CI/deployment path.
8. Replay the affected Bronze range into the same deterministic transformation and idempotent sink.
9. Run source-to-target reconciliation and explain every quarantined, duplicate and filtered record.
10. Record the root cause, missing guardrail and prevention change in the operations log.
