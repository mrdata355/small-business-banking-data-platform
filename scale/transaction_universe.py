from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import math
import os
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Iterator, Sequence


UNIVERSE_CARDINALITY = 1_000_000_000_000
DEFAULT_BLOCK_SIZE = 1_000_000_000
DEFAULT_SAMPLE_ROWS = 250_000


@dataclass(frozen=True)
class TransactionBlock:
    block_id: int
    start_ordinal: int
    end_ordinal: int
    row_count: int
    partition_date: str
    shard: int
    checksum: str


@dataclass(frozen=True)
class TreasuryTransaction:
    ordinal: int
    transaction_id: str
    event_ts: str
    account_id: str
    business_id: str
    direction: str
    amount: float
    sec_code: str
    transaction_status: str
    counterparty_token: str
    source_system: str


def _digest(*parts: object, length: int = 24) -> str:
    raw = "|".join(str(p) for p in parts).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:length].upper()


def deterministic_uniform(ordinal: int, salt: str) -> float:
    digest = hashlib.blake2b(f"{ordinal}:{salt}".encode(), digest_size=8).digest()
    value = int.from_bytes(digest, "big")
    return value / float(2**64 - 1)


def deterministic_choice(ordinal: int, values: Sequence[str], salt: str) -> str:
    return values[min(len(values) - 1, int(deterministic_uniform(ordinal, salt) * len(values)))]


def deterministic_amount(ordinal: int) -> float:
    # Heavy-tailed but bounded generated transaction amount. The transform is deterministic,
    # so any ordinal can be regenerated without storing all prior rows.
    u = max(1e-12, 1.0 - deterministic_uniform(ordinal, "amount"))
    amount = min(2_500_000.0, 25.0 * (-math.log(u)) ** 3 * 120)
    return round(max(1.0, amount), 2)


def transaction_for_ordinal(ordinal: int, epoch: datetime | None = None) -> TreasuryTransaction:
    if ordinal < 0 or ordinal >= UNIVERSE_CARDINALITY:
        raise ValueError(f"ordinal must be in [0, {UNIVERSE_CARDINALITY})")
    epoch = epoch or datetime(2020, 1, 1, tzinfo=timezone.utc)
    event_ts = epoch + timedelta(seconds=ordinal % (365 * 24 * 3600 * 10))
    account_slot = ordinal % 8_000_000
    business_slot = account_slot // 2
    status_roll = deterministic_uniform(ordinal, "status")
    status = "RETURNED" if status_roll < 0.007 else "PENDING" if status_roll < 0.014 else "POSTED"
    return TreasuryTransaction(
        ordinal=ordinal,
        transaction_id=f"ACH-{ordinal:012d}-{_digest(ordinal, 'tx', length=12)}",
        event_ts=event_ts.isoformat(),
        account_id=f"ACCT-{account_slot:08d}",
        business_id=f"BIZ-{business_slot:08d}",
        direction=deterministic_choice(ordinal, ("CREDIT", "DEBIT"), "direction"),
        amount=deterministic_amount(ordinal),
        sec_code=deterministic_choice(ordinal, ("CCD", "CTX", "PPD", "WEB"), "sec"),
        transaction_status=status,
        counterparty_token=f"cp-{_digest(ordinal, 'cp', length=18).lower()}",
        source_system="scale_harness",
    )


def iter_transactions(start_ordinal: int, row_count: int) -> Iterator[TreasuryTransaction]:
    stop = min(UNIVERSE_CARDINALITY, start_ordinal + row_count)
    for ordinal in range(start_ordinal, stop):
        yield transaction_for_ordinal(ordinal)


def build_block_manifest(
    cardinality: int = UNIVERSE_CARDINALITY,
    block_size: int = DEFAULT_BLOCK_SIZE,
    epoch: datetime | None = None,
) -> list[TransactionBlock]:
    if cardinality <= 0 or block_size <= 0:
        raise ValueError("cardinality and block_size must be positive")
    epoch = epoch or datetime(2020, 1, 1, tzinfo=timezone.utc)
    blocks: list[TransactionBlock] = []
    block_count = math.ceil(cardinality / block_size)
    for block_id in range(block_count):
        start = block_id * block_size
        end = min(cardinality, start + block_size)
        row_count = end - start
        representative = transaction_for_ordinal(start, epoch)
        checksum = _digest(block_id, start, end, representative.transaction_id, cardinality, block_size)
        blocks.append(
            TransactionBlock(
                block_id=block_id,
                start_ordinal=start,
                end_ordinal=end - 1,
                row_count=row_count,
                partition_date=representative.event_ts[:10],
                shard=block_id % 1024,
                checksum=checksum,
            )
        )
    return blocks


def manifest_summary(blocks: Sequence[TransactionBlock]) -> dict:
    total_rows = sum(b.row_count for b in blocks)
    root_hash = hashlib.sha256("".join(b.checksum for b in blocks).encode()).hexdigest()
    return {
        "logical_transaction_cardinality": total_rows,
        "materialized_row_count": 0,
        "block_count": len(blocks),
        "minimum_ordinal": blocks[0].start_ordinal if blocks else None,
        "maximum_ordinal": blocks[-1].end_ordinal if blocks else None,
        "manifest_merkle_like_root": root_hash,
        "generator_version": "1.0.0",
        "storage_model": "deterministic ordinal address space; materialize selected shards only",
        "evidence_note": (
            "The manifest proves an addressable deterministic universe of generated records. "
            "It does not claim that one trillion physical rows are stored in the development database."
        ),
    }


def write_manifest(path: Path, blocks: Sequence[TransactionBlock]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "summary": manifest_summary(blocks),
        "blocks": [dataclasses.asdict(block) for block in blocks],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[TreasuryTransaction]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(dataclasses.asdict(row), sort_keys=True) + "\n")
            count += 1
    return count


def validate_determinism(samples: int = 1000, seed: int = 7) -> dict:
    rng = random.Random(seed)
    ordinals = [rng.randrange(0, UNIVERSE_CARDINALITY) for _ in range(samples)]
    first = [transaction_for_ordinal(o) for o in ordinals]
    second = [transaction_for_ordinal(o) for o in ordinals]
    mismatches = [o for o, a, b in zip(ordinals, first, second) if a != b]
    ids = [row.transaction_id for row in first]
    return {
        "samples": samples,
        "deterministic": not mismatches,
        "mismatch_count": len(mismatches),
        "unique_transaction_ids": len(set(ids)),
        "id_collision_count": samples - len(set(ids)),
    }


def estimate_physical_footprint(cardinality: int = UNIVERSE_CARDINALITY, avg_row_bytes: int = 280) -> dict:
    raw_bytes = cardinality * avg_row_bytes
    return {
        "logical_rows": cardinality,
        "assumed_avg_row_bytes": avg_row_bytes,
        "estimated_raw_bytes": raw_bytes,
        "estimated_raw_tb_decimal": round(raw_bytes / 1_000_000_000_000, 2),
        "estimated_raw_tib_binary": round(raw_bytes / (1024**4), 2),
        "warning": "Physical materialization at this scale is intentionally disabled in free/reference environments.",
    }


def export_evidence(root: Path, sample_rows: int = DEFAULT_SAMPLE_ROWS) -> dict:
    blocks = build_block_manifest()
    manifest_path = root / "transaction_universe_manifest.json"
    sample_path = root / "transaction_sample.jsonl"
    write_manifest(manifest_path, blocks)
    materialized = write_jsonl(sample_path, iter_transactions(0, sample_rows))
    evidence = {
        "manifest": manifest_summary(blocks),
        "sample_materialization": {
            "rows": materialized,
            "path": str(sample_path),
            "sha256": hashlib.sha256(sample_path.read_bytes()).hexdigest(),
        },
        "determinism": validate_determinism(),
        "footprint": estimate_physical_footprint(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    evidence_path = root / "scale_evidence.json"
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser(description="Deterministic generated treasury transaction scale harness")
    parser.add_argument("--output", default="runtime/scale", help="Output directory")
    parser.add_argument("--sample-rows", type=int, default=DEFAULT_SAMPLE_ROWS)
    parser.add_argument("--ordinal", type=int, help="Print one deterministic transaction and exit")
    args = parser.parse_args()

    if args.ordinal is not None:
        print(json.dumps(dataclasses.asdict(transaction_for_ordinal(args.ordinal)), indent=2))
        return

    if args.sample_rows < 0 or args.sample_rows > 5_000_000:
        raise SystemExit("--sample-rows must be between 0 and 5,000,000 in the reference environment")

    evidence = export_evidence(Path(args.output), args.sample_rows)
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
