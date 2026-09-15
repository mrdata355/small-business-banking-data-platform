from decimal import Decimal

from oakbridge.risk.exposure import Exposure, ExposureAnalytics


def sample_exposures():
    return [
        Exposure("E1", "B1", "DENTAL", "FL", "SBA_7A", Decimal("100"), Decimal("100"), Decimal("0.02"), Decimal("0.40")),
        Exposure("E2", "B2", "DENTAL", "GA", "SBA_7A", Decimal("200"), Decimal("200"), Decimal("0.03"), Decimal("0.40")),
        Exposure("E3", "B3", "VET", "FL", "CONVENTIONAL", Decimal("700"), Decimal("700"), Decimal("0.01"), Decimal("0.35")),
    ]


def test_concentration_shares_sum_to_one():
    analytics = ExposureAnalytics(sample_exposures())
    rows = analytics.concentration("industry")
    assert sum((row.share_of_portfolio for row in rows), Decimal("0")) == Decimal("1")
    assert rows[0].key == "VET"


def test_stress_increases_expected_loss():
    analytics = ExposureAnalytics(sample_exposures())
    stressed = analytics.stress(Decimal("2"), Decimal("0.10"))
    assert stressed["stressed_expected_loss"] > stressed["baseline_expected_loss"]


def test_limits_detect_excess_concentration():
    analytics = ExposureAnalytics(sample_exposures())
    findings = analytics.limits({"industry": Decimal("0.60")})
    assert findings
    assert findings[0]["severity"] == "BREACH"
