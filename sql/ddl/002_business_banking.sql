CREATE TABLE IF NOT EXISTS oakbridge_prod.silver_customer.business (
  business_id STRING,
  legal_business_name STRING,
  ein_token STRING,
  naics_code STRING,
  formation_state STRING,
  formation_date DATE,
  business_address STRING,
  account_product STRING,
  kyc_status STRING,
  event_ts TIMESTAMP
) USING DELTA;

CREATE TABLE IF NOT EXISTS oakbridge_prod.silver_treasury.ach_transaction (
  transaction_id STRING,
  event_ts TIMESTAMP,
  account_id STRING,
  business_id STRING,
  direction STRING,
  amount DECIMAL(18,2),
  sec_code STRING,
  transaction_status STRING,
  counterparty_token STRING
) USING DELTA;
