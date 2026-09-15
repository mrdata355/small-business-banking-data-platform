with applications as (
    select * from {{ ref('int_application_lifecycle') }}
),
scored as (
    select
        application_id,
        business_id,
        product_code,
        requested_amount,
        application_status,
        ready_for_underwriting,
        case
            when product_code = 'SBA_7A' then 0.020
            when product_code = 'USDA_BI' then 0.017
            when product_code = 'CONVENTIONAL' then 0.015
            else 0.025
        end::numeric as probability_of_default,
        case
            when product_code in ('SBA_7A','USDA_BI') then 0.35
            else 0.45
        end::numeric as loss_given_default
    from applications
),
exposure as (
    select
        *,
        requested_amount as exposure_at_default,
        requested_amount * probability_of_default * loss_given_default as expected_loss
    from scored
),
portfolio as (
    select sum(exposure_at_default) as total_exposure from exposure
),
ranked as (
    select
        e.*,
        {{ safe_divide('e.exposure_at_default', 'p.total_exposure') }} as portfolio_share,
        dense_rank() over (order by e.exposure_at_default desc) as exposure_rank
    from exposure e
    cross join portfolio p
)
select * from ranked
