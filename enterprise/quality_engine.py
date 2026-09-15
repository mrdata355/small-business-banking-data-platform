from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Callable, Iterable, Mapping, Sequence


class Severity(StrEnum):
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class QualityIssue:
    rule_id: str
    severity: Severity
    field: str | None
    message: str
    observed_value: Any
    expected: str


@dataclass(frozen=True)
class QualityResult:
    contract_name: str
    contract_version: str
    record_fingerprint: str
    valid: bool
    issues: tuple[QualityIssue, ...]
    evaluated_at: str

    @property
    def quarantine_reason(self) -> str | None:
        blocking = [i.rule_id for i in self.issues if i.severity in {Severity.ERROR, Severity.CRITICAL}]
        return ",".join(blocking) if blocking else None


@dataclass(frozen=True)
class Rule:
    rule_id: str
    description: str
    severity: Severity
    evaluator: Callable[[Mapping[str, Any]], QualityIssue | None]
    tags: tuple[str, ...] = ()

    def evaluate(self, record: Mapping[str, Any]) -> QualityIssue | None:
        return self.evaluator(record)


def fingerprint(record: Mapping[str, Any]) -> str:
    encoded = json.dumps(record, sort_keys=True, default=str, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def required(field_name: str, severity: Severity = Severity.ERROR) -> Rule:
    def check(record: Mapping[str, Any]) -> QualityIssue | None:
        value = record.get(field_name)
        if value is None or (isinstance(value, str) and not value.strip()):
            return QualityIssue(
                f"required:{field_name}", severity, field_name,
                f"{field_name} is required", value, "non-null and non-empty",
            )
        return None
    return Rule(f"required:{field_name}", f"Require {field_name}", severity, check, ("completeness",))


def in_set(field_name: str, allowed: Sequence[str], severity: Severity = Severity.ERROR) -> Rule:
    domain = frozenset(allowed)
    def check(record: Mapping[str, Any]) -> QualityIssue | None:
        value = record.get(field_name)
        if value is not None and value not in domain:
            return QualityIssue(
                f"domain:{field_name}", severity, field_name,
                f"{field_name} is outside its controlled domain", value, f"one of {sorted(domain)}",
            )
        return None
    return Rule(f"domain:{field_name}", f"Validate domain for {field_name}", severity, check, ("validity",))


def numeric_range(field_name: str, minimum: float | None = None, maximum: float | None = None,
                  severity: Severity = Severity.ERROR) -> Rule:
    def check(record: Mapping[str, Any]) -> QualityIssue | None:
        value = record.get(field_name)
        if value is None:
            return None
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return QualityIssue(f"range:{field_name}", severity, field_name, "value is not numeric", value, "numeric")
        if not math.isfinite(numeric):
            return QualityIssue(f"range:{field_name}", severity, field_name, "value is not finite", value, "finite numeric")
        if minimum is not None and numeric < minimum:
            return QualityIssue(f"range:{field_name}", severity, field_name, "below minimum", value, f">= {minimum}")
        if maximum is not None and numeric > maximum:
            return QualityIssue(f"range:{field_name}", severity, field_name, "above maximum", value, f"<= {maximum}")
        return None
    return Rule(f"range:{field_name}", f"Validate range for {field_name}", severity, check, ("validity",))


def monotonic_version(field_name: str, current_version: int | None,
                      severity: Severity = Severity.ERROR) -> Rule:
    def check(record: Mapping[str, Any]) -> QualityIssue | None:
        value = record.get(field_name)
        try:
            incoming = int(value)
        except (TypeError, ValueError):
            return QualityIssue(f"version:{field_name}", severity, field_name, "invalid version", value, "positive integer")
        if incoming <= 0:
            return QualityIssue(f"version:{field_name}", severity, field_name, "version must be positive", value, "> 0")
        if current_version is not None and incoming < current_version:
            return QualityIssue(f"version:{field_name}", severity, field_name, "stale version", value, f">= {current_version}")
        return None
    return Rule(f"version:{field_name}", "Prevent stale overwrite", severity, check, ("consistency",))


def no_sensitive_plaintext(field_names: Iterable[str]) -> Rule:
    fields = tuple(field_names)
    def check(record: Mapping[str, Any]) -> QualityIssue | None:
        for name in fields:
            value = record.get(name)
            if value not in (None, ""):
                return QualityIssue(
                    "security:no-sensitive-plaintext", Severity.CRITICAL, name,
                    "sensitive plaintext field is not permitted", "<redacted>", "tokenized or absent",
                )
        return None
    return Rule(
        "security:no-sensitive-plaintext",
        "Prevent raw highly restricted identifiers in analytical contracts",
        Severity.CRITICAL, check, ("security", "privacy"),
    )


@dataclass
class RuleSet:
    contract_name: str
    contract_version: str
    rules: list[Rule] = field(default_factory=list)

    def evaluate(self, record: Mapping[str, Any]) -> QualityResult:
        issues = tuple(issue for rule in self.rules if (issue := rule.evaluate(record)) is not None)
        blocking = any(issue.severity in {Severity.ERROR, Severity.CRITICAL} for issue in issues)
        return QualityResult(
            self.contract_name, self.contract_version, fingerprint(record), not blocking,
            issues, datetime.now(timezone.utc).isoformat(),
        )

    def evaluate_batch(self, rows: Iterable[Mapping[str, Any]]) -> list[QualityResult]:
        return [self.evaluate(row) for row in rows]

    def metrics(self, results: Iterable[QualityResult]) -> dict[str, Any]:
        rows = list(results)
        invalid = sum(not row.valid for row in rows)
        counts: dict[str, int] = {}
        severities: dict[str, int] = {}
        for row in rows:
            for issue in row.issues:
                counts[issue.rule_id] = counts.get(issue.rule_id, 0) + 1
                severities[issue.severity.value] = severities.get(issue.severity.value, 0) + 1
        return {
            "rows": len(rows), "valid": len(rows) - invalid, "invalid": invalid,
            "invalid_rate": invalid / len(rows) if rows else 0.0,
            "rules": dict(sorted(counts.items(), key=lambda x: x[1], reverse=True)),
            "severities": severities,
        }


def application_event_rules(current_version: int | None = None) -> RuleSet:
    return RuleSet(
        "lending.application-events.v1", "1.0.0",
        [
            required("event_id"), required("application_id"), required("event_type"),
            required("event_ts"), required("source_system"),
            monotonic_version("event_version", current_version),
            in_set("application_status", [
                "SUBMITTED", "DOCUMENTS_PENDING", "REVIEW", "READY_FOR_UNDERWRITING",
                "UNDERWRITING", "DECISIONED", "FUNDED", "CANCELLED",
            ]),
            numeric_range("requested_amount", 0.01, 100_000_000),
            no_sensitive_plaintext(("ssn", "tin", "ein", "tax_id", "raw_tax_id")),
        ],
    )
