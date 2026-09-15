from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from pyspark.sql import DataFrame, functions as F


@dataclass(frozen=True)
class PartitionProfile:
    partitions: int
    min_rows: int
    median_rows: float
    p95_rows: float
    max_rows: int
    max_to_median_ratio: float
    empty_partitions: int


@dataclass(frozen=True)
class JoinRecommendation:
    strategy: str
    rationale: str
    estimated_small_side_bytes: int
    estimated_large_side_bytes: int
    broadcast_threshold_bytes: int


def partition_row_counts(df: DataFrame) -> list[int]:
    return df.rdd.mapPartitions(lambda rows: [sum(1 for _ in rows)]).collect()


def _percentile(values: list[int], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * q))))
    return float(ordered[index])


def profile_partitions(df: DataFrame) -> PartitionProfile:
    counts = partition_row_counts(df)
    if not counts:
        return PartitionProfile(0, 0, 0.0, 0.0, 0, 0.0, 0)
    median = _percentile(counts, 0.50)
    maximum = max(counts)
    ratio = maximum / median if median else float("inf") if maximum else 0.0
    return PartitionProfile(
        partitions=len(counts),
        min_rows=min(counts),
        median_rows=median,
        p95_rows=_percentile(counts, 0.95),
        max_rows=maximum,
        max_to_median_ratio=ratio,
        empty_partitions=sum(count == 0 for count in counts),
    )


def hot_keys(
    df: DataFrame,
    key_columns: Iterable[str],
    limit: int = 25,
) -> DataFrame:
    keys = list(key_columns)
    if not keys:
        raise ValueError("key_columns cannot be empty")
    return (
        df.groupBy(*keys)
        .count()
        .withColumn(
            "share_of_rows",
            F.col("count") / F.sum("count").over(__import__("pyspark").sql.Window.partitionBy()),
        )
        .orderBy(F.desc("count"))
        .limit(limit)
    )


def estimate_dataframe_size_bytes(df: DataFrame) -> int | None:
    try:
        optimized = df._jdf.queryExecution().optimizedPlan()
        size = int(optimized.stats().sizeInBytes())
        if size < 0 or size >= 2**63 - 1:
            return None
        return size
    except Exception:
        return None


def recommend_join_strategy(
    left: DataFrame,
    right: DataFrame,
    broadcast_threshold_bytes: int = 10 * 1024 * 1024,
) -> JoinRecommendation:
    left_size = estimate_dataframe_size_bytes(left)
    right_size = estimate_dataframe_size_bytes(right)
    if left_size is None or right_size is None:
        return JoinRecommendation(
            strategy="MEASURE_STATS_FIRST",
            rationale="Catalyst statistics are unavailable; collect table/file statistics before forcing a join hint.",
            estimated_small_side_bytes=-1,
            estimated_large_side_bytes=-1,
            broadcast_threshold_bytes=broadcast_threshold_bytes,
        )
    small = min(left_size, right_size)
    large = max(left_size, right_size)
    if small <= broadcast_threshold_bytes and large > small * 4:
        strategy = "BROADCAST_SMALL_SIDE"
        rationale = (
            "The smaller relation fits the configured broadcast envelope and is materially smaller "
            "than the opposite side; validate the physical plan and executor memory before forcing it."
        )
    else:
        strategy = "SHUFFLE_HASH_OR_SORT_MERGE"
        rationale = (
            "Broadcast is not clearly justified by current size estimates; preserve adaptive planning "
            "and inspect skew, partition sizes and the executed plan."
        )
    return JoinRecommendation(strategy, rationale, small, large, broadcast_threshold_bytes)


def explain_formatted(df: DataFrame) -> str:
    return df._sc._jvm.PythonSQLUtils.explainString(df._jdf.queryExecution(), "formatted")


def cardinality_guard(
    before_count: int,
    after_count: int,
    relationship: str,
    tolerance: float = 0.0,
) -> dict:
    if before_count < 0 or after_count < 0:
        raise ValueError("counts cannot be negative")
    relationship = relationship.upper()
    if relationship == "ONE_TO_ONE":
        expected_min = before_count * (1 - tolerance)
        expected_max = before_count * (1 + tolerance)
        valid = expected_min <= after_count <= expected_max
    elif relationship == "LEFT_PRESERVING":
        expected_min = before_count
        expected_max = float("inf")
        valid = after_count >= before_count
    elif relationship == "FILTERING":
        expected_min = 0
        expected_max = before_count
        valid = after_count <= before_count
    else:
        raise ValueError(f"unsupported relationship: {relationship}")
    return {
        "relationship": relationship,
        "before_count": before_count,
        "after_count": after_count,
        "row_multiplier": after_count / before_count if before_count else 0.0,
        "expected_min": expected_min,
        "expected_max": expected_max,
        "valid": valid,
    }
