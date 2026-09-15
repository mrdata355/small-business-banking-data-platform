from pyspark.sql import functions as F

from oakbridge.config.settings import Settings
from oakbridge.ingestion.local_file_stream import read_json_stream
from oakbridge.schemas.application import APPLICATION_EVENT_SCHEMA
from oakbridge.sinks.local_parquet import append_parquet, upsert_latest_parquet
from oakbridge.transforms.application import normalize_application, with_application_dq


def run_application_pipeline(spark, cfg: Settings) -> None:
    landing = cfg.landing_path("application_events")
    bronze = cfg.bronze_path("application_events")

    raw = read_json_stream(spark, landing, APPLICATION_EVENT_SCHEMA)
    (
        raw.writeStream
        .format("parquet")
        .option("path", bronze)
        .option("checkpointLocation", cfg.checkpoint_path("application_bronze"))
        .trigger(availableNow=True)
        .start()
        .awaitTermination()
    )

    bronze_df = spark.readStream.schema(APPLICATION_EVENT_SCHEMA).parquet(bronze)
    checked = with_application_dq(bronze_df)

    invalid = checked.filter(F.col("dq_reason").isNotNull())
    (
        invalid.writeStream
        .format("parquet")
        .option("path", cfg.quarantine_path("application_events"))
        .option("checkpointLocation", cfg.checkpoint_path("application_quarantine"))
        .trigger(availableNow=True)
        .start()
        .awaitTermination()
    )

    valid = checked.filter(F.col("dq_reason").isNull()).drop("dq_reason")
    deduped = (
        valid
        .withWatermark("event_ts", "2 hours")
        .dropDuplicates(["event_id"])
        .transform(normalize_application)
    )

    history_path = cfg.silver_path("loan_application_status_history")
    current_path = cfg.silver_path("loan_application")

    def persist(batch_df, batch_id):
        batch_df.cache()
        append_parquet(batch_df, history_path)
        upsert_latest_parquet(
            batch_df,
            current_path,
            key_columns=["application_id"],
            order_columns=["event_version", "event_ts"],
        )
        batch_df.unpersist()

    (
        deduped.writeStream
        .foreachBatch(persist)
        .option("checkpointLocation", cfg.checkpoint_path("application_silver"))
        .trigger(availableNow=True)
        .start()
        .awaitTermination()
    )
