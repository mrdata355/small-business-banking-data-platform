#!/bin/sh
set -eu

until mc alias set local http://minio:9000 "${MINIO_ROOT_USER:-minioadmin}" "${MINIO_ROOT_PASSWORD:-minioadmin123}"; do
  echo "waiting for MinIO"
  sleep 2
done

for bucket in oakbridge-landing oakbridge-bronze oakbridge-silver oakbridge-gold oakbridge-quarantine oakbridge-checkpoints oakbridge-ml-artifacts; do
  mc mb --ignore-existing "local/${bucket}"
done

for bucket in oakbridge-landing oakbridge-bronze oakbridge-silver oakbridge-gold oakbridge-quarantine oakbridge-checkpoints oakbridge-ml-artifacts; do
  mc anonymous set none "local/${bucket}" || true
done

mc ls local
