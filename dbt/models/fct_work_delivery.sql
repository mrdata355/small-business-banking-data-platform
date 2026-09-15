{{ config(materialized='table', tags=['collaboration','delivery']) }}

with work as (
    select * from public.work_items
),
department as (
    select department_id,department_code,department_name,service_tier from public.departments
),
dependencies as (
    select work_item_id,
           count(*) as dependency_count,
           sum(case when dependency_type='BLOCKS' then 1 else 0 end) as blocking_dependency_count,
           sum(case when dependency_type='REQUIRES_DATA_FROM' then 1 else 0 end) as data_dependency_count
    from public.work_item_dependencies group by 1
),
comments as (
    select work_item_id,count(*) as comment_count,max(created_at) as latest_comment_at
    from public.work_item_comments group by 1
)
select
    w.work_key,w.title,w.work_type,w.status,w.priority,
    rd.department_code as requester_department_code,
    rd.department_name as requester_department,
    od.department_code as owner_department_code,
    od.department_name as owner_department,
    w.owner_name,w.pipeline_component,w.due_at,w.estimated_hours,
    w.business_value,w.risk_reduction,w.urgency_score,w.effort_score,w.recommendation_score,
    coalesce(d.dependency_count,0) as dependency_count,
    coalesce(d.blocking_dependency_count,0) as blocking_dependency_count,
    coalesce(d.data_dependency_count,0) as data_dependency_count,
    coalesce(c.comment_count,0) as comment_count,c.latest_comment_at,
    extract(epoch from (w.due_at-now()))/3600 as hours_to_due,
    case
      when w.status in ('DONE','CANCELLED') then 'CLOSED'
      when w.due_at<now() then 'OVERDUE'
      when w.priority='P0' then 'IMMEDIATE'
      when coalesce(d.blocking_dependency_count,0)>0 then 'BLOCKED_DEPENDENCY'
      when extract(epoch from (w.due_at-now()))/3600<24 then 'DUE_SOON'
      else 'ON_TRACK'
    end as attention_status,
    w.created_at,w.updated_at
from work w
left join department rd on rd.department_id=w.requester_department_id
left join department od on od.department_id=w.owner_department_id
left join dependencies d using(work_item_id)
left join comments c using(work_item_id)
