CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS landing_objects (
  object_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  bucket_name text NOT NULL DEFAULT 'banking-live-landing',
  object_key text NOT NULL UNIQUE,
  object_type text NOT NULL,
  payload jsonb NOT NULL,
  received_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS stream_arrivals (
  arrival_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id text NOT NULL,
  application_id text NOT NULL,
  event_type text NOT NULL,
  event_version integer NOT NULL,
  event_ts timestamptz NOT NULL,
  payload jsonb NOT NULL,
  received_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS clean_events (
  event_id text PRIMARY KEY,
  application_id text NOT NULL,
  event_type text NOT NULL,
  event_version integer NOT NULL,
  event_ts timestamptz NOT NULL,
  application_status text NOT NULL,
  documents_complete boolean NOT NULL,
  financial_package_complete boolean NOT NULL,
  identity_verification_status text NOT NULL,
  payload jsonb NOT NULL,
  processed_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS quarantine_events (
  quarantine_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  arrival_id uuid NOT NULL,
  event_id text NOT NULL,
  application_id text,
  dq_reason text NOT NULL,
  payload jsonb NOT NULL,
  quarantined_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS canonical_applications (
  application_id text PRIMARY KEY,
  customer_id text NOT NULL,
  business_id text NOT NULL,
  product_code text NOT NULL,
  requested_amount numeric(18,2) NOT NULL,
  event_version integer NOT NULL,
  application_status text NOT NULL,
  documents_complete boolean NOT NULL,
  financial_package_complete boolean NOT NULL,
  identity_verification_status text NOT NULL,
  ready_for_underwriting boolean NOT NULL,
  last_event_id text NOT NULL,
  last_event_ts timestamptz NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS pipeline_audit (
  audit_id bigserial PRIMARY KEY,
  action text NOT NULL,
  application_id text,
  event_id text,
  outcome text NOT NULL,
  detail jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_landing_received ON landing_objects(received_at DESC);
CREATE INDEX IF NOT EXISTS idx_arrivals_app_time ON stream_arrivals(application_id, received_at DESC);
CREATE INDEX IF NOT EXISTS idx_clean_app_version ON clean_events(application_id, event_version DESC);
CREATE INDEX IF NOT EXISTS idx_quarantine_time ON quarantine_events(quarantined_at DESC);

-- The deployed live demo exposes only two SECURITY DEFINER RPC functions through
-- the database HTTPS API: process_live_event(...) and live_dashboard_snapshot().
-- Direct anonymous table writes are not granted.
