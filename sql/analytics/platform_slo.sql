-- SRE/Data Platform data product: freshness, throughput, quality and error-budget posture.

WITH run_base AS (
  SELECT
    r.run_id,
    p.pipeline_code,
    p.domain,
    p.service_tier,
    p.freshness_slo_seconds,
    r.started_ts,
    r.completed_ts,
    r.status,
    r.records_in,
    r.records_out,
    r.records_quarantined,
    r.duplicates_removed,
    r.duration_ms,
    r.freshness_p95_ms,
    r.estimated_compute_cost,
    r.reconciliation_delta,
    CASE WHEN r.records_in = 0 THEN 0 ELSE r.records_quarantined::numeric / r.records_in END AS quarantine_rate,
    CASE WHEN r.records_in = 0 THEN 0 ELSE r.duplicates_removed::numeric / r.records_in END AS duplicate_rate,
    CASE WHEN r.duration_ms IS NULL OR r.duration_ms = 0 THEN NULL
         ELSE 1000.0 * r.records_out / r.duration_ms END AS processed_rows_per_second
  FROM analytics_core.fact_pipeline_run r
  JOIN analytics_core.dim_pipeline p ON p.pipeline_key = r.pipeline_key
),
classified AS (
  SELECT
    *,
    CASE WHEN freshness_slo_seconds IS NULL THEN NULL
         ELSE freshness_p95_ms / 1000.0 / nullif(freshness_slo_seconds,0) END AS freshness_burn,
    CASE
      WHEN status NOT IN ('SUCCEEDED','RUNNING') THEN 'EXECUTION_FAILURE'
      WHEN coalesce(reconciliation_delta,0) <> 0 THEN 'RECONCILIATION_BREACH'
      WHEN freshness_slo_seconds IS NOT NULL AND freshness_p95_ms > freshness_slo_seconds * 1000 THEN 'FRESHNESS_BREACH'
      WHEN quarantine_rate > 0.02 THEN 'QUALITY_PRESSURE'
      ELSE 'WITHIN_SLO'
    END AS operating_state
  FROM run_base
),
windowed AS (
  SELECT
    *,
    avg(CASE WHEN operating_state = 'WITHIN_SLO' THEN 1.0 ELSE 0.0 END)
      OVER (PARTITION BY pipeline_code ORDER BY started_ts ROWS BETWEEN 99 PRECEDING AND CURRENT ROW) AS last_100_run_slo_rate,
    percentile_cont(0.95) WITHIN GROUP (ORDER BY freshness_p95_ms)
      OVER (PARTITION BY pipeline_code) AS observed_freshness_p95_ms,
    avg(estimated_compute_cost)
      OVER (PARTITION BY pipeline_code ORDER BY started_ts ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS rolling_30_run_avg_cost
  FROM classified
)
SELECT
  *,
  CASE
    WHEN operating_state IN ('EXECUTION_FAILURE','RECONCILIATION_BREACH') THEN 'PAGE'
    WHEN coalesce(freshness_burn,0) >= 2 THEN 'PAGE'
    WHEN last_100_run_slo_rate < 0.99 THEN 'INVESTIGATE'
    WHEN quarantine_rate > 0.01 THEN 'WATCH'
    ELSE 'HEALTHY'
  END AS response_tier
FROM windowed
ORDER BY started_ts DESC, pipeline_code;
