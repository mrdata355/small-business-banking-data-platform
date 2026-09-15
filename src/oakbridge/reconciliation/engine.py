from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Iterable, Mapping


class ReconciliationStatus(StrEnum):
    BALANCED = "BALANCED"
    WARN = "WARN"
    FAILED = "FAILED"


@dataclass(frozen=True)
class ControlTotals:
    row_count: int
    amount_sum: Decimal = Decimal("0")
    distinct_business_keys: int = 0
    null_business_keys: int = 0
    duplicate_rows: int = 0
    min_event_version: int | None = None
    max_event_version: int | None = None


@dataclass(frozen=True)
class ReconciliationBucket:
    name: str
    row_count: int
    amount_sum: Decimal = Decimal("0")
    intentional: bool = True
    reason: str = ""


@dataclass(frozen=True)
class ReconciliationResult:
    source: ControlTotals
    target: ControlTotals
    buckets: tuple[ReconciliationBucket, ...]
    unexplained_rows: int
    unexplained_amount: Decimal
    status: ReconciliationStatus
    findings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def balanced(self) -> bool:
        return self.status == ReconciliationStatus.BALANCED


class ReconciliationEngine:
    """Reconciles source truth to canonical outputs and explicit exception buckets.

    Every missing source row must be explained by a governed bucket such as duplicate
    delivery, quarantine, policy exclusion or late-data repair. A successful pipeline
    cannot silently make rows disappear.
    """

    def __init__(
        self,
        row_tolerance: int = 0,
        amount_tolerance: Decimal = Decimal("0.01"),
    ) -> None:
        if row_tolerance < 0 or amount_tolerance < 0:
            raise ValueError("reconciliation tolerances cannot be negative")
        self.row_tolerance = row_tolerance
        self.amount_tolerance = amount_tolerance

    def reconcile(
        self,
        source: ControlTotals,
        target: ControlTotals,
        buckets: Iterable[ReconciliationBucket] = (),
    ) -> ReconciliationResult:
        bucket_rows = tuple(buckets)
        explained_rows = sum(bucket.row_count for bucket in bucket_rows if bucket.intentional)
        explained_amount = sum(
            (bucket.amount_sum for bucket in bucket_rows if bucket.intentional),
            Decimal("0"),
        )
        unexplained_rows = source.row_count - target.row_count - explained_rows
        unexplained_amount = source.amount_sum - target.amount_sum - explained_amount

        findings: list[str] = []
        if abs(unexplained_rows) > self.row_tolerance:
            findings.append(
                f"unexplained row delta {unexplained_rows} exceeds tolerance {self.row_tolerance}"
            )
        if abs(unexplained_amount) > self.amount_tolerance:
            findings.append(
                f"unexplained amount delta {unexplained_amount} exceeds tolerance "
                f"{self.amount_tolerance}"
            )
        if target.null_business_keys:
            findings.append(f"target contains {target.null_business_keys} null business keys")
        if target.duplicate_rows:
            findings.append(f"target contains {target.duplicate_rows} duplicate rows")
        if target.distinct_business_keys > target.row_count:
            findings.append("target distinct-key count exceeds row count")

        if findings:
            status = ReconciliationStatus.FAILED
        elif any(not bucket.intentional for bucket in bucket_rows):
            status = ReconciliationStatus.WARN
        else:
            status = ReconciliationStatus.BALANCED

        return ReconciliationResult(
            source=source,
            target=target,
            buckets=bucket_rows,
            unexplained_rows=unexplained_rows,
            unexplained_amount=unexplained_amount,
            status=status,
            findings=tuple(findings),
        )

    def explain(self, result: ReconciliationResult) -> dict:
        return {
            "status": result.status,
            "balanced": result.balanced,
            "equation": {
                "source_rows": result.source.row_count,
                "target_rows": result.target.row_count,
                "explained_rows": sum(b.row_count for b in result.buckets if b.intentional),
                "unexplained_rows": result.unexplained_rows,
                "source_amount": str(result.source.amount_sum),
                "target_amount": str(result.target.amount_sum),
                "explained_amount": str(
                    sum(
                        (b.amount_sum for b in result.buckets if b.intentional),
                        Decimal("0"),
                    )
                ),
                "unexplained_amount": str(result.unexplained_amount),
            },
            "buckets": [
                {
                    "name": bucket.name,
                    "row_count": bucket.row_count,
                    "amount_sum": str(bucket.amount_sum),
                    "intentional": bucket.intentional,
                    "reason": bucket.reason,
                }
                for bucket in result.buckets
            ],
            "findings": list(result.findings),
        }


def control_totals_from_records(
    records: Iterable[Mapping[str, object]],
    business_key: str,
    amount_field: str | None = None,
    event_version_field: str | None = None,
) -> ControlTotals:
    rows = list(records)
    keys = [record.get(business_key) for record in rows]
    non_null_keys = [key for key in keys if key not in (None, "")]
    duplicates = len(non_null_keys) - len(set(non_null_keys))
    amount_sum = Decimal("0")
    if amount_field:
        for record in rows:
            value = record.get(amount_field)
            if value is not None:
                amount_sum += Decimal(str(value))
    versions: list[int] = []
    if event_version_field:
        versions = [
            int(record[event_version_field])
            for record in rows
            if record.get(event_version_field) is not None
        ]
    return ControlTotals(
        row_count=len(rows),
        amount_sum=amount_sum,
        distinct_business_keys=len(set(non_null_keys)),
        null_business_keys=len(rows) - len(non_null_keys),
        duplicate_rows=duplicates,
        min_event_version=min(versions) if versions else None,
        max_event_version=max(versions) if versions else None,
    )
