from __future__ import annotations

import dataclasses
import heapq
import math
import random
import statistics
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Callable, Iterable


class EventType(StrEnum):
    APPLICATION_SUBMITTED = "APPLICATION_SUBMITTED"
    DOCUMENT_RECEIVED = "DOCUMENT_RECEIVED"
    IDENTITY_VERIFIED = "IDENTITY_VERIFIED"
    FINANCIAL_PACKAGE_RECEIVED = "FINANCIAL_PACKAGE_RECEIVED"
    UNDERWRITING_STARTED = "UNDERWRITING_STARTED"
    DECISIONED = "DECISIONED"
    FUNDED = "FUNDED"
    ACH_POSTED = "ACH_POSTED"
    ACH_RETURNED = "ACH_RETURNED"
    CUSTOMER_CONTACT = "CUSTOMER_CONTACT"
    PIPELINE_DEGRADED = "PIPELINE_DEGRADED"
    PIPELINE_RECOVERED = "PIPELINE_RECOVERED"


@dataclass(order=True)
class TwinEvent:
    at: datetime
    sequence: int
    event_type: EventType = field(compare=False)
    aggregate_id: str = field(compare=False)
    payload: dict = field(default_factory=dict, compare=False)


@dataclass
class ApplicationState:
    application_id: str
    industry: str
    requested_amount: float
    submitted_at: datetime
    documents_complete: bool = False
    identity_verified: bool = False
    financial_package_complete: bool = False
    underwriting_started_at: datetime | None = None
    decisioned_at: datetime | None = None
    funded_at: datetime | None = None
    decision: str | None = None
    event_version: int = 0

    @property
    def ready_for_underwriting(self) -> bool:
        return self.documents_complete and self.identity_verified and self.financial_package_complete


@dataclass
class PlatformState:
    applications: dict[str, ApplicationState] = field(default_factory=dict)
    pipeline_lag_ms: dict[str, int] = field(default_factory=dict)
    pipeline_status: dict[str, str] = field(default_factory=dict)
    counters: Counter = field(default_factory=Counter)
    time_series: dict[str, list[tuple[datetime, float]]] = field(default_factory=lambda: defaultdict(list))
    decisions: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class TwinPolicy:
    document_minutes_p50: float = 42
    identity_minutes_p50: float = 8
    financial_package_minutes_p50: float = 95
    underwriting_minutes_p50: float = 180
    approval_probability: float = 0.79
    funding_minutes_p50: float = 1440
    pipeline_base_lag_ms: int = 900
    pipeline_degraded_lag_ms: int = 45_000
    digital_contact_probability: float = 0.14


@dataclass(frozen=True)
class SimulationResult:
    seed: int
    applications: int
    approved: int
    funded: int
    declined: int
    approval_rate: float
    funded_rate: float
    median_time_to_decision_minutes: float
    p95_time_to_decision_minutes: float
    median_time_to_funding_minutes: float
    customer_contacts: int
    degraded_events: int
    max_pipeline_lag_ms: int
    state: PlatformState


def _lognormal_minutes(rng: random.Random, median: float, sigma: float = 0.45) -> float:
    return max(0.25, rng.lognormvariate(math.log(max(median, 0.25)), sigma))


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, math.ceil(q * len(ordered)) - 1))
    return float(ordered[idx])


class BankingDigitalTwin:
    """Discrete-event twin for generated small-business banking workloads.

    It is deliberately deterministic for a given seed so architecture changes can be
    compared with controlled counterfactual experiments.
    """

    def __init__(self, policy: TwinPolicy | None = None, seed: int = 7):
        self.policy = policy or TwinPolicy()
        self.seed = seed
        self.rng = random.Random(seed)
        self.state = PlatformState()
        self._queue: list[TwinEvent] = []
        self._sequence = 0
        self._handlers: dict[EventType, Callable[[TwinEvent], None]] = {
            EventType.APPLICATION_SUBMITTED: self._on_application_submitted,
            EventType.DOCUMENT_RECEIVED: self._on_document_received,
            EventType.IDENTITY_VERIFIED: self._on_identity_verified,
            EventType.FINANCIAL_PACKAGE_RECEIVED: self._on_financial_package,
            EventType.UNDERWRITING_STARTED: self._on_underwriting_started,
            EventType.DECISIONED: self._on_decisioned,
            EventType.FUNDED: self._on_funded,
            EventType.CUSTOMER_CONTACT: self._on_customer_contact,
            EventType.PIPELINE_DEGRADED: self._on_pipeline_degraded,
            EventType.PIPELINE_RECOVERED: self._on_pipeline_recovered,
            EventType.ACH_POSTED: self._on_ach_posted,
            EventType.ACH_RETURNED: self._on_ach_returned,
        }

    def schedule(self, event_type: EventType, aggregate_id: str, at: datetime, **payload) -> None:
        self._sequence += 1
        heapq.heappush(self._queue, TwinEvent(at, self._sequence, event_type, aggregate_id, payload))

    def seed_applications(
        self,
        count: int,
        start_at: datetime | None = None,
        industries: Iterable[str] | None = None,
    ) -> None:
        start_at = start_at or datetime.now(timezone.utc).replace(second=0, microsecond=0)
        choices = list(industries or ["Dental", "Veterinary", "Professional Services", "Technology", "Agriculture"])
        for index in range(count):
            app_id = f"TWIN-APP-{index + 1:07d}"
            amount = round(self.rng.triangular(75_000, 5_000_000, 450_000), 2)
            industry = self.rng.choice(choices)
            arrival = start_at + timedelta(seconds=self.rng.uniform(0, max(60, count * 5)))
            self.schedule(EventType.APPLICATION_SUBMITTED, app_id, arrival, amount=amount, industry=industry)

    def inject_pipeline_incident(self, at: datetime, duration_minutes: int, component: str = "canonical-merge") -> None:
        self.schedule(EventType.PIPELINE_DEGRADED, component, at, component=component)
        self.schedule(EventType.PIPELINE_RECOVERED, component, at + timedelta(minutes=duration_minutes), component=component)

    def run(self, until: datetime | None = None) -> SimulationResult:
        while self._queue:
            event = heapq.heappop(self._queue)
            if until and event.at > until:
                heapq.heappush(self._queue, event)
                break
            self.state.counters[event.event_type] += 1
            self._handlers[event.event_type](event)

        decision_minutes: list[float] = []
        funding_minutes: list[float] = []
        approved = funded = declined = 0
        for app in self.state.applications.values():
            if app.decisioned_at:
                decision_minutes.append((app.decisioned_at - app.submitted_at).total_seconds() / 60)
            if app.decision == "APPROVED":
                approved += 1
            elif app.decision == "DECLINED":
                declined += 1
            if app.funded_at:
                funded += 1
                funding_minutes.append((app.funded_at - app.submitted_at).total_seconds() / 60)

        total = len(self.state.applications)
        max_lag = max(self.state.pipeline_lag_ms.values(), default=0)
        return SimulationResult(
            seed=self.seed,
            applications=total,
            approved=approved,
            funded=funded,
            declined=declined,
            approval_rate=approved / total if total else 0.0,
            funded_rate=funded / total if total else 0.0,
            median_time_to_decision_minutes=statistics.median(decision_minutes) if decision_minutes else 0.0,
            p95_time_to_decision_minutes=_percentile(decision_minutes, 0.95),
            median_time_to_funding_minutes=statistics.median(funding_minutes) if funding_minutes else 0.0,
            customer_contacts=self.state.counters[EventType.CUSTOMER_CONTACT],
            degraded_events=self.state.counters[EventType.PIPELINE_DEGRADED],
            max_pipeline_lag_ms=max_lag,
            state=self.state,
        )

    def _app(self, event: TwinEvent) -> ApplicationState:
        return self.state.applications[event.aggregate_id]

    def _touch_version(self, app: ApplicationState) -> None:
        app.event_version += 1

    def _schedule_contact_maybe(self, app: ApplicationState, at: datetime) -> None:
        if self.rng.random() < self.policy.digital_contact_probability:
            self.schedule(EventType.CUSTOMER_CONTACT, app.application_id, at + timedelta(minutes=self.rng.uniform(4, 55)))

    def _on_application_submitted(self, event: TwinEvent) -> None:
        app = ApplicationState(
            application_id=event.aggregate_id,
            industry=event.payload["industry"],
            requested_amount=float(event.payload["amount"]),
            submitted_at=event.at,
            event_version=1,
        )
        self.state.applications[app.application_id] = app
        self.schedule(EventType.DOCUMENT_RECEIVED, app.application_id, event.at + timedelta(minutes=_lognormal_minutes(self.rng, self.policy.document_minutes_p50)))
        self.schedule(EventType.IDENTITY_VERIFIED, app.application_id, event.at + timedelta(minutes=_lognormal_minutes(self.rng, self.policy.identity_minutes_p50)))
        self.schedule(EventType.FINANCIAL_PACKAGE_RECEIVED, app.application_id, event.at + timedelta(minutes=_lognormal_minutes(self.rng, self.policy.financial_package_minutes_p50)))
        self._schedule_contact_maybe(app, event.at)

    def _maybe_start_underwriting(self, app: ApplicationState, at: datetime) -> None:
        if app.ready_for_underwriting and not app.underwriting_started_at:
            self.schedule(EventType.UNDERWRITING_STARTED, app.application_id, at)

    def _on_document_received(self, event: TwinEvent) -> None:
        app = self._app(event); app.documents_complete = True; self._touch_version(app); self._maybe_start_underwriting(app, event.at)

    def _on_identity_verified(self, event: TwinEvent) -> None:
        app = self._app(event); app.identity_verified = True; self._touch_version(app); self._maybe_start_underwriting(app, event.at)

    def _on_financial_package(self, event: TwinEvent) -> None:
        app = self._app(event); app.financial_package_complete = True; self._touch_version(app); self._maybe_start_underwriting(app, event.at)

    def _on_underwriting_started(self, event: TwinEvent) -> None:
        app = self._app(event)
        if app.underwriting_started_at:
            return
        app.underwriting_started_at = event.at; self._touch_version(app)
        duration = _lognormal_minutes(self.rng, self.policy.underwriting_minutes_p50, 0.55)
        self.schedule(EventType.DECISIONED, app.application_id, event.at + timedelta(minutes=duration))

    def _on_decisioned(self, event: TwinEvent) -> None:
        app = self._app(event)
        amount_penalty = min(0.28, max(0.0, (app.requested_amount - 1_000_000) / 12_000_000))
        industry_penalty = 0.08 if app.industry in {"Agriculture", "Hospitality"} else 0.0
        p_approve = max(0.08, self.policy.approval_probability - amount_penalty - industry_penalty)
        app.decision = "APPROVED" if self.rng.random() < p_approve else "DECLINED"
        app.decisioned_at = event.at; self._touch_version(app)
        self.state.decisions.append({"application_id": app.application_id, "decision": app.decision, "at": event.at.isoformat()})
        if app.decision == "APPROVED":
            self.schedule(EventType.FUNDED, app.application_id, event.at + timedelta(minutes=_lognormal_minutes(self.rng, self.policy.funding_minutes_p50, 0.6)))

    def _on_funded(self, event: TwinEvent) -> None:
        app = self._app(event); app.funded_at = event.at; self._touch_version(app)

    def _on_customer_contact(self, event: TwinEvent) -> None:
        self.state.time_series["customer_contact"].append((event.at, 1.0))

    def _on_pipeline_degraded(self, event: TwinEvent) -> None:
        component = event.payload["component"]
        self.state.pipeline_status[component] = "DEGRADED"
        self.state.pipeline_lag_ms[component] = self.policy.pipeline_degraded_lag_ms
        self.state.time_series[f"pipeline_lag:{component}"].append((event.at, self.policy.pipeline_degraded_lag_ms))

    def _on_pipeline_recovered(self, event: TwinEvent) -> None:
        component = event.payload["component"]
        self.state.pipeline_status[component] = "HEALTHY"
        self.state.pipeline_lag_ms[component] = self.policy.pipeline_base_lag_ms
        self.state.time_series[f"pipeline_lag:{component}"].append((event.at, self.policy.pipeline_base_lag_ms))

    def _on_ach_posted(self, event: TwinEvent) -> None:
        self.state.time_series["ach_amount"].append((event.at, float(event.payload.get("amount", 0))))

    def _on_ach_returned(self, event: TwinEvent) -> None:
        self.state.time_series["ach_return"].append((event.at, float(event.payload.get("amount", 0))))


def compare_policies(
    baseline: TwinPolicy,
    candidate: TwinPolicy,
    applications: int = 1000,
    seeds: Iterable[int] = range(10),
) -> dict:
    """Paired counterfactual experiment using identical random seeds."""
    baseline_results: list[SimulationResult] = []
    candidate_results: list[SimulationResult] = []
    for seed in seeds:
        b = BankingDigitalTwin(baseline, seed); b.seed_applications(applications); baseline_results.append(b.run())
        c = BankingDigitalTwin(candidate, seed); c.seed_applications(applications); candidate_results.append(c.run())

    def avg(attr: str, rows: list[SimulationResult]) -> float:
        return statistics.fmean(float(getattr(row, attr)) for row in rows)

    metrics = ["approval_rate", "funded_rate", "median_time_to_decision_minutes", "p95_time_to_decision_minutes", "median_time_to_funding_minutes", "customer_contacts"]
    return {
        metric: {
            "baseline": avg(metric, baseline_results),
            "candidate": avg(metric, candidate_results),
            "delta": avg(metric, candidate_results) - avg(metric, baseline_results),
        }
        for metric in metrics
    }
