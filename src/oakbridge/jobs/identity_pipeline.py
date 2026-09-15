from oakbridge.config.settings import Settings
from oakbridge.ingestion.local_file_stream import read_json_stream
from oakbridge.schemas.identity import IDENTITY_SCHEMA
from oakbridge.sinks.local_parquet import upsert_latest_parquet
from oakbridge.transforms.identity import normalize_identity


def run_identity_pipeline(spark, cfg: Settings) -> None:
    landing = cfg.landing_path("identity_verification")
    bronze = cfg.bronze_path("identity_verification")

    raw = read_json_stream(spark, landing, IDENTITY_SCHEMA)
    (
        raw.writeStream
        .format("parquet")
        .option("path", bronze)
        .option("checkpointLocation", cfg.checkpoint_path("identity_bronze"))
        .trigger(availableNow=True)
        .start()
        .awaitTermination()
    )

    silver = spark.readStream.schema(IDENTITY_SCHEMA).parquet(bronze).transform(normalize_identity)

    def persist(batch_df, batch_id):
        upsert_latest_parquet(
            batch_df,
            cfg.silver_path("identity_verification"),
            key_columns=["application_id"],
            order_columns=["verification_ts"],
        )

    (
        silver.writeStream
        .foreachBatch(persist)
        .option("checkpointLocation", cfg.checkpoint_path("identity_silver"))
        .trigger(availableNow=True)
        .start()
        .awaitTermination()
    )
