-- Enterprise dimensional model for generated small-business banking data.
-- Project-owned schema; not a representation of any bank's private warehouse.

CREATE SCHEMA IF NOT EXISTS analytics_core;

-- Conformed dimensions
CREATE TABLE IF NOT EXISTS analytics_core.dim_date (
  date_key integer PRIMARY KEY,
  full_date date UNIQUE NOT NULL,
  day_of_week smallint NOT NULL,
  day_name varchar(12) NOT NULL,
  day_of_month smallint NOT NULL,
  week_of_year smallint NOT NULL,
  month_number smallint NOT NULL,
  month_name varchar(12) NOT NULL,
  quarter_number smallint NOT NULL,
  year_number integer NOT NULL,
  is_month_end boolean NOT NULL,
  is_quarter_end boolean NOT NULL,
  is_year_end boolean NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics_core.dim_customer (
  customer_key bigserial PRIMARY KEY,
  customer_id text NOT NULL,
  customer_type text NOT NULL,
  state_code varchar(2),
  kyc_status text,
  aml_risk_band text,
  acquisition_channel text,
  valid_from timestamptz NOT NULL,
  valid_to timestamptz,
  is_current boolean NOT NULL,
  source_system text NOT NULL,
  row_hash text NOT NULL,
  UNIQUE(customer_id, valid_from)
);
CREATE INDEX IF NOT EXISTS ix_dim_customer_current ON analytics_core.dim_customer(customer_id) WHERE is_current;

CREATE TABLE IF NOT EXISTS analytics_core.dim_business (
  business_key bigserial PRIMARY KEY,
  business_id text NOT NULL,
  legal_business_name text,
  naics_code text,
  industry_name text,
  formation_state varchar(2),
  formation_date date,
  revenue_band text,
  employee_band text,
  ownership_type text,
  lifecycle_stage text,
  valid_from timestamptz NOT NULL,
  valid_to timestamptz,
  is_current boolean NOT NULL,
  source_system text NOT NULL,
  row_hash text NOT NULL,
  UNIQUE(business_id, valid_from)
);
CREATE INDEX IF NOT EXISTS ix_dim_business_current ON analytics_core.dim_business(business_id) WHERE is_current;

CREATE TABLE IF NOT EXISTS analytics_core.dim_industry (
  industry_key bigserial PRIMARY KEY,
  naics_code text UNIQUE NOT NULL,
  industry_name text NOT NULL,
  industry_group text,
  public_specialty_segment text,
  credit_cycle_band text,
  seasonality_band text
);

CREATE TABLE IF NOT EXISTS analytics_core.dim_product (
  product_key bigserial PRIMARY KEY,
  product_code text UNIQUE NOT NULL,
  product_family text NOT NULL,
  product_name text NOT NULL,
  lending_program text,
  deposit_or_credit text NOT NULL,
  secured_flag boolean,
  revolving_flag boolean,
  active_flag boolean NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS analytics_core.dim_geography (
  geography_key bigserial PRIMARY KEY,
  country_code varchar(2) NOT NULL,
  state_code varchar(2),
  metro_name text,
  county_name text,
  census_region text,
  rural_flag boolean,
  UNIQUE(country_code, state_code, metro_name, county_name)
);

CREATE TABLE IF NOT EXISTS analytics_core.dim_channel (
  channel_key bigserial PRIMARY KEY,
  channel_code text UNIQUE NOT NULL,
  channel_name text NOT NULL,
  channel_group text NOT NULL,
  digital_flag boolean NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics_core.dim_status (
  status_key bigserial PRIMARY KEY,
  domain text NOT NULL,
  status_code text NOT NULL,
  status_name text NOT NULL,
  terminal_flag boolean NOT NULL DEFAULT false,
  success_flag boolean,
  sort_order integer,
  UNIQUE(domain, status_code)
);

CREATE TABLE IF NOT EXISTS analytics_core.dim_document_type (
  document_type_key bigserial PRIMARY KEY,
  document_type_code text UNIQUE NOT NULL,
  document_type_name text NOT NULL,
  regulatory_class text,
  sensitive_flag boolean NOT NULL DEFAULT false,
  expiry_required boolean NOT NULL DEFAULT false
);

CREATE TABLE IF NOT EXISTS analytics_core.dim_source_system (
  source_system_key bigserial PRIMARY KEY,
  source_system_code text UNIQUE NOT NULL,
  source_system_name text NOT NULL,
  source_kind text NOT NULL,
  owner_department text,
  criticality text NOT NULL,
  contract_version text
);

CREATE TABLE IF NOT EXISTS analytics_core.dim_pipeline (
  pipeline_key bigserial PRIMARY KEY,
  pipeline_code text UNIQUE NOT NULL,
  domain text NOT NULL,
  runtime text NOT NULL,
  service_tier text NOT NULL,
  freshness_slo_seconds integer,
  recovery_rto_seconds integer,
  recovery_rpo_seconds integer,
  owner_department text NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics_core.dim_model (
  model_key bigserial PRIMARY KEY,
  model_name text NOT NULL,
  model_version text NOT NULL,
  model_family text NOT NULL,
  use_case text NOT NULL,
  lifecycle_stage text NOT NULL,
  approved_at timestamptz,
  retired_at timestamptz,
  UNIQUE(model_name, model_version)
);

CREATE TABLE IF NOT EXISTS analytics_core.dim_department (
  department_key bigserial PRIMARY KEY,
  department_code text UNIQUE NOT NULL,
  department_name text NOT NULL,
  business_function text NOT NULL,
  control_function_flag boolean NOT NULL DEFAULT false,
  executive_rollup text
);

CREATE TABLE IF NOT EXISTS analytics_core.dim_stakeholder (
  stakeholder_key bigserial PRIMARY KEY,
  stakeholder_type text NOT NULL,
  stakeholder_group text NOT NULL,
  objective text NOT NULL,
  time_horizon text NOT NULL,
  value_weight numeric(8,4) NOT NULL DEFAULT 1,
  risk_weight numeric(8,4) NOT NULL DEFAULT 1,
  experience_weight numeric(8,4) NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS analytics_core.dim_vendor (
  vendor_key bigserial PRIMARY KEY,
  vendor_code text UNIQUE NOT NULL,
  vendor_name text NOT NULL,
  service_type text NOT NULL,
  criticality text NOT NULL,
  sla_seconds integer,
  pii_processor_flag boolean NOT NULL DEFAULT false
);

CREATE TABLE IF NOT EXISTS analytics_core.dim_data_asset (
  data_asset_key bigserial PRIMARY KEY,
  asset_fqn text UNIQUE NOT NULL,
  domain text NOT NULL,
  medallion_layer text NOT NULL,
  asset_type text NOT NULL,
  owner_department text NOT NULL,
  classification text NOT NULL,
  retention_days integer,
  authoritative_flag boolean NOT NULL DEFAULT false
);

-- Lending facts
CREATE TABLE IF NOT EXISTS analytics_core.fact_loan_application (
  application_id text PRIMARY KEY,
  application_date_key integer REFERENCES analytics_core.dim_date(date_key),
  customer_key bigint REFERENCES analytics_core.dim_customer(customer_key),
  business_key bigint REFERENCES analytics_core.dim_business(business_key),
  industry_key bigint REFERENCES analytics_core.dim_industry(industry_key),
  product_key bigint REFERENCES analytics_core.dim_product(product_key),
  geography_key bigint REFERENCES analytics_core.dim_geography(geography_key),
  channel_key bigint REFERENCES analytics_core.dim_channel(channel_key),
  status_key bigint REFERENCES analytics_core.dim_status(status_key),
  requested_amount numeric(18,2),
  approved_amount numeric(18,2),
  funded_amount numeric(18,2),
  equity_injection_amount numeric(18,2),
  documents_complete boolean,
  financial_package_complete boolean,
  identity_verified boolean,
  ready_for_underwriting boolean,
  application_age_hours numeric(18,4),
  event_version bigint NOT NULL,
  last_event_ts timestamptz NOT NULL,
  load_ts timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS analytics_core.fact_application_event (
  event_id text PRIMARY KEY,
  application_id text NOT NULL,
  event_date_key integer REFERENCES analytics_core.dim_date(date_key),
  source_system_key bigint REFERENCES analytics_core.dim_source_system(source_system_key),
  pipeline_key bigint REFERENCES analytics_core.dim_pipeline(pipeline_key),
  event_type text NOT NULL,
  event_version bigint NOT NULL,
  event_ts timestamptz NOT NULL,
  ingest_ts timestamptz NOT NULL,
  latency_ms bigint,
  duplicate_flag boolean NOT NULL DEFAULT false,
  quarantined_flag boolean NOT NULL DEFAULT false,
  dq_reason text,
  payload_bytes bigint
);
CREATE INDEX IF NOT EXISTS ix_fact_application_event_app_ts ON analytics_core.fact_application_event(application_id, event_ts);

CREATE TABLE IF NOT EXISTS analytics_core.fact_underwriting_decision (
  decision_id text PRIMARY KEY,
  application_id text NOT NULL,
  decision_date_key integer REFERENCES analytics_core.dim_date(date_key),
  product_key bigint REFERENCES analytics_core.dim_product(product_key),
  industry_key bigint REFERENCES analytics_core.dim_industry(industry_key),
  decision_code text NOT NULL,
  approved_amount numeric(18,2),
  pricing_rate numeric(12,6),
  term_months integer,
  risk_grade text,
  exception_count integer NOT NULL DEFAULT 0,
  cycle_time_minutes numeric(18,4),
  decision_ts timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics_core.fact_document (
  document_fact_id bigserial PRIMARY KEY,
  application_id text NOT NULL,
  document_type_key bigint REFERENCES analytics_core.dim_document_type(document_type_key),
  vendor_key bigint REFERENCES analytics_core.dim_vendor(vendor_key),
  received_date_key integer REFERENCES analytics_core.dim_date(date_key),
  received_ts timestamptz NOT NULL,
  validated_ts timestamptz,
  validation_status text NOT NULL,
  page_count integer,
  extracted_field_count integer,
  confidence_score numeric(8,6),
  exception_count integer NOT NULL DEFAULT 0
);

-- Deposit / treasury facts
CREATE TABLE IF NOT EXISTS analytics_core.fact_account_daily_balance (
  date_key integer REFERENCES analytics_core.dim_date(date_key),
  account_id text NOT NULL,
  customer_key bigint REFERENCES analytics_core.dim_customer(customer_key),
  business_key bigint REFERENCES analytics_core.dim_business(business_key),
  product_key bigint REFERENCES analytics_core.dim_product(product_key),
  geography_key bigint REFERENCES analytics_core.dim_geography(geography_key),
  opening_balance numeric(20,2),
  closing_balance numeric(20,2),
  average_ledger_balance numeric(20,2),
  available_balance numeric(20,2),
  credits_amount numeric(20,2),
  debits_amount numeric(20,2),
  transaction_count integer,
  interest_accrued numeric(20,4),
  PRIMARY KEY(date_key, account_id)
);

CREATE TABLE IF NOT EXISTS analytics_core.fact_ach_transaction (
  transaction_id text PRIMARY KEY,
  transaction_date_key integer REFERENCES analytics_core.dim_date(date_key),
  business_key bigint REFERENCES analytics_core.dim_business(business_key),
  channel_key bigint REFERENCES analytics_core.dim_channel(channel_key),
  source_system_key bigint REFERENCES analytics_core.dim_source_system(source_system_key),
  account_id text NOT NULL,
  direction text NOT NULL,
  sec_code text NOT NULL,
  transaction_status text NOT NULL,
  amount numeric(18,2) NOT NULL,
  anomaly_score numeric(8,6),
  risk_flag boolean NOT NULL DEFAULT false,
  event_ts timestamptz NOT NULL,
  ingest_ts timestamptz,
  settlement_ts timestamptz
);

CREATE TABLE IF NOT EXISTS analytics_core.fact_treasury_usage_daily (
  date_key integer REFERENCES analytics_core.dim_date(date_key),
  business_key bigint REFERENCES analytics_core.dim_business(business_key),
  product_key bigint REFERENCES analytics_core.dim_product(product_key),
  ach_count bigint NOT NULL DEFAULT 0,
  ach_amount numeric(20,2) NOT NULL DEFAULT 0,
  wire_count bigint NOT NULL DEFAULT 0,
  wire_amount numeric(20,2) NOT NULL DEFAULT 0,
  billpay_count bigint NOT NULL DEFAULT 0,
  positive_pay_exception_count bigint NOT NULL DEFAULT 0,
  login_count bigint NOT NULL DEFAULT 0,
  active_user_count bigint NOT NULL DEFAULT 0,
  PRIMARY KEY(date_key, business_key, product_key)
);

-- Customer / service facts
CREATE TABLE IF NOT EXISTS analytics_core.fact_customer_interaction (
  interaction_id text PRIMARY KEY,
  interaction_date_key integer REFERENCES analytics_core.dim_date(date_key),
  customer_key bigint REFERENCES analytics_core.dim_customer(customer_key),
  business_key bigint REFERENCES analytics_core.dim_business(business_key),
  channel_key bigint REFERENCES analytics_core.dim_channel(channel_key),
  application_id text,
  interaction_type text NOT NULL,
  sentiment_score numeric(8,6),
  sentiment_label text,
  first_response_seconds integer,
  resolution_seconds integer,
  resolved_flag boolean,
  escalation_flag boolean,
  created_ts timestamptz NOT NULL
);

-- Platform / reliability facts
CREATE TABLE IF NOT EXISTS analytics_core.fact_pipeline_run (
  run_id text PRIMARY KEY,
  pipeline_key bigint REFERENCES analytics_core.dim_pipeline(pipeline_key),
  date_key integer REFERENCES analytics_core.dim_date(date_key),
  started_ts timestamptz NOT NULL,
  completed_ts timestamptz,
  status text NOT NULL,
  records_in bigint NOT NULL DEFAULT 0,
  records_out bigint NOT NULL DEFAULT 0,
  records_quarantined bigint NOT NULL DEFAULT 0,
  duplicates_removed bigint NOT NULL DEFAULT 0,
  bytes_in bigint NOT NULL DEFAULT 0,
  duration_ms bigint,
  freshness_p95_ms bigint,
  estimated_compute_cost numeric(18,6),
  reconciliation_delta bigint
);

CREATE TABLE IF NOT EXISTS analytics_core.fact_data_quality_result (
  dq_result_id bigserial PRIMARY KEY,
  date_key integer REFERENCES analytics_core.dim_date(date_key),
  data_asset_key bigint REFERENCES analytics_core.dim_data_asset(data_asset_key),
  pipeline_key bigint REFERENCES analytics_core.dim_pipeline(pipeline_key),
  rule_code text NOT NULL,
  severity text NOT NULL,
  rows_evaluated bigint NOT NULL,
  rows_failed bigint NOT NULL,
  failure_rate numeric(12,8) NOT NULL,
  threshold numeric(12,8),
  passed_flag boolean NOT NULL,
  evaluated_ts timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics_core.fact_model_prediction (
  prediction_id text PRIMARY KEY,
  prediction_date_key integer REFERENCES analytics_core.dim_date(date_key),
  model_key bigint REFERENCES analytics_core.dim_model(model_key),
  customer_key bigint REFERENCES analytics_core.dim_customer(customer_key),
  business_key bigint REFERENCES analytics_core.dim_business(business_key),
  application_id text,
  transaction_id text,
  prediction numeric(18,8) NOT NULL,
  predicted_class text,
  confidence numeric(18,8),
  actual_outcome text,
  feature_drift_score numeric(18,8),
  scored_ts timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics_core.fact_deployment (
  deployment_id text PRIMARY KEY,
  date_key integer REFERENCES analytics_core.dim_date(date_key),
  pipeline_key bigint REFERENCES analytics_core.dim_pipeline(pipeline_key),
  environment text NOT NULL,
  commit_sha text NOT NULL,
  artifact_version text,
  deployment_status text NOT NULL,
  started_ts timestamptz NOT NULL,
  completed_ts timestamptz,
  rollback_flag boolean NOT NULL DEFAULT false,
  change_failure_flag boolean NOT NULL DEFAULT false,
  lead_time_minutes numeric(18,4)
);

-- Collaboration / portfolio facts
CREATE TABLE IF NOT EXISTS analytics_core.fact_work_item (
  work_key text PRIMARY KEY,
  created_date_key integer REFERENCES analytics_core.dim_date(date_key),
  owner_department_key bigint REFERENCES analytics_core.dim_department(department_key),
  requester_department_key bigint REFERENCES analytics_core.dim_department(department_key),
  stakeholder_key bigint REFERENCES analytics_core.dim_stakeholder(stakeholder_key),
  work_type text NOT NULL,
  status text NOT NULL,
  priority text NOT NULL,
  business_value numeric(18,6),
  risk_reduction numeric(18,6),
  urgency_score numeric(18,6),
  effort_score numeric(18,6),
  recommendation_score numeric(18,6),
  age_hours numeric(18,4),
  blocked_hours numeric(18,4),
  cycle_time_hours numeric(18,4),
  dependency_count integer,
  created_ts timestamptz NOT NULL,
  completed_ts timestamptz
);

CREATE TABLE IF NOT EXISTS analytics_core.fact_agent_run (
  agent_run_id text PRIMARY KEY,
  date_key integer REFERENCES analytics_core.dim_date(date_key),
  department_key bigint REFERENCES analytics_core.dim_department(department_key),
  model_key bigint REFERENCES analytics_core.dim_model(model_key),
  agent_id text NOT NULL,
  objective text NOT NULL,
  status text NOT NULL,
  confidence numeric(8,6),
  duration_ms bigint,
  token_or_unit_cost numeric(18,8),
  recommendation_count integer NOT NULL DEFAULT 0,
  accepted_count integer NOT NULL DEFAULT 0,
  created_ts timestamptz NOT NULL
);

-- Shareholder / management facts. These are generated analytical constructs, not public-company accounting records.
CREATE TABLE IF NOT EXISTS analytics_core.fact_management_kpi_daily (
  date_key integer REFERENCES analytics_core.dim_date(date_key),
  metric_code text NOT NULL,
  product_key bigint REFERENCES analytics_core.dim_product(product_key),
  industry_key bigint REFERENCES analytics_core.dim_industry(industry_key),
  geography_key bigint REFERENCES analytics_core.dim_geography(geography_key),
  metric_value numeric(24,8) NOT NULL,
  target_value numeric(24,8),
  prior_period_value numeric(24,8),
  forecast_value numeric(24,8),
  lower_confidence_bound numeric(24,8),
  upper_confidence_bound numeric(24,8),
  PRIMARY KEY(date_key, metric_code, product_key, industry_key, geography_key)
);

-- Recommended aggregate indexes.
CREATE INDEX IF NOT EXISTS ix_fact_loan_application_product_status ON analytics_core.fact_loan_application(product_key, status_key, application_date_key);
CREATE INDEX IF NOT EXISTS ix_fact_ach_business_date ON analytics_core.fact_ach_transaction(business_key, transaction_date_key);
CREATE INDEX IF NOT EXISTS ix_fact_pipeline_run_pipeline_date ON analytics_core.fact_pipeline_run(pipeline_key, date_key);
CREATE INDEX IF NOT EXISTS ix_fact_model_prediction_model_date ON analytics_core.fact_model_prediction(model_key, prediction_date_key);
