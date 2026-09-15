from pathlib import Path

from pyspark.sql import functions as F

from oakbridge.config.settings import Settings
from oakbridge.schemas.application import APPLICATION_EVENT_SCHEMA
from oakbridge.transforms.application import with_application_dq


def reconcile_applications(spark, cfg: Settings) -> dict:
    landing = cfg.landing_path("application_events")
    source = spark.read.schema(APPLICATION_EVENT_SCHEMA).json(landing)
    checked = with_application_dq(source)

    source_count = source.count()
    invalid_count = checked.filter(F.col("dq_reason").isNotNull()).count()
    valid = checked.filter(F.col("dq_reason").isNull())
    valid_count = valid.count()
    unique_valid_count = valid.select("event_id").distinct().count()
    duplicate_valid_count = valid_count - unique_valid_count

    history_path = cfg.silver_path("loan_application_status_history")
    history_count = spark.read.parquet(history_path).count() if Path(history_path).exists() else 0

    explained = invalid_count + duplicate_valid_count + history_count
    result = {
        "source_count": source_count,
        "invalid_count": invalid_count,
        "duplicate_valid_count": duplicate_valid_count,
        "history_count": history_count,
        "explained_count": explained,
        "balanced": source_count == explained,
    }

    spark.createDataFrame([result]).write.mode("overwrite").json(
        cfg.ops_path("application_reconciliation")
    )
    return result
