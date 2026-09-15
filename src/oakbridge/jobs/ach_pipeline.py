from oakbridge.config.settings import Settings
from oakbridge.ingestion.local_file_stream import read_json_stream
from oakbridge.schemas.ach import ACH_EVENT_SCHEMA
from oakbridge.sinks.local_parquet import append_parquet
from oakbridge.transforms.ach import normalize_ach


def run_ach_pipeline(spark, cfg: Settings) -> None:
    landing = cfg.landing_path("ach_transactions")
    bronze = cfg.bronze_path("ach_transactions")

    raw = read_json_stream(spark, landing, ACH_EVENT_SCHEMA)
    (
        raw.writeStream
        .format("parquet")
        .option("path", bronze)
        .option("checkpointLocation", cfg.checkpoint_path("ach_bronze"))
        .trigger(availableNow=True)
        .start()
        .awaitTermination()
    )

    silver = (
        spark.readStream
        .schema(ACH_EVENT_SCHEMA)
        .parquet(bronze)
        .withWatermark("event_ts", "2 hours")
        .dropDuplicates(["transaction_id"])
        .transform(normalize_ach)
    )

    (
        silver.writeStream
        .foreachBatch(lambda df, batch_id: append_parquet(df, cfg.silver_path("ach_transaction")))
        .option("checkpointLocation", cfg.checkpoint_path("ach_silver"))
        .trigger(availableNow=True)
        .start()
        .awaitTermination()
    )
