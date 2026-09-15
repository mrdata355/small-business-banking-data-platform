from oakbridge.quality.rules_engine import application_event_engine


def test_valid_application_event_passes_rules():
    result = application_event_engine().evaluate(
        {
            "event_id": "EVT-1",
            "application_id": "APP-1",
            "event_type": "LoanApplicationSubmitted",
            "event_ts": "2026-09-15T12:00:00Z",
            "event_version": 1,
            "application_status": "SUBMITTED",
        }
    )
    assert result.valid is True
    assert result.quarantine_reason is None


def test_invalid_event_produces_explainable_quarantine_reasons():
    result = application_event_engine().evaluate(
        {
            "event_id": "",
            "application_id": "APP-1",
            "event_type": "LoanApplicationSubmitted",
            "event_ts": "2026-09-15T12:00:00Z",
            "event_version": 0,
            "application_status": "UNKNOWN",
        }
    )
    assert result.valid is False
    assert "REQUIRED.event_id" in result.quarantine_reason
    assert "POSITIVE.event_version" in result.quarantine_reason
    assert "DOMAIN.application_status" in result.quarantine_reason
