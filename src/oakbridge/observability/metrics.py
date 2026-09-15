from __future__ import annotations

from pyspark.sql import functions as F


def freshness_summary(df, event_time_column: str = "event_ts"):
    return (
        df
        .withColumn(
            "_freshness_seconds",
            F.unix_timestamp(F.current_timestamp()) - F.unix_timestamp(event_time_column),
        )
        .agg(
            F.expr("percentile_approx(_freshness_seconds, 0.50)").alias("p50_seconds"),
            F.expr("percentile_approx(_freshness_seconds, 0.95)").alias("p95_seconds"),
            F.max("_freshness_seconds").alias("max_seconds"),
        )
    )
