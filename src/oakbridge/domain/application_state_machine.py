from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import StrEnum
from typing import Iterable, Mapping


class ApplicationStatus(StrEnum):
    SUBMITTED = "SUBMITTED"
    DOCUMENTS_PENDING = "DOCUMENTS_PENDING"
    REVIEW = "REVIEW"
    READY_FOR_UNDERWRITING = "READY_FOR_UNDERWRITING"
    UNDERWRITING = "UNDERWRITING"
    DECISIONED = "DECISIONED"
    FUNDED = "FUNDED"
    CANCELLED = "CANCELLED"


class IdentityStatus(StrEnum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REVIEW = "REVIEW"
    FAILED = "FAILED"


@dataclass(frozen=True)
class ApplicationEvent:
    event_id: str
    application_id: str
    event_type: str
    event_version: int
    event_ts: datetime
    source_system: str
    payload: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ApplicationState:
    application_id: str
    version: int = 0
    status: ApplicationStatus = ApplicationStatus.SUBMITTED
    documents_complete: bool = False
    financial_package_complete: bool = False
    identity_status: IdentityStatus = IdentityStatus.PENDING
    decision: str | None = None
    funded_amount: float | None = None
    updated_at: datetime | None = None
    last_event_id: str | None = None
    last_source_system: str | None = None

    @property
    def ready_for_underwriting(self) -> bool:
        return (
            self.documents_complete
            and self.financial_package_complete
            and self.identity_status == IdentityStatus.VERIFIED
            and self.status not in {ApplicationStatus.CANCELLED, ApplicationStatus.FUNDED}
        )


@dataclass(frozen=True)
class ReductionResult:
    previous: ApplicationState
    current: ApplicationState
    applied: bool
    reason: str
    event_id: str


class ApplicationStateMachine:
    """Deterministic reducer for canonical lending state.

    Delivery identity and business precedence are different concerns. Replayed event IDs
    are ignored, stale versions are preserved in history but cannot overwrite current
    state, and readiness is derived from canonical prerequisites rather than transport
    arrival order.
    """

    def __init__(self) -> None:
        self._seen_event_ids: set[str] = set()

    def reduce(self, state: ApplicationState, event: ApplicationEvent) -> ReductionResult:
        if event.application_id != state.application_id:
            return ReductionResult(state, state, False, "APPLICATION_KEY_MISMATCH", event.event_id)
        if event.event_id in self._seen_event_ids:
            return ReductionResult(state, state, False, "DUPLICATE_EVENT_ID", event.event_id)
        self._seen_event_ids.add(event.event_id)
        if event.event_version <= 0:
            return ReductionResult(state, state, False, "INVALID_EVENT_VERSION", event.event_id)
        if event.event_version < state.version:
            return ReductionResult(state, state, False, "STALE_EVENT_VERSION", event.event_id)
        if event.event_version == state.version and state.last_event_id != event.event_id:
            return ReductionResult(state, state, False, "VERSION_COLLISION", event.event_id)

        current = self._apply(state, event)
        return ReductionResult(state, current, current != state, "APPLIED", event.event_id)

    def reduce_many(self, application_id: str, events: Iterable[ApplicationEvent]) -> ApplicationState:
        state = ApplicationState(application_id=application_id)
        ordered = sorted(events, key=lambda e: (e.event_version, e.event_ts, e.event_id))
        for event in ordered:
            state = self.reduce(state, event).current
        return state

    def _apply(self, state: ApplicationState, event: ApplicationEvent) -> ApplicationState:
        payload = dict(event.payload)
        changes: dict[str, object] = {
            "version": event.event_version,
            "updated_at": event.event_ts,
            "last_event_id": event.event_id,
            "last_source_system": event.source_system,
        }

        if event.event_type == "LoanApplicationSubmitted":
            changes["status"] = ApplicationStatus.SUBMITTED
        elif event.event_type == "DocumentReceived":
            changes["documents_complete"] = bool(payload.get("documents_complete", True))
            changes["status"] = ApplicationStatus.DOCUMENTS_PENDING
        elif event.event_type == "FinancialPackageReceived":
            changes["financial_package_complete"] = bool(
                payload.get("financial_package_complete", True)
            )
            changes["status"] = ApplicationStatus.REVIEW
        elif event.event_type == "IdentityVerificationUpdated":
            changes["identity_status"] = IdentityStatus(
                str(payload.get("identity_status", "VERIFIED"))
            )
        elif event.event_type == "UnderwritingStarted":
            changes["status"] = ApplicationStatus.UNDERWRITING
        elif event.event_type == "Decisioned":
            changes["status"] = ApplicationStatus.DECISIONED
            changes["decision"] = str(payload.get("decision", "UNKNOWN"))
        elif event.event_type == "Funded":
            changes["status"] = ApplicationStatus.FUNDED
            amount = payload.get("funded_amount")
            changes["funded_amount"] = (
                float(amount) if amount is not None else state.funded_amount
            )
        elif event.event_type == "Cancelled":
            changes["status"] = ApplicationStatus.CANCELLED
        else:
            raise ValueError(f"unsupported application event type: {event.event_type}")

        candidate = replace(state, **changes)
        if candidate.ready_for_underwriting and candidate.status in {
            ApplicationStatus.SUBMITTED,
            ApplicationStatus.DOCUMENTS_PENDING,
            ApplicationStatus.REVIEW,
        }:
            candidate = replace(candidate, status=ApplicationStatus.READY_FOR_UNDERWRITING)
        return candidate


def parse_event(record: Mapping[str, object]) -> ApplicationEvent:
    event_ts = record["event_ts"]
    if isinstance(event_ts, str):
        event_ts = datetime.fromisoformat(event_ts.replace("Z", "+00:00"))
    if not isinstance(event_ts, datetime):
        raise TypeError("event_ts must be ISO timestamp or datetime")
    if event_ts.tzinfo is None:
        event_ts = event_ts.replace(tzinfo=timezone.utc)
    reserved = {
        "event_id",
        "application_id",
        "event_type",
        "event_version",
        "event_ts",
        "source_system",
    }
    payload = {k: v for k, v in record.items() if k not in reserved}
    return ApplicationEvent(
        event_id=str(record["event_id"]),
        application_id=str(record["application_id"]),
        event_type=str(record["event_type"]),
        event_version=int(record["event_version"]),
        event_ts=event_ts,
        source_system=str(record["source_system"]),
        payload=payload,
    )
