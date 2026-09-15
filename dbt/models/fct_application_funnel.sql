{{ config(materialized='table', tags=['lending','funnel']) }}

with app as (
    select application_id,application_date_key,industry_key,product_key,status_key,
           requested_amount,approved_amount,funded_amount,documents_complete,
           financial_package_complete,identity_verified,ready_for_underwriting,
           application_age_hours,last_event_ts
    from analytics_core.fact_loan_application
),
status as (
    select status_key,status_code,status_name from analytics_core.dim_status
    where domain='LENDING_APPLICATION'
),
product as (
    select product_key,product_code,product_family,lending_program from analytics_core.dim_product
),
industry as (
    select industry_key,industry_name,industry_group,public_specialty_segment from analytics_core.dim_industry
),
enriched as (
    select a.*,s.status_code,s.status_name,p.product_code,p.product_family,p.lending_program,
           i.industry_name,i.industry_group,i.public_specialty_segment
    from app a
    left join status s using(status_key)
    left join product p using(product_key)
    left join industry i using(industry_key)
)
select
    application_date_key,product_code,product_family,lending_program,
    industry_group,public_specialty_segment,
    count(*) as application_count,
    sum(requested_amount) as requested_amount,
    sum(coalesce(approved_amount,0)) as approved_amount,
    sum(coalesce(funded_amount,0)) as funded_amount,
    sum(case when documents_complete then 1 else 0 end) as documents_complete_count,
    sum(case when financial_package_complete then 1 else 0 end) as financial_package_complete_count,
    sum(case when identity_verified then 1 else 0 end) as identity_verified_count,
    sum(case when ready_for_underwriting then 1 else 0 end) as ready_for_underwriting_count,
    sum(case when status_code='DECISIONED' then 1 else 0 end) as decisioned_count,
    sum(case when status_code='FUNDED' then 1 else 0 end) as funded_count,
    avg(application_age_hours) as average_application_age_hours,
    percentile_cont(.50) within group (order by application_age_hours) as p50_application_age_hours,
    percentile_cont(.95) within group (order by application_age_hours) as p95_application_age_hours,
    max(last_event_ts) as freshest_event_ts
from enriched
group by 1,2,3,4,5,6
