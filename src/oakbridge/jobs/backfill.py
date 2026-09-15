from pathlib import Path

from oakbridge.config.settings import Settings
from oakbridge.schemas.application import APPLICATION_EVENT_SCHEMA
from oakbridge.sinks.local_parquet import upsert_latest_parquet
from oakbridge.transforms.application import normalize_application, with_application_dq


def replay_application_range(spark, cfg: Settings) -> None:
    bronze = cfg.bronze_path("application_events")
    if not Path(bronze).exists():
        return

    source = spark.read.schema(APPLICATION_EVENT_SCHEMA).parquet(bronze)
    valid = (
        with_application_dq(source)
        .filter("dq_reason IS NULL")
        .drop("dq_reason")
        .dropDuplicates(["event_id"])
        .transform(normalize_application)
    )

    valid.cache()
    upsert_latest_parquet(
        valid,
        cfg.silver_path("loan_application"),
        key_columns=["application_id"],
        order_columns=["event_version", "event_ts"],
    )
    valid.unpersist()
