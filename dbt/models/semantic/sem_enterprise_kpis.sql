{{ config(materialized='view') }}

with application as (
    select * from {{ source('analytics_core', 'fact_loan_application') }}
),
pipeline as (
    select * from {{ source('analytics_core', 'fact_pipeline_run') }}
),
quality as (
    select * from {{ source('analytics_core', 'fact_data_quality_result') }}
),
model_prediction as (
    select * from {{ source('analytics_core', 'fact_model_prediction') }}
),
work_item as (
    select * from {{ source('analytics_core', 'fact_work_item') }}
),
application_kpis as (
    select
        'LENDING' as domain,
        'applications_total' as metric_code,
        count(*)::numeric as metric_value,
        null::numeric as target_value
    from application
    union all
    select 'LENDING','underwriting_ready_rate',
        avg(case when ready_for_underwriting then 1 else 0 end)::numeric,
        0.95::numeric
    from application
),
pipeline_kpis as (
    select 'PLATFORM' as domain, 'pipeline_success_rate' as metric_code,
        avg(case when status = 'SUCCEEDED' then 1 else 0 end)::numeric as metric_value,
        0.995::numeric as target_value
    from pipeline
    union all
    select 'PLATFORM','reconciliation_unexplained_delta',
        coalesce(sum(abs(reconciliation_delta)),0)::numeric,
        0::numeric
    from pipeline
    union all
    select 'PLATFORM','dq_failure_rate',
        coalesce(sum(rows_failed),0)::numeric / nullif(coalesce(sum(rows_evaluated),0),0),
        0.01::numeric
    from quality
),
model_kpis as (
    select 'MODEL' as domain, 'predictions_total' as metric_code,
        count(*)::numeric, null::numeric
    from model_prediction
    union all
    select 'MODEL','avg_prediction_confidence',
        avg(confidence)::numeric, 0.80::numeric
    from model_prediction
),
work_kpis as (
    select 'COLLABORATION' as domain, 'open_priority_score' as metric_code,
        coalesce(sum(recommendation_score) filter (where status not in ('DONE','CANCELLED')),0)::numeric,
        null::numeric
    from work_item
)
select * from application_kpis
union all select * from pipeline_kpis
union all select * from model_kpis
union all select * from work_kpis
