CREATE TABLE IF NOT EXISTS oakbridge_prod.silver_lending.loan_application (
  application_id STRING,
  customer_id STRING,
  business_id STRING,
  product_code STRING,
  requested_amount DECIMAL(18,2),
  use_of_funds STRING,
  application_status STRING,
  documents_complete BOOLEAN,
  financial_package_complete BOOLEAN,
  event_version BIGINT,
  event_ts TIMESTAMP,
  source_system STRING,
  trace_id STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS oakbridge_prod.silver_risk.identity_verification (
  application_id STRING,
  customer_id STRING,
  verification_status STRING,
  verification_ts TIMESTAMP,
  vendor_file_id STRING
) USING DELTA;
