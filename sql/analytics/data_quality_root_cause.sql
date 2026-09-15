-- Data Quality deliverable: prioritize defects by recurrence, impact and producer.

WITH rule_result AS (
  SELECT
    q.dq_result_id,
    d.full_date,
    a.asset_fqn,
    a.domain,
    a.medallion_layer,
    a.owner_department,
    a.classification,
    p.pipeline_code,
    q.rule_code,
    q.severity,
    q.rows_evaluated,
    q.rows_failed,
    q.failure_rate,
    q.threshold,
    q.passed_flag,
    q.evaluated_ts
  FROM analytics_core.fact_data_quality_result q
  JOIN analytics_core.dim_date d ON d.date_key = q.date_key
  JOIN analytics_core.dim_data_asset a ON a.data_asset_key = q.data_asset_key
  LEFT JOIN analytics_core.dim_pipeline p ON p.pipeline_key = q.pipeline_key
),
rolling AS (
  SELECT
    *,
    sum(rows_failed) OVER (
      PARTITION BY asset_fqn, rule_code
      ORDER BY evaluated_ts
      ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) AS rolling_30_eval_failed_rows,
    avg(failure_rate) OVER (
      PARTITION BY asset_fqn, rule_code
      ORDER BY evaluated_ts
      ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) AS rolling_30_eval_failure_rate,
    sum(CASE WHEN not passed_flag THEN 1 ELSE 0 END) OVER (
      PARTITION BY asset_fqn, rule_code
      ORDER BY evaluated_ts
      ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) AS rolling_30_eval_breach_count
  FROM rule_result
),
prioritized AS (
  SELECT
    *,
    (
      ln(1 + greatest(rolling_30_eval_failed_rows,0))
      * (1 + 10 * greatest(rolling_30_eval_failure_rate,0))
      * CASE severity WHEN 'FATAL' THEN 5 WHEN 'ERROR' THEN 3 WHEN 'WARN' THEN 1.5 ELSE 1 END
      * CASE classification WHEN 'HIGHLY_RESTRICTED' THEN 2 WHEN 'RESTRICTED_PII' THEN 1.5 ELSE 1 END
    ) AS defect_priority_score
  FROM rolling
)
SELECT
  full_date,
  domain,
  medallion_layer,
  owner_department,
  pipeline_code,
  asset_fqn,
  rule_code,
  severity,
  rows_evaluated,
  rows_failed,
  failure_rate,
  threshold,
  rolling_30_eval_failed_rows,
  rolling_30_eval_failure_rate,
  rolling_30_eval_breach_count,
  defect_priority_score,
  CASE
    WHEN defect_priority_score >= 30 THEN 'P0_PREVENT_RECURRENCE'
    WHEN defect_priority_score >= 15 THEN 'P1_ROOT_CAUSE'
    WHEN defect_priority_score >= 5 THEN 'P2_REMEDIATE'
    ELSE 'MONITOR'
  END AS recommended_queue,
  evaluated_ts
FROM prioritized
ORDER BY defect_priority_score DESC, evaluated_ts DESC;
