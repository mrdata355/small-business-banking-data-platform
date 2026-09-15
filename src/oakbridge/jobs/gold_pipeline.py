from pathlib import Path

from pyspark.sql import functions as F

from oakbridge.config.settings import Settings


def _read_if_exists(spark, path: str):
    if not Path(path).exists():
        return None
    return spark.read.parquet(path)


def build_gold_outputs(spark, cfg: Settings) -> None:
    applications = _read_if_exists(spark, cfg.silver_path("loan_application"))
    identity = _read_if_exists(spark, cfg.silver_path("identity_verification"))
    ach = _read_if_exists(spark, cfg.silver_path("ach_transaction"))

    if applications is not None and identity is not None:
        readiness = (
            applications.alias("a")
            .join(
                identity.select(
                    "application_id",
                    F.col("verification_status").alias("identity_verification_status"),
                    "verification_ts",
                ).alias("i"),
                "application_id",
                "left",
            )
            .withColumn(
                "ready_for_underwriting",
                F.col("documents_complete")
                & F.col("financial_package_complete")
                & (F.col("identity_verification_status") == F.lit("VERIFIED")),
            )
        )
        readiness.write.mode("overwrite").parquet(
            cfg.gold_path("underwriting_readiness_queue")
        )

    if ach is not None:
        daily = (
            ach
            .withColumn("activity_date", F.to_date("event_ts"))
            .groupBy("activity_date", "business_id", "direction", "transaction_status")
            .agg(
                F.count("*").alias("transaction_count"),
                F.sum("amount").alias("total_amount"),
            )
        )
        daily.write.mode("overwrite").parquet(cfg.gold_path("treasury_activity_daily"))
