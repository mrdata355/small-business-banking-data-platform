from oakbridge.transforms.application import VALID_APPLICATION_STATUS, VALID_EVENT_TYPES


def test_expected_application_statuses_are_defined():
    assert "READY_FOR_UNDERWRITING" in VALID_APPLICATION_STATUS
    assert "FUNDED" in VALID_APPLICATION_STATUS


def test_expected_event_types_are_defined():
    assert "LoanApplicationSubmitted" in VALID_EVENT_TYPES
    assert "FinancialPackageReceived" in VALID_EVENT_TYPES
