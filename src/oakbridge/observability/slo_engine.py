from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable


class Health(StrEnum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    BREACHED = "BREACHED"


@dataclass(frozen=True)
class StreamObservation:
    timestamp_ms: int
    input_rows_per_second: float
    processed_rows_per_second: float
    p95_freshness_ms: float
    trigger_duration_ms: float
    state_rows: int
    source_lag_records: int
    dq_reject_rate: float
    sink_error_rate: float


@dataclass(frozen=True)
class StreamSLO:
    max_p95_freshness_ms: float = 60_000
    max_source_lag_records: int = 10_000
    max_dq_reject_rate: float = 0.02
    max_sink_error_rate: float = 0.001
    min_processing_headroom: float = 1.05
    max_trigger_utilization: float = 0.85
    trigger_interval_ms: float = 5_000


@dataclass(frozen=True)
class SLOResult:
    health: Health
    violations: tuple[str, ...]
    burn_rate: float
    processing_headroom: float
    trigger_utilization: float


class SLOEngine:
    def __init__(self, slo: StreamSLO | None = None) -> None:
        self.slo = slo or StreamSLO()

    def evaluate(self, observation: StreamObservation) -> SLOResult:
        violations: list[str] = []
        incoming = max(0.000001, observation.input_rows_per_second)
        headroom = observation.processed_rows_per_second / incoming
        trigger_utilization = observation.trigger_duration_ms / self.slo.trigger_interval_ms

        if observation.p95_freshness_ms > self.slo.max_p95_freshness_ms:
            violations.append("FRESHNESS")
        if observation.source_lag_records > self.slo.max_source_lag_records:
            violations.append("SOURCE_LAG")
        if observation.dq_reject_rate > self.slo.max_dq_reject_rate:
            violations.append("DATA_QUALITY")
        if observation.sink_error_rate > self.slo.max_sink_error_rate:
            violations.append("SINK_ERRORS")
        if headroom < self.slo.min_processing_headroom:
            violations.append("PROCESSING_HEADROOM")
        if trigger_utilization > self.slo.max_trigger_utilization:
            violations.append("TRIGGER_UTILIZATION")

        burn_rate = max(
            observation.p95_freshness_ms / max(self.slo.max_p95_freshness_ms, 1),
            observation.source_lag_records / max(self.slo.max_source_lag_records, 1),
            observation.dq_reject_rate / max(self.slo.max_dq_reject_rate, 1e-9),
            observation.sink_error_rate / max(self.slo.max_sink_error_rate, 1e-9),
            self.slo.min_processing_headroom / max(headroom, 1e-9),
            trigger_utilization / max(self.slo.max_trigger_utilization, 1e-9),
        )
        if not violations:
            health = Health.HEALTHY
        elif burn_rate < 2:
            health = Health.DEGRADED
        else:
            health = Health.BREACHED
        return SLOResult(
            health=health,
            violations=tuple(violations),
            burn_rate=round(burn_rate, 4),
            processing_headroom=round(headroom, 4),
            trigger_utilization=round(trigger_utilization, 4),
        )

    def window(self, observations: Iterable[StreamObservation]) -> dict:
        rows = list(observations)
        if not rows:
            return {
                "health": Health.HEALTHY,
                "observations": 0,
                "availability": 1.0,
                "breach_rate": 0.0,
                "max_burn_rate": 0.0,
            }
        results = [self.evaluate(row) for row in rows]
        healthy = sum(result.health == Health.HEALTHY for result in results)
        breached = sum(result.health == Health.BREACHED for result in results)
        max_burn = max(result.burn_rate for result in results)
        overall = (
            Health.BREACHED
            if breached
            else Health.DEGRADED
            if healthy != len(results)
            else Health.HEALTHY
        )
        return {
            "health": overall,
            "observations": len(rows),
            "availability": healthy / len(rows),
            "breach_rate": breached / len(rows),
            "max_burn_rate": max_burn,
            "violations": sorted(
                {violation for result in results for violation in result.violations}
            ),
        }
