from oakbridge.observability.slo_engine import (
    Health,
    SLOEngine,
    StreamObservation,
)


def observation(**overrides):
    values = {
        "timestamp_ms": 1,
        "input_rows_per_second": 100.0,
        "processed_rows_per_second": 130.0,
        "p95_freshness_ms": 10_000.0,
        "trigger_duration_ms": 2_000.0,
        "state_rows": 500,
        "source_lag_records": 100,
        "dq_reject_rate": 0.001,
        "sink_error_rate": 0.0,
    }
    values.update(overrides)
    return StreamObservation(**values)


def test_healthy_stream_requires_headroom_not_just_running_state():
    result = SLOEngine().evaluate(observation())
    assert result.health == Health.HEALTHY
    assert result.processing_headroom > 1.0


def test_stale_running_stream_is_breached():
    result = SLOEngine().evaluate(
        observation(p95_freshness_ms=180_000, processed_rows_per_second=80.0)
    )
    assert result.health == Health.BREACHED
    assert "FRESHNESS" in result.violations
    assert "PROCESSING_HEADROOM" in result.violations


def test_window_reports_breach_rate():
    engine = SLOEngine()
    result = engine.window(
        [observation(), observation(source_lag_records=100_000), observation()]
    )
    assert result["observations"] == 3
    assert result["breach_rate"] > 0
