from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Iterable


class ReplayMode(StrEnum):
    DRY_RUN = "DRY_RUN"
    REPAIR = "REPAIR"
    REBUILD = "REBUILD"


@dataclass(frozen=True)
class ReplayRange:
    start_event_time: datetime
    end_event_time: datetime
    source_paths: tuple[str, ...]
    affected_business_keys: tuple[str, ...] = ()

    def validate(self) -> None:
        if self.start_event_time.tzinfo is None or self.end_event_time.tzinfo is None:
            raise ValueError("replay boundaries must be timezone-aware")
        if self.start_event_time >= self.end_event_time:
            raise ValueError("replay start must be before replay end")
        if not self.source_paths:
            raise ValueError("replay requires at least one immutable source path")


@dataclass(frozen=True)
class ReplayPlan:
    replay_id: str
    mode: ReplayMode
    affected_range: ReplayRange
    checkpoint_action: str
    target_strategy: str
    throttle_rows_per_second: int | None
    preconditions: tuple[str, ...]
    postconditions: tuple[str, ...]
    created_at: datetime


class ReplayPlanner:
    """Creates explicit, auditable replay plans instead of deleting checkpoints blindly."""

    DEFAULT_PRECONDITIONS = (
        "immutable source range is readable",
        "current checkpoint is preserved",
        "target state is backed up or versioned",
        "code artifact and configuration are pinned",
        "business keys and expected source counts are captured",
    )
    DEFAULT_POSTCONDITIONS = (
        "source-to-target reconciliation is balanced",
        "no duplicate current-state business keys exist",
        "quarantine is explained",
        "freshness returns inside SLO",
        "customer-facing state is sampled and validated",
    )

    def plan(
        self,
        replay_id: str,
        affected_range: ReplayRange,
        mode: ReplayMode = ReplayMode.REPAIR,
        throttle_rows_per_second: int | None = None,
    ) -> ReplayPlan:
        affected_range.validate()
        if throttle_rows_per_second is not None and throttle_rows_per_second <= 0:
            raise ValueError("throttle_rows_per_second must be positive")
        if mode == ReplayMode.REBUILD:
            target_strategy = "rebuild isolated target, validate, then atomically promote"
        elif mode == ReplayMode.REPAIR:
            target_strategy = "idempotent merge into canonical target using stable keys and precedence"
        else:
            target_strategy = "read, transform, calculate diffs, write no canonical changes"
        return ReplayPlan(
            replay_id=replay_id,
            mode=mode,
            affected_range=affected_range,
            checkpoint_action="preserve existing checkpoint; use isolated replay progress path",
            target_strategy=target_strategy,
            throttle_rows_per_second=throttle_rows_per_second,
            preconditions=self.DEFAULT_PRECONDITIONS,
            postconditions=self.DEFAULT_POSTCONDITIONS,
            created_at=datetime.now(timezone.utc),
        )

    def split_by_hour(self, replay_range: ReplayRange) -> list[tuple[datetime, datetime]]:
        replay_range.validate()
        windows: list[tuple[datetime, datetime]] = []
        current = replay_range.start_event_time
        while current < replay_range.end_event_time:
            next_hour = current.replace(minute=0, second=0, microsecond=0)
            if next_hour <= current:
                from datetime import timedelta

                next_hour += timedelta(hours=1)
            end = min(next_hour, replay_range.end_event_time)
            windows.append((current, end))
            current = end
        return windows

    def object_predicates(self, replay_range: ReplayRange) -> tuple[str, ...]:
        replay_range.validate()
        days: list[str] = []
        current = replay_range.start_event_time.date()
        end = replay_range.end_event_time.date()
        from datetime import timedelta

        while current <= end:
            days.append(f"event_date={current.isoformat()}")
            current += timedelta(days=1)
        return tuple(days)

    def validate_result(
        self,
        source_count: int,
        target_count: int,
        quarantine_count: int,
        duplicate_count: int,
        unexplained_keys: Iterable[str] = (),
    ) -> dict:
        explained = target_count + quarantine_count + duplicate_count
        delta = source_count - explained
        unexplained = tuple(unexplained_keys)
        return {
            "source_count": source_count,
            "target_count": target_count,
            "quarantine_count": quarantine_count,
            "duplicate_count": duplicate_count,
            "explained_count": explained,
            "unexplained_delta": delta,
            "unexplained_keys": unexplained,
            "balanced": delta == 0 and not unexplained,
        }
