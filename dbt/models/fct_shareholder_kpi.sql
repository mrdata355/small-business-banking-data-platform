{{ config(materialized='table', tags=['shareholder','executive']) }}

with kpi as (
    select snapshot_date_key,stakeholder_key,metric_code,metric_value,metric_unit,
           target_value,variance_to_target,trend_7d,trend_30d,confidence,
           source_freshness_seconds,created_at
    from analytics_core.fact_management_kpi_snapshot
),
stakeholder as (
    select stakeholder_key,stakeholder_type,stakeholder_group,objective,time_horizon,
           value_weight,risk_weight,experience_weight
    from analytics_core.dim_stakeholder
),
base as (
    select k.*,s.stakeholder_type,s.stakeholder_group,s.objective,s.time_horizon,
           s.value_weight,s.risk_weight,s.experience_weight,
           case when k.target_value is null or k.target_value=0 then null else k.metric_value/k.target_value end as attainment_ratio
    from kpi k join stakeholder s using(stakeholder_key)
    where s.stakeholder_type in ('SHAREHOLDER','EXECUTIVE')
)
select *,
       round((coalesce(attainment_ratio,1.0)*greatest(confidence,.70)*greatest(.25,value_weight+risk_weight+experience_weight))::numeric,6) as weighted_value_score,
       case
         when source_freshness_seconds>86400 then 'STALE'
         when confidence<.70 then 'LOW_CONFIDENCE'
         when coalesce(attainment_ratio,1)<.85 then 'BELOW_TARGET'
         when coalesce(attainment_ratio,1)>=1.05 then 'ABOVE_TARGET'
         else 'ON_TRACK'
       end as operating_status
from base
