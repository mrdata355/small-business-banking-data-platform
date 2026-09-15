from pyspark import pipelines as dp
from pyspark.sql import functions as F

@dp.table(name="ach_event_raw", comment="Generated ACH event stream")
def ach_event_raw():
    src = spark.readStream.format("rate").option("rowsPerSecond", "10").load()
    return src.select(
        F.concat(F.lit("ACH-"), F.lpad(F.col("value").cast("string"), 14, "0")).alias("transaction_id"),
        F.col("timestamp").alias("event_ts"),
        F.concat(F.lit("ACCT-"), (F.col("value") % 12000).cast("string")).alias("account_id"),
        F.concat(F.lit("BIZ-"), (F.col("value") % 2000).cast("string")).alias("business_id"),
        F.when((F.col("value") % 2) == 0, "CREDIT").otherwise("DEBIT").alias("direction"),
        (F.lit(25) + (F.col("value") % 25000)).cast("decimal(18,2)").alias("amount"),
        F.when((F.col("value") % 3) == 0, "CCD").when((F.col("value") % 3) == 1, "PPD").otherwise("WEB").alias("sec_code"),
        F.when((F.col("value") % 23) == 0, "RETURNED").otherwise("POSTED").alias("transaction_status"),
        F.concat(F.lit("counterparty-"), (F.col("value") % 5000).cast("string")).alias("counterparty_token"),
        F.lit("databricks_demo_stream").alias("source_system"),
        F.current_timestamp().alias("ingest_ts"),
    )

@dp.table(name="ach_event_valid", comment="Validated ACH event stream")
@dp.expect_or_drop("positive_amount", "amount > 0")
@dp.expect_or_drop("known_direction", "direction IN ('CREDIT','DEBIT')")
def ach_event_valid():
    return spark.readStream.table("ach_event_raw")
