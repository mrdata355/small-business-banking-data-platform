-- Finance data product: transparent risk-adjusted product economics.
-- Generated data only. Rates and allocation assumptions are illustrative project policy.

WITH monthly_application AS (
  SELECT
    d.year_number,
    d.month_number,
    p.product_code,
    p.product_name,
    count(*) AS application_count,
    sum(f.requested_amount) AS requested_amount,
    sum(coalesce(f.approved_amount, 0)) AS approved_amount,
    sum(coalesce(f.funded_amount, 0)) AS funded_amount,
    avg(f.application_age_hours) AS avg_application_age_hours
  FROM analytics_core.fact_loan_application f
  JOIN analytics_core.dim_date d ON d.date_key = f.application_date_key
  JOIN analytics_core.dim_product p ON p.product_key = f.product_key
  GROUP BY 1,2,3,4
),
monthly_balance AS (
  SELECT
    d.year_number,
    d.month_number,
    p.product_code,
    avg(b.average_ledger_balance) AS average_balance,
    sum(b.interest_accrued) AS interest_accrued,
    sum(b.credits_amount) AS credits_amount,
    sum(b.debits_amount) AS debits_amount,
    sum(b.transaction_count) AS transaction_count
  FROM analytics_core.fact_account_daily_balance b
  JOIN analytics_core.dim_date d ON d.date_key = b.date_key
  JOIN analytics_core.dim_product p ON p.product_key = b.product_key
  GROUP BY 1,2,3
),
assumption AS (
  SELECT * FROM (VALUES
    ('SBA_7A', 0.040::numeric, 0.018::numeric, 0.090::numeric, 0.100::numeric),
    ('USDA_BI', 0.040::numeric, 0.014::numeric, 0.080::numeric, 0.100::numeric),
    ('CONVENTIONAL', 0.040::numeric, 0.012::numeric, 0.080::numeric, 0.100::numeric),
    ('CUSTOM', 0.040::numeric, 0.022::numeric, 0.100::numeric, 0.100::numeric)
  ) AS x(product_code, transfer_rate, expected_loss_rate, capital_rate, capital_charge_rate)
),
combined AS (
  SELECT
    a.year_number,
    a.month_number,
    a.product_code,
    a.product_name,
    a.application_count,
    a.requested_amount,
    a.approved_amount,
    a.funded_amount,
    a.avg_application_age_hours,
    coalesce(b.average_balance, 0) AS average_balance,
    coalesce(b.interest_accrued, 0) AS interest_accrued,
    coalesce(b.transaction_count, 0) AS transaction_count,
    coalesce(s.transfer_rate, 0.04) AS transfer_rate,
    coalesce(s.expected_loss_rate, 0.02) AS expected_loss_rate,
    coalesce(s.capital_rate, 0.09) AS capital_rate,
    coalesce(s.capital_charge_rate, 0.10) AS capital_charge_rate
  FROM monthly_application a
  LEFT JOIN monthly_balance b
    ON b.year_number = a.year_number
   AND b.month_number = a.month_number
   AND b.product_code = a.product_code
  LEFT JOIN assumption s USING (product_code)
),
economics AS (
  SELECT
    *,
    average_balance * transfer_rate / 12.0 AS funds_transfer_charge,
    greatest(funded_amount, average_balance) * expected_loss_rate / 12.0 AS expected_credit_loss,
    greatest(funded_amount, average_balance) * capital_rate AS allocated_capital
  FROM combined
),
contribution AS (
  SELECT
    *,
    interest_accrued
      - funds_transfer_charge
      - expected_credit_loss
      - (allocated_capital * capital_charge_rate / 12.0) AS risk_adjusted_contribution,
    CASE WHEN allocated_capital = 0 THEN 0 ELSE
      12.0 * (
        interest_accrued
        - funds_transfer_charge
        - expected_credit_loss
        - (allocated_capital * capital_charge_rate / 12.0)
      ) / allocated_capital
    END AS annualized_raroc_proxy
  FROM economics
)
SELECT
  *,
  CASE
    WHEN annualized_raroc_proxy >= 0.20 THEN 'HIGH_VALUE'
    WHEN annualized_raroc_proxy >= 0.10 THEN 'VALUE_CREATING'
    WHEN annualized_raroc_proxy >= 0 THEN 'LOW_RETURN'
    ELSE 'VALUE_DESTRUCTIVE'
  END AS value_band
FROM contribution
ORDER BY year_number DESC, month_number DESC, risk_adjusted_contribution DESC;
