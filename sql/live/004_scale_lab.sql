-- Reproducible generated-data scale lab.
-- The logical universe is one trillion addressable records; only bounded samples are materialized.

CREATE SCHEMA IF NOT EXISTS scale_lab;

CREATE TABLE IF NOT EXISTS scale_lab.transaction_universe_manifest (
  universe_name text PRIMARY KEY,
  logical_cardinality numeric NOT NULL CHECK (logical_cardinality > 0),
  block_size bigint NOT NULL CHECK (block_size > 0),
  block_count bigint NOT NULL CHECK (block_count > 0),
  generator_version text NOT NULL,
  generator_source text NOT NULL,
  materialization_limit bigint NOT NULL CHECK (materialization_limit >= 0),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS scale_lab.transaction_block_manifest (
  universe_name text NOT NULL REFERENCES scale_lab.transaction_universe_manifest(universe_name),
  block_id bigint NOT NULL,
  start_ordinal numeric NOT NULL,
  end_ordinal numeric NOT NULL,
  row_count bigint NOT NULL CHECK (row_count > 0),
  shard integer NOT NULL,
  checksum text NOT NULL,
  materialized boolean NOT NULL DEFAULT false,
  materialized_row_count bigint NOT NULL DEFAULT 0 CHECK (materialized_row_count >= 0),
  materialized_at timestamptz,
  PRIMARY KEY (universe_name, block_id),
  CHECK (end_ordinal >= start_ordinal)
);

CREATE TABLE IF NOT EXISTS scale_lab.generated_treasury_transaction_sample (
  ordinal bigint PRIMARY KEY,
  transaction_id text UNIQUE NOT NULL,
  event_ts timestamptz NOT NULL,
  account_id text NOT NULL,
  business_id text NOT NULL,
  direction text NOT NULL CHECK (direction IN ('CREDIT','DEBIT')),
  amount numeric NOT NULL CHECK (amount > 0),
  sec_code text NOT NULL,
  transaction_status text NOT NULL,
  counterparty_token text NOT NULL,
  generator_version text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE OR REPLACE VIEW scale_lab.transaction_universe_evidence AS
SELECT
  u.universe_name,
  u.logical_cardinality,
  u.block_size,
  u.block_count,
  count(b.block_id) AS manifest_block_rows,
  coalesce(sum(b.row_count),0) AS manifest_logical_rows,
  coalesce(sum(b.materialized_row_count),0) AS materialized_rows,
  count(*) FILTER (WHERE b.materialized) AS materialized_blocks,
  u.generator_version,
  u.generator_source,
  u.materialization_limit,
  max(b.materialized_at) AS last_materialized_at
FROM scale_lab.transaction_universe_manifest u
LEFT JOIN scale_lab.transaction_block_manifest b USING (universe_name)
GROUP BY u.universe_name, u.logical_cardinality, u.block_size, u.block_count,
         u.generator_version, u.generator_source, u.materialization_limit;

INSERT INTO scale_lab.transaction_universe_manifest (
  universe_name, logical_cardinality, block_size, block_count,
  generator_version, generator_source, materialization_limit
) VALUES (
  'generated_treasury_transactions_v1', 1000000000000, 1000000000, 1000,
  '1.0.0', 'scale/transaction_universe.py', 5000000
)
ON CONFLICT (universe_name) DO UPDATE SET
  logical_cardinality = EXCLUDED.logical_cardinality,
  block_size = EXCLUDED.block_size,
  block_count = EXCLUDED.block_count,
  generator_version = EXCLUDED.generator_version,
  generator_source = EXCLUDED.generator_source,
  materialization_limit = EXCLUDED.materialization_limit;
