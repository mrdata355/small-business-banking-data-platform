from oakbridge.config.settings import Settings
from oakbridge.ingestion.local_file_stream import read_json_stream
from oakbridge.schemas.onboarding import BUSINESS_ONBOARDING_SCHEMA
from oakbridge.sinks.local_parquet import upsert_latest_parquet
from oakbridge.transforms.onboarding import normalize_onboarding


def run_onboarding_pipeline(spark, cfg: Settings) -> None:
    landing = cfg.landing_path("business_onboarding")
    bronze = cfg.bronze_path("business_onboarding")

    raw = read_json_stream(spark, landing, BUSINESS_ONBOARDING_SCHEMA)
    (
        raw.writeStream
        .format("parquet")
        .option("path", bronze)
        .option("checkpointLocation", cfg.checkpoint_path("onboarding_bronze"))
        .trigger(availableNow=True)
        .start()
        .awaitTermination()
    )

    stream = (
        spark.readStream
        .schema(BUSINESS_ONBOARDING_SCHEMA)
        .parquet(bronze)
        .withWatermark("event_ts", "2 hours")
        .dropDuplicates(["onboarding_event_id"])
        .transform(normalize_onboarding)
    )

    def persist(batch_df, batch_id):
        upsert_latest_parquet(
            batch_df,
            cfg.silver_path("business_onboarding"),
            key_columns=["business_id"],
            order_columns=["event_ts"],
        )

    (
        stream.writeStream
        .foreachBatch(persist)
        .option("checkpointLocation", cfg.checkpoint_path("onboarding_silver"))
        .trigger(availableNow=True)
        .start()
        .awaitTermination()
    )
