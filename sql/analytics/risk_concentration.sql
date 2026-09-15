-- Risk data product: generated-data exposure, expected loss and concentration monitoring.

WITH exposure AS (
  SELECT
    f.application_id,
    b.business_id,
    i.naics_code,
    i.industry_name,
    p.product_code,
    g.state_code,
    coalesce(f.funded_amount, f.approved_amount, f.requested_amount, 0) AS exposure_at_default,
    CASE
      WHEN p.product_code = 'SBA_7A' THEN 0.020
      WHEN p.product_code = 'USDA_BI' THEN 0.017
      WHEN p.product_code = 'CONVENTIONAL' THEN 0.015
      ELSE 0.025
    END::numeric AS probability_of_default,
    CASE WHEN p.product_code IN ('SBA_7A','USDA_BI') THEN 0.35 ELSE 0.45 END::numeric AS loss_given_default
  FROM analytics_core.fact_loan_application f
  LEFT JOIN analytics_core.dim_business b ON b.business_key = f.business_key
  LEFT JOIN analytics_core.dim_industry i ON i.industry_key = f.industry_key
  LEFT JOIN analytics_core.dim_product p ON p.product_key = f.product_key
  LEFT JOIN analytics_core.dim_geography g ON g.geography_key = f.geography_key
),
loss AS (
  SELECT
    *,
    exposure_at_default * probability_of_default * loss_given_default AS expected_loss,
    exposure_at_default * least(1.0, probability_of_default * 2.0)
      * least(1.0, loss_given_default + 0.10) AS stressed_expected_loss
  FROM exposure
),
portfolio AS (
  SELECT
    sum(exposure_at_default) AS portfolio_ead,
    sum(expected_loss) AS portfolio_expected_loss,
    sum(stressed_expected_loss) AS portfolio_stressed_expected_loss
  FROM loss
),
industry AS (
  SELECT
    'INDUSTRY' AS concentration_dimension,
    coalesce(industry_name, 'UNKNOWN') AS concentration_key,
    count(*) AS exposure_count,
    sum(exposure_at_default) AS exposure_at_default,
    sum(expected_loss) AS expected_loss,
    sum(stressed_expected_loss) AS stressed_expected_loss
  FROM loss
  GROUP BY 1,2
),
geography AS (
  SELECT
    'STATE' AS concentration_dimension,
    coalesce(state_code, 'NA') AS concentration_key,
    count(*) AS exposure_count,
    sum(exposure_at_default) AS exposure_at_default,
    sum(expected_loss) AS expected_loss,
    sum(stressed_expected_loss) AS stressed_expected_loss
  FROM loss
  GROUP BY 1,2
),
product AS (
  SELECT
    'PRODUCT' AS concentration_dimension,
    coalesce(product_code, 'UNKNOWN') AS concentration_key,
    count(*) AS exposure_count,
    sum(exposure_at_default) AS exposure_at_default,
    sum(expected_loss) AS expected_loss,
    sum(stressed_expected_loss) AS stressed_expected_loss
  FROM loss
  GROUP BY 1,2
),
combined AS (
  SELECT * FROM industry
  UNION ALL SELECT * FROM geography
  UNION ALL SELECT * FROM product
)
SELECT
  c.*,
  CASE WHEN p.portfolio_ead = 0 THEN 0 ELSE c.exposure_at_default / p.portfolio_ead END AS portfolio_share,
  c.stressed_expected_loss - c.expected_loss AS stress_incremental_loss,
  CASE
    WHEN p.portfolio_ead = 0 THEN 'NO_EXPOSURE'
    WHEN c.exposure_at_default / p.portfolio_ead >= 0.30 THEN 'HIGH_CONCENTRATION'
    WHEN c.exposure_at_default / p.portfolio_ead >= 0.15 THEN 'WATCH'
    ELSE 'WITHIN_REFERENCE_LIMIT'
  END AS concentration_band,
  p.portfolio_ead,
  p.portfolio_expected_loss,
  p.portfolio_stressed_expected_loss
FROM combined c
CROSS JOIN portfolio p
ORDER BY portfolio_share DESC, concentration_dimension, concentration_key;
