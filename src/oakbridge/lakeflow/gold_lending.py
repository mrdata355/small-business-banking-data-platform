from pyspark import pipelines as dp
from pyspark.sql import functions as F

CATALOG = spark.conf.get("oakbridge.catalog", "main")
SILVER = CATALOG + ".silver_lending.loan_application"

@dp.materialized_view(name="underwriting_readiness_queue", comment="Applications prioritized for underwriting review")
def underwriting_readiness_queue():
    return (
        spark.read.table(SILVER)
        .withColumn(
            "priority_score",
            F.when(F.col("ready_for_underwriting"), F.lit(100)).otherwise(F.lit(25))
            + F.when(F.col("requested_amount") >= 1000000, F.lit(20)).otherwise(F.lit(0))
            + F.when(F.col("event_age_seconds") > 3600, F.lit(15)).otherwise(F.lit(0)),
        )
        .select(
            "application_id",
            "customer_id",
            "business_id",
            "product_code",
            "requested_amount",
            "application_status",
            "documents_complete",
            "financial_package_complete",
            "ready_for_underwriting",
            "priority_score",
            "event_ts",
            "processed_ts",
        )
    )

@dp.materialized_view(name="application_funnel_daily", comment="Daily lending funnel by product and status")
def application_funnel_daily():
    return (
        spark.read.table(SILVER)
        .withColumn("activity_date", F.to_date("event_ts"))
        .groupBy("activity_date", "product_code", "application_status")
        .agg(
            F.count("*").alias("applications"),
            F.sum("requested_amount").alias("requested_amount"),
            F.avg("requested_amount").alias("average_requested_amount"),
        )
    )
