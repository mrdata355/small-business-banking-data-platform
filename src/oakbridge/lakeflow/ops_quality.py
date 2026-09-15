from pyspark import pipelines as dp
from pyspark.sql import functions as F

CATALOG = spark.conf.get("oakbridge.catalog", "main")
LENDING = CATALOG + ".silver_lending.loan_application"
TREASURY = CATALOG + ".silver_treasury.ach_transaction"

@dp.materialized_view(name="pipeline_health", comment="Operational health summary across lending and treasury domains")
def pipeline_health():
    lending = (
        spark.read.table(LENDING)
        .agg(
            F.count("*").alias("row_count"),
            F.max("event_ts").alias("latest_event_ts"),
            F.sum(F.when(F.col("ready_for_underwriting"), 1).otherwise(0)).alias("ready_count"),
        )
        .withColumn("domain", F.lit("lending"))
    )
    treasury = (
        spark.read.table(TREASURY)
        .agg(
            F.count("*").alias("row_count"),
            F.max("event_ts").alias("latest_event_ts"),
            F.sum(F.when(F.col("transaction_status") == "RETURNED", 1).otherwise(0)).alias("ready_count"),
        )
        .withColumn("domain", F.lit("treasury"))
    )
    return lending.unionByName(treasury).withColumn("observed_at", F.current_timestamp())

@dp.materialized_view(name="data_quality_result", comment="Cross-domain deterministic quality metrics")
def data_quality_result():
    lending = spark.read.table(LENDING)
    treasury = spark.read.table(TREASURY)
    lending_metrics = lending.agg(
        F.count("*").alias("rows"),
        F.sum(F.when(F.col("application_id").isNull(), 1).otherwise(0)).alias("violations"),
    ).withColumn("check_name", F.lit("lending_application_id_not_null"))
    treasury_metrics = treasury.agg(
        F.count("*").alias("rows"),
        F.sum(F.when(F.col("amount") <= 0, 1).otherwise(0)).alias("violations"),
    ).withColumn("check_name", F.lit("treasury_amount_positive"))
    return (
        lending_metrics.unionByName(treasury_metrics)
        .withColumn("passed", F.col("violations") == 0)
        .withColumn("run_ts", F.current_timestamp())
    )
