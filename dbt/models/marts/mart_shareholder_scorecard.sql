with finance as (
    select
        as_of_date,
        count(*) as application_count,
        sum(requested_amount) as requested_amount,
        sum(risk_adjusted_contribution_before_opex) as risk_adjusted_contribution,
        avg(raroc_proxy) as average_raroc
    from {{ ref('mart_finance_profitability') }}
    group by 1
),
risk as (
    select
        current_date as as_of_date,
        sum(exposure_at_default) as exposure_at_default,
        sum(expected_loss) as expected_loss,
        max(portfolio_share) as largest_single_exposure_share
    from {{ ref('mart_risk_exposure') }}
),
quality as (
    select
        current_date as as_of_date,
        max(case when balanced then 1 else 0 end) as reconciliation_balanced,
        avg(coalesce(dq_reject_rate,0)) as dq_reject_rate,
        max(coalesce(p95_freshness_seconds,0)) as p95_freshness_seconds
    from {{ source('ops','pipeline_reconciliation') }}
),
joined as (
    select
        f.as_of_date,
        f.application_count,
        f.requested_amount,
        f.risk_adjusted_contribution,
        f.average_raroc,
        r.exposure_at_default,
        r.expected_loss,
        r.largest_single_exposure_share,
        q.reconciliation_balanced,
        q.dq_reject_rate,
        q.p95_freshness_seconds,
        case
            when coalesce(q.reconciliation_balanced,0) = 0 then 'CONTROL_FAILURE'
            when coalesce(q.dq_reject_rate,0) > 0.02 then 'DATA_QUALITY_PRESSURE'
            when coalesce(q.p95_freshness_seconds,0) > 60 then 'FRESHNESS_PRESSURE'
            else 'WITHIN_OPERATING_ENVELOPE'
        end as operating_posture
    from finance f
    left join risk r using (as_of_date)
    left join quality q using (as_of_date)
)
select * from joined
