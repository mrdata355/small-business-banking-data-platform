{{ config(materialized='table', tags=['risk','mlops']) }}

with prediction as (
    select prediction_date_key,model_key,entity_id,prediction_score,prediction_label,
           threshold,latency_ms,feature_freshness_seconds,drift_status,decision_status,created_at
    from analytics_core.fact_model_prediction
),
model as (
    select model_key,model_name,model_version,model_family,use_case,lifecycle_stage
    from analytics_core.dim_model
)
select
    p.prediction_date_key,m.model_name,m.model_version,m.model_family,m.use_case,m.lifecycle_stage,
    count(*) as prediction_count,
    avg(p.prediction_score) as average_score,
    percentile_cont(.50) within group (order by p.prediction_score) as p50_score,
    percentile_cont(.95) within group (order by p.prediction_score) as p95_score,
    percentile_cont(.95) within group (order by p.latency_ms) as serving_p95_ms,
    percentile_cont(.95) within group (order by p.feature_freshness_seconds) as feature_freshness_p95_seconds,
    sum(case when p.drift_status='BLOCK' then 1 else 0 end) as drift_block_count,
    sum(case when p.drift_status='REVIEW' then 1 else 0 end) as drift_review_count,
    sum(case when p.decision_status='REJECTED' then 1 else 0 end) as rejected_decision_count,
    case
      when sum(case when p.drift_status='BLOCK' then 1 else 0 end)>0 then 'BLOCK'
      when percentile_cont(.95) within group (order by p.latency_ms)>250 then 'REVIEW'
      when percentile_cont(.95) within group (order by p.feature_freshness_seconds)>3600 then 'REVIEW'
      else 'PASS'
    end as model_operating_status,
    max(p.created_at) as freshest_prediction_ts
from prediction p join model m using(model_key)
group by 1,2,3,4,5,6
