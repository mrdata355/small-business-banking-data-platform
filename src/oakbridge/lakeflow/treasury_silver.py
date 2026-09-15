from pyspark import pipelines as dp
from pyspark.sql import functions as F

CATALOG = spark.conf.get("oakbridge.catalog", "main")
BRONZE = CATALOG + ".bronze_treasury.ach_event_valid"

@dp.table(name="ach_transaction", comment="Canonical ACH transaction stream")
@dp.expect_or_drop("positive_amount", "amount > 0")
def ach_transaction():
    return (
        spark.readStream.table(BRONZE)
        .withWatermark("event_ts", "2 hours")
        .dropDuplicates(["transaction_id"])
        .withColumn("direction", F.upper(F.trim("direction")))
        .withColumn("sec_code", F.upper(F.trim("sec_code")))
        .withColumn("transaction_status", F.upper(F.trim("transaction_status")))
        .withColumn("processed_ts", F.current_timestamp())
    )

@dp.materialized_view(name="treasury_activity_snapshot", comment="Current treasury activity summary")
def treasury_activity_snapshot():
    return (
        spark.read.table("ach_transaction")
        .withColumn("activity_date", F.to_date("event_ts"))
        .groupBy("activity_date", "business_id", "direction", "transaction_status")
        .agg(
            F.count("*").alias("transaction_count"),
            F.sum("amount").alias("total_amount"),
            F.max("amount").alias("max_amount"),
            F.max("event_ts").alias("latest_event_ts"),
        )
    )
