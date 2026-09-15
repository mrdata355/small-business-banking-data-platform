from pyspark import pipelines as dp
from pyspark.sql import Window, functions as F

CATALOG = spark.conf.get("oakbridge.catalog", "main")
BRONZE = CATALOG + ".bronze_lending.loan_application_event_valid"

@dp.table(name="loan_application_status_history", comment="Canonical lending event history")
@dp.expect_or_drop("non_null_application_id", "application_id IS NOT NULL")
@dp.expect_or_drop("non_null_event_time", "event_ts IS NOT NULL")
def loan_application_status_history():
    return (
        spark.readStream.table(BRONZE)
        .withWatermark("event_ts", "2 hours")
        .dropDuplicates(["event_id"])
        .withColumn("application_status", F.upper(F.trim("application_status")))
        .withColumn("product_code", F.upper(F.trim("product_code")))
        .withColumn("processed_ts", F.current_timestamp())
    )

@dp.materialized_view(name="loan_application", comment="Authoritative current application state")
def loan_application():
    history = spark.read.table("loan_application_status_history")
    w = Window.partitionBy("application_id").orderBy(
        F.col("event_version").desc(),
        F.col("event_ts").desc(),
        F.col("ingest_ts").desc(),
    )
    return (
        history.withColumn("_rn", F.row_number().over(w))
        .filter(F.col("_rn") == 1)
        .drop("_rn")
        .withColumn("ready_for_underwriting", F.col("documents_complete") & F.col("financial_package_complete"))
    )

@dp.materialized_view(name="application_funnel_snapshot", comment="Operational application funnel snapshot")
def application_funnel_snapshot():
    return (
        spark.read.table("loan_application")
        .groupBy("product_code", "application_status")
        .agg(
            F.count("*").alias("application_count"),
            F.sum("requested_amount").alias("requested_amount_total"),
            F.max("event_ts").alias("latest_event_ts"),
        )
    )
