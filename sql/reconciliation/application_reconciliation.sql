-- Source-valid events should be fully explained by canonical history plus duplicate deliveries
WITH source AS (
  SELECT event_id
  FROM oakbridge_prod.bronze_lending.loan_application_event_raw
),
valid AS (
  SELECT event_id
  FROM source
  WHERE event_id IS NOT NULL
),
duplicate_count AS (
  SELECT COUNT(*) - COUNT(DISTINCT event_id) AS c FROM valid
),
history AS (
  SELECT COUNT(*) AS c
  FROM oakbridge_prod.silver_lending.loan_application_status_history
)
SELECT
  (SELECT COUNT(*) FROM valid) AS valid_source_count,
  (SELECT c FROM duplicate_count) AS duplicate_delivery_count,
  (SELECT c FROM history) AS canonical_history_count;
