{{ config(materialized='table', tags=['finance','profitability']) }}

with loans as (
    select business_key,product_key,last_event_ts::date as activity_date,
           sum(coalesce(funded_amount,0)) as funded_principal,
           count(*) filter (where coalesce(funded_amount,0)>0) as funded_loan_count
    from analytics_core.fact_loan_application
    group by 1,2,3
),
business as (
    select business_key,business_id,industry_name,revenue_band
    from analytics_core.dim_business where is_current
),
product as (
    select product_key,product_code,product_family from analytics_core.dim_product
),
ach as (
    select business_key,transaction_date_key,
           sum(case when direction='CREDIT' and transaction_status='POSTED' then amount else 0 end) as posted_credits,
           sum(case when direction='DEBIT' and transaction_status='POSTED' then amount else 0 end) as posted_debits,
           sum(case when transaction_status='RETURNED' then amount else 0 end) as returned_amount,
           count(*) as transaction_count
    from analytics_core.fact_ach_transaction group by 1,2
),
cost as (
    select execution_date_key,
           sum(coalesce(compute_cost_usd,0)+coalesce(storage_cost_usd,0)+coalesce(network_cost_usd,0)) as platform_cost_usd
    from analytics_core.fact_pipeline_execution group by 1
),
base as (
    select l.activity_date,b.business_id,b.industry_name,b.revenue_band,
           p.product_code,p.product_family,l.funded_principal,l.funded_loan_count,
           coalesce(a.posted_credits,0) as posted_credits,
           coalesce(a.posted_debits,0) as posted_debits,
           coalesce(a.returned_amount,0) as returned_amount,
           coalesce(a.transaction_count,0) as treasury_transaction_count,
           coalesce(c.platform_cost_usd,0) as daily_platform_cost_usd
    from loans l
    join business b using(business_key)
    join product p using(product_key)
    left join analytics_core.dim_date d on d.full_date=l.activity_date
    left join ach a on a.business_key=l.business_key and a.transaction_date_key=d.date_key
    left join cost c on c.execution_date_key=d.date_key
)
select *,
       round((funded_principal*.00035)::numeric,2) as generated_interest_revenue_proxy,
       round((posted_credits*.00002+posted_debits*.000015)::numeric,2) as generated_treasury_revenue_proxy,
       round((returned_amount*.015)::numeric,2) as generated_return_loss_proxy,
       round((daily_platform_cost_usd/nullif(count(*) over(partition by activity_date),0))::numeric,2) as allocated_platform_cost_usd,
       round(((funded_principal*.00035)+(posted_credits*.00002+posted_debits*.000015)-(returned_amount*.015)-(daily_platform_cost_usd/nullif(count(*) over(partition by activity_date),0)))::numeric,2) as generated_risk_adjusted_contribution_proxy
from base
