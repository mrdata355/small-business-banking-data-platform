#!/bin/bash
set -euo pipefail
BROKER=redpanda:9092
for topic in \
  lending.application-events.v1 \
  banking.business-onboarding.v1 \
  risk.identity-verification.v1 \
  treasury.ach-events.v1 \
  customer.interactions.v1 \
  ops.pipeline-events.v1; do
  rpk topic create "$topic" --brokers "$BROKER" --partitions 6 --replicas 1 || true
done
rpk topic list --brokers "$BROKER"
