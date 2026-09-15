from pyspark import pipelines as dp
from pyspark.sql import functions as F

CATALOG = spark.conf.get("oakbridge.catalog", "main")
SILVER = CATALOG + ".silver_treasury.ach_transaction"

@dp.materialized_view(name="activity_daily", comment="Daily treasury activity by business, direction, and status")
def activity_daily():
    return (
        spark.read.table(SILVER)
        .withColumn("activity_date", F.to_date("event_ts"))
        .groupBy("activity_date", "business_id", "direction", "transaction_status")
        .agg(
            F.count("*").alias("transaction_count"),
            F.sum("amount").alias("total_amount"),
            F.avg("amount").alias("average_amount"),
            F.max("amount").alias("largest_transaction"),
        )
    )

@dp.materialized_view(name="ach_risk_watch", comment="High-value and returned ACH activity for operations review")
def ach_risk_watch():
    return (
        spark.read.table(SILVER)
        .filter((F.col("amount") >= 10000) | (F.col("transaction_status") == "RETURNED"))
        .withColumn(
            "risk_signal",
            F.when(F.col("transaction_status") == "RETURNED", F.lit("RETURN"))
            .when(F.col("amount") >= 50000, F.lit("HIGH_VALUE"))
            .otherwise(F.lit("REVIEW")),
        )
    )
