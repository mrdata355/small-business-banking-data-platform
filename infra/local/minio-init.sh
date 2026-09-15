#!/bin/sh
set -eu

mc alias set local http://minio:9000 "${MINIO_ROOT_USER:-minioadmin}" "${MINIO_ROOT_PASSWORD:-minioadmin123}"
for bucket in oakbridge-landing oakbridge-bronze oakbridge-silver oakbridge-gold oakbridge-quarantine oakbridge-checkpoints oakbridge-ml-artifacts; do
  mc mb --ignore-existing "local/${bucket}"
done
mc anonymous set none local/oakbridge-landing || true
mc anonymous set none local/oakbridge-bronze || true
mc anonymous set none local/oakbridge-silver || true
mc anonymous set none local/oakbridge-gold || true
mc anonymous set none local/oakbridge-quarantine || true
mc anonymous set none local/oakbridge-checkpoints || true
mc anonymous set none local/oakbridge-ml-artifacts || true
