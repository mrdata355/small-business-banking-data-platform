#!/usr/bin/env bash
set -euo pipefail

HOST="https://dbc-a81c7db4-9f41.cloud.databricks.com"
PROFILE="oakbridge-dev"
TARGET="${1:-dev}"

if ! command -v databricks >/dev/null 2>&1; then
  echo "Databricks CLI is required: https://docs.databricks.com/aws/en/dev-tools/cli/install"
  exit 1
fi

if ! databricks auth profiles -o text 2>/dev/null | grep -q "${PROFILE}"; then
  databricks auth login --host "${HOST}" --profile "${PROFILE}"
fi

databricks bundle validate --target "${TARGET}" --profile "${PROFILE}"
databricks bundle deploy --target "${TARGET}" --profile "${PROFILE}"

echo "Bundle deployed to ${HOST} using target ${TARGET}."
echo "Jobs are defined in resources/jobs.yml and remain paused until explicitly started."
