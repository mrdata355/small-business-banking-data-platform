# Scale evidence

The reference environment exposes a deterministic generated transaction address space of exactly **1,000,000,000,000** treasury transactions.

This is deliberately different from claiming that one trillion physical rows are stored in a development database. Materializing a trillion physical rows solely for demonstration would be expensive, slow and operationally wasteful.

## Mechanism

`scale/transaction_universe.py` maps any ordinal in `0..999,999,999,999` to one deterministic generated treasury transaction. The mapping derives transaction ID, event timestamp, account ID, business ID, direction, amount, ACH SEC code, status, counterparty token and source system. No prior rows must exist for ordinal `999,999,999,999` to be reproduced.

## Evidence artifacts

The `scale-evidence` GitHub Action creates:

```text
runtime/scale/transaction_universe_manifest.json
runtime/scale/transaction_sample.jsonl
runtime/scale/scale_evidence.json
```

The manifest partitions the logical address space into deterministic billion-row blocks and records a checksum for every block. The evidence report verifies:

- logical cardinality = 1,000,000,000,000;
- deterministic regeneration;
- sample ID uniqueness;
- first and last ordinal coverage;
- manifest root hash;
- physical-footprint estimate;
- exact sample SHA-256.

## Materialization policy

Reference and CI environments materialize bounded samples only. Production-scale experiments can materialize selected shards or use distributed generation directly inside Spark executors. This keeps the proof reproducible without creating hundreds of terabytes of unnecessary storage.

## Verification

```bash
python scale/transaction_universe.py --ordinal 999999999999
python scale/transaction_universe.py --output runtime/scale --sample-rows 25000
pytest -q tests/unit/test_scale_harness.py
```

Anyone can request an arbitrary ordinal, regenerate the same record and compare the manifest/evidence hashes independently.
