from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Callable, Iterable, Mapping, Sequence


class Severity(StrEnum):
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"


@dataclass(frozen=True)
class QualityFinding:
    rule_id: str
    severity: Severity
    message: str
    field: str | None = None
    observed_value: object | None = None


@dataclass(frozen=True)
class Rule:
    rule_id: str
    description: str
    severity: Severity
    predicate: Callable[[Mapping[str, object]], bool]
    message: str
    field: str | None = None


@dataclass(frozen=True)
class Evaluation:
    record: Mapping[str, object]
    findings: tuple[QualityFinding, ...]

    @property
    def valid(self) -> bool:
        return not any(
            finding.severity in {Severity.ERROR, Severity.FATAL}
            for finding in self.findings
        )

    @property
    def quarantine_reason(self) -> str | None:
        blocking = [
            finding.rule_id
            for finding in self.findings
            if finding.severity in {Severity.ERROR, Severity.FATAL}
        ]
        return ",".join(blocking) if blocking else None


class RulesEngine:
    def __init__(self, rules: Iterable[Rule]) -> None:
        self.rules = tuple(rules)
        ids = [rule.rule_id for rule in self.rules]
        if len(ids) != len(set(ids)):
            raise ValueError("rule_id values must be unique")

    def evaluate(self, record: Mapping[str, object]) -> Evaluation:
        findings: list[QualityFinding] = []
        for rule in self.rules:
            try:
                passed = bool(rule.predicate(record))
            except Exception as exc:  # rule failure itself is evidence
                findings.append(
                    QualityFinding(
                        rule_id=f"{rule.rule_id}.EXECUTION",
                        severity=Severity.FATAL,
                        message=f"rule execution failed: {type(exc).__name__}: {exc}",
                        field=rule.field,
                    )
                )
                continue
            if not passed:
                findings.append(
                    QualityFinding(
                        rule_id=rule.rule_id,
                        severity=rule.severity,
                        message=rule.message,
                        field=rule.field,
                        observed_value=record.get(rule.field) if rule.field else None,
                    )
                )
        return Evaluation(record=record, findings=tuple(findings))

    def partition(
        self, records: Iterable[Mapping[str, object]]
    ) -> tuple[list[Evaluation], list[Evaluation]]:
        valid: list[Evaluation] = []
        invalid: list[Evaluation] = []
        for record in records:
            result = self.evaluate(record)
            (valid if result.valid else invalid).append(result)
        return valid, invalid

    def scorecard(self, records: Iterable[Mapping[str, object]]) -> dict:
        evaluations = [self.evaluate(record) for record in records]
        total = len(evaluations)
        invalid = sum(not evaluation.valid for evaluation in evaluations)
        counts: dict[str, int] = {}
        for evaluation in evaluations:
            for finding in evaluation.findings:
                counts[finding.rule_id] = counts.get(finding.rule_id, 0) + 1
        return {
            "records": total,
            "valid_records": total - invalid,
            "invalid_records": invalid,
            "valid_rate": (total - invalid) / total if total else 1.0,
            "invalid_rate": invalid / total if total else 0.0,
            "rule_failures": dict(sorted(counts.items(), key=lambda item: item[1], reverse=True)),
        }


def required(field: str, severity: Severity = Severity.ERROR) -> Rule:
    return Rule(
        rule_id=f"REQUIRED.{field}",
        description=f"{field} must be present and non-empty",
        severity=severity,
        predicate=lambda record: record.get(field) not in (None, ""),
        message=f"{field} is required",
        field=field,
    )


def one_of(field: str, allowed: Sequence[object], severity: Severity = Severity.ERROR) -> Rule:
    allowed_values = frozenset(allowed)
    return Rule(
        rule_id=f"DOMAIN.{field}",
        description=f"{field} must be in the governed domain",
        severity=severity,
        predicate=lambda record: record.get(field) in allowed_values,
        message=f"{field} is outside the governed domain",
        field=field,
    )


def positive(field: str, severity: Severity = Severity.ERROR) -> Rule:
    def predicate(record: Mapping[str, object]) -> bool:
        value = record.get(field)
        return value is not None and float(value) > 0

    return Rule(
        rule_id=f"POSITIVE.{field}",
        description=f"{field} must be positive",
        severity=severity,
        predicate=predicate,
        message=f"{field} must be greater than zero",
        field=field,
    )


def application_event_engine() -> RulesEngine:
    return RulesEngine(
        [
            required("event_id", Severity.FATAL),
            required("application_id", Severity.FATAL),
            required("event_type"),
            required("event_ts"),
            positive("event_version"),
            one_of(
                "application_status",
                [
                    "SUBMITTED",
                    "DOCUMENTS_PENDING",
                    "REVIEW",
                    "READY_FOR_UNDERWRITING",
                    "UNDERWRITING",
                    "DECISIONED",
                    "FUNDED",
                    "CANCELLED",
                ],
            ),
        ]
    )
