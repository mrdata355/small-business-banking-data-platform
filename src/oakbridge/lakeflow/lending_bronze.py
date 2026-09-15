from pyspark import pipelines as dp
from pyspark.sql import functions as F


@dp.table(
    name="loan_application_event_raw",
    comment="Synthetic live lending application event stream used as the Bronze replay boundary.",
    table_properties={"quality": "bronze", "domain": "lending"},
)
@dp.expect("valid_event_id", "event_id IS NOT NULL")
@dp.expect("valid_application_id", "application_id IS NOT NULL")
def loan_application_event_raw():
    rate = (
        spark.readStream.format("rate")
        .option("rowsPerSecond", spark.conf.get("oakbridge.demo.lending_rps", "5"))
        .option("numPartitions", "2")
        .load()
    )
    return (
        rate.select(
            F.concat(F.lit("EVT-"), F.lpad(F.col("value").cast("string"), 12, "0")).alias("event_id"),
            F.when((F.col("value") % 4) == 0, F.lit("LoanApplicationSubmitted"))
            .when((F.col("value") % 4) == 1, F.lit("DocumentReceived"))
            .when((F.col("value") % 4) == 2, F.lit("FinancialPackageReceived"))
            .otherwise(F.lit("ApplicationStatusChanged"))
            .alias("event_type"),
            (F.col("value") % 6 + 1).cast("long").alias("event_version"),
            F.col("timestamp").alias("event_ts"),
            F.concat(F.lit("APP-"), F.lpad((F.col("value") % 5000).cast("string"), 8, "0")).alias("application_id"),
            F.concat(F.lit("CUST-"), F.lpad((F.col("value") % 3500).cast("string"), 8, "0")).alias("customer_id"),
            F.concat(F.lit("BIZ-"), F.lpad((F.col("value") % 2000).cast("string"), 8, "0")).alias("business_id"),
            F.when((F.col("value") % 3) == 0, F.lit("SBA_7A"))
            .when((F.col("value") % 3) == 1, F.lit("USDA_BI"))
            .otherwise(F.lit("CONVENTIONAL"))
            .alias("product_code"),
            (F.lit(100000) + (F.col("value") % 2500) * F.lit(1000)).cast("decimal(18,2)").alias("requested_amount"),
            F.when((F.col("value") % 3) == 0, F.lit("WORKING_CAPITAL"))
            .when((F.col("value") % 3) == 1, F.lit("ACQUISITION"))
            .otherwise(F.lit("EQUIPMENT"))
            .alias("use_of_funds"),
            F.when((F.col("value") % 6) <= 1, F.lit("SUBMITTED"))
            .when((F.col("value") % 6) <= 3, F.lit("DOCUMENTS_PENDING"))
            .otherwise(F.lit("REVIEW"))
            .alias("application_status"),
            ((F.col("value") % 6) >= 2).alias("documents_complete"),
            ((F.col("value") % 6) >= 4).alias("financial_package_complete"),
            F.lit("databricks_demo_stream").alias("source_system"),
            F.concat(F.lit("trace-"), F.sha2(F.col("value").cast("string"), 256)).alias("trace_id"),
            F.current_timestamp().alias("ingest_ts"),
        )
    )


@dp.table(
    name="loan_application_event_valid",
    comment="Validated Bronze lending events that passed core structural rules.",
    table_properties={"quality": "bronze_validated", "domain": "lending"},
)
@dp.expect_or_drop("positive_event_version", "event_version > 0")
@dp.expect_or_drop(
    "known_status",
    "application_status IN ('SUBMITTED','DOCUMENTS_PENDING','REVIEW','READY_FOR_UNDERWRITING','DECISIONED','FUNDED')",
)
def loan_application_event_valid():
    return spark.readStream.table("loan_application_event_raw")
