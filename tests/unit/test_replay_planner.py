from datetime import datetime, timezone

from oakbridge.spark.replay import ReplayMode, ReplayPlanner, ReplayRange


def replay_range():
    return ReplayRange(
        start_event_time=datetime(2026, 9, 14, 10, 15, tzinfo=timezone.utc),
        end_event_time=datetime(2026, 9, 14, 13, 45, tzinfo=timezone.utc),
        source_paths=("s3a://oakbridge-bronze/lending/application_event/",),
    )


def test_repair_plan_preserves_checkpoint_and_uses_idempotent_merge():
    plan = ReplayPlanner().plan("R-1", replay_range(), ReplayMode.REPAIR)
    assert "preserve" in plan.checkpoint_action
    assert "idempotent merge" in plan.target_strategy
    assert plan.mode == ReplayMode.REPAIR


def test_hour_splitting_covers_full_range_without_overlap():
    windows = ReplayPlanner().split_by_hour(replay_range())
    assert windows[0][0] == replay_range().start_event_time
    assert windows[-1][1] == replay_range().end_event_time
    for left, right in zip(windows, windows[1:]):
        assert left[1] == right[0]


def test_replay_result_requires_zero_unexplained_delta():
    result = ReplayPlanner().validate_result(
        source_count=100,
        target_count=97,
        quarantine_count=2,
        duplicate_count=1,
    )
    assert result["balanced"] is True
    assert result["unexplained_delta"] == 0
