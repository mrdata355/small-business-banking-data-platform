{{ config(materialized='table', tags=['operations','slo']) }}

with execution as (
    select
        execution_date_key,
        pipeline_key,
        status,
        input_rows,
        output_rows,
        quarantined_rows,
        duplicate_rows,
        input_rows_per_second,
        processed_rows_per_second,
        freshness_p95_ms,
        batch_duration_p95_ms,
        source_lag_p95_ms,
        state_rows_max,
        coalesce(compute_cost_usd,0)+coalesce(storage_cost_usd,0)+coalesce(network_cost_usd,0) as total_cost_usd
    from analytics_core.fact_pipeline_execution
),
pipeline as (
    select pipeline_key,pipeline_code,domain,runtime,service_tier,freshness_slo_seconds,owner_department
    from analytics_core.dim_pipeline
)
select
    e.execution_date_key,
    p.pipeline_code,
    p.domain,
    p.runtime,
    p.service_tier,
    p.owner_department,
    count(*) as execution_count,
    sum(case when e.status='FAILED' then 1 else 0 end) as failed_count,
    sum(e.input_rows) as input_rows,
    sum(e.output_rows) as output_rows,
    sum(e.quarantined_rows) as quarantined_rows,
    sum(e.duplicate_rows) as duplicate_rows,
    sum(e.input_rows-e.output_rows-e.quarantined_rows-e.duplicate_rows) as unexplained_delta,
    avg(case when e.processed_rows_per_second>0 then e.input_rows_per_second/e.processed_rows_per_second end) as pressure_ratio,
    percentile_cont(.95) within group (order by e.freshness_p95_ms) as freshness_p95_ms,
    percentile_cont(.95) within group (order by e.source_lag_p95_ms) as source_lag_p95_ms,
    percentile_cont(.95) within group (order by e.batch_duration_p95_ms) as batch_duration_p95_ms,
    max(e.state_rows_max) as state_rows_max,
    sum(e.total_cost_usd) as total_cost_usd,
    case
      when sum(e.input_rows-e.output_rows-e.quarantined_rows-e.duplicate_rows)<>0 then 'BREACHED'
      when sum(case when e.status='FAILED' then 1 else 0 end)>0 then 'BREACHED'
      when percentile_cont(.95) within group (order by e.freshness_p95_ms)>max(p.freshness_slo_seconds)*1000 then 'AT_RISK'
      when avg(case when e.processed_rows_per_second>0 then e.input_rows_per_second/e.processed_rows_per_second end)>1 then 'AT_RISK'
      else 'HEALTHY'
    end as slo_status
from execution e join pipeline p using(pipeline_key)
group by 1,2,3,4,5,6
