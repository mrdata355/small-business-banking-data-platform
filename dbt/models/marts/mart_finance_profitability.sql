with applications as (
    select * from {{ ref('int_application_lifecycle') }}
),
product_assumptions as (
    select 'SBA_7A' as product_code, 0.085::numeric as contractual_rate, 0.040::numeric as transfer_rate, 0.018::numeric as expected_loss_rate, 0.09::numeric as capital_rate
    union all select 'USDA_BI', 0.080, 0.040, 0.014, 0.08
    union all select 'CONVENTIONAL', 0.075, 0.040, 0.012, 0.08
    union all select 'CUSTOM', 0.090, 0.040, 0.022, 0.10
),
economics as (
    select
        a.application_id,
        a.business_id,
        a.customer_id,
        a.product_code,
        a.application_status,
        a.requested_amount,
        a.updated_at::date as as_of_date,
        coalesce(p.contractual_rate, 0.08) as contractual_rate,
        coalesce(p.transfer_rate, 0.04) as transfer_rate,
        coalesce(p.expected_loss_rate, 0.02) as expected_loss_rate,
        coalesce(p.capital_rate, 0.09) as capital_rate,
        a.requested_amount * coalesce(p.contractual_rate, 0.08) / 12.0 as monthly_interest_income,
        a.requested_amount * coalesce(p.transfer_rate, 0.04) / 12.0 as monthly_funds_transfer_charge,
        a.requested_amount * coalesce(p.expected_loss_rate, 0.02) / 12.0 as monthly_expected_loss,
        a.requested_amount * coalesce(p.capital_rate, 0.09) as allocated_capital
    from applications a
    left join product_assumptions p using (product_code)
),
contribution as (
    select
        *,
        monthly_interest_income - monthly_funds_transfer_charge - monthly_expected_loss as risk_adjusted_contribution_before_opex,
        {{ safe_divide(
            '12.0 * (monthly_interest_income - monthly_funds_transfer_charge - monthly_expected_loss)',
            'allocated_capital'
        ) }} as raroc_proxy
    from economics
)
select * from contribution
