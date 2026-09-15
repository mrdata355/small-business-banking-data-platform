from datetime import datetime, timezone

from oakbridge.domain.application_state_machine import (
    ApplicationEvent,
    ApplicationState,
    ApplicationStateMachine,
    ApplicationStatus,
)


def event(event_id: str, version: int, event_type: str, **payload) -> ApplicationEvent:
    return ApplicationEvent(
        event_id=event_id,
        application_id="APP-1",
        event_type=event_type,
        event_version=version,
        event_ts=datetime(2026, 9, 15, 12, version, tzinfo=timezone.utc),
        source_system="test",
        payload=payload,
    )


def test_readiness_is_derived_from_canonical_prerequisites():
    machine = ApplicationStateMachine()
    state = ApplicationState(application_id="APP-1")
    state = machine.reduce(state, event("e1", 1, "LoanApplicationSubmitted")).current
    state = machine.reduce(state, event("e2", 2, "DocumentReceived")).current
    state = machine.reduce(state, event("e3", 3, "FinancialPackageReceived")).current
    state = machine.reduce(
        state,
        event("e4", 4, "IdentityVerificationUpdated", identity_status="VERIFIED"),
    ).current
    assert state.ready_for_underwriting is True
    assert state.status == ApplicationStatus.READY_FOR_UNDERWRITING


def test_duplicate_delivery_is_ignored():
    machine = ApplicationStateMachine()
    state = ApplicationState(application_id="APP-1")
    first = event("same", 1, "LoanApplicationSubmitted")
    state = machine.reduce(state, first).current
    replay = machine.reduce(state, first)
    assert replay.applied is False
    assert replay.reason == "DUPLICATE_EVENT_ID"
    assert replay.current.version == 1


def test_stale_event_cannot_overwrite_newer_state():
    machine = ApplicationStateMachine()
    state = ApplicationState(application_id="APP-1")
    state = machine.reduce(state, event("e3", 3, "FinancialPackageReceived")).current
    stale = machine.reduce(state, event("e2", 2, "DocumentReceived"))
    assert stale.applied is False
    assert stale.reason == "STALE_EVENT_VERSION"
    assert stale.current.version == 3
