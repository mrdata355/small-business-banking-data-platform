# Databricks notebook source
# MAGIC %md
# MAGIC # Management and shareholder KPI snapshot

# COMMAND ----------
from pyspark.sql import functions as F

catalog = spark.conf.get("oakbridge.catalog", "main")
applications = spark.table(f"{catalog}.silver_lending.loan_application")
ach = spark.table(f"{catalog}.silver_treasury.ach_transaction")

# COMMAND ----------
lending = applications.agg(
    F.countDistinct("application_id").alias("applications"),
    F.sum("requested_amount").alias("requested_amount"),
    F.sum(F.when(F.col("application_status") == "FUNDED", F.col("requested_amount")).otherwise(F.lit(0))).alias("funded_amount"),
    F.sum(F.when(F.col("application_status") == "FUNDED", 1).otherwise(0)).alias("funded_applications")
)

treasury = ach.agg(
    F.countDistinct("transaction_id").alias("ach_transactions"),
    F.sum("amount").alias("ach_gross_amount"),
    F.sum(F.when(F.col("transaction_status") == "RETURNED", 1).otherwise(0)).alias("ach_returns")
)

snapshot = (
    lending.crossJoin(treasury)
    .withColumn("funding_rate", F.col("funded_applications") / F.greatest(F.col("applications"), F.lit(1)))
    .withColumn("ach_return_rate", F.col("ach_returns") / F.greatest(F.col("ach_transactions"), F.lit(1)))
    .withColumn("estimated_lending_revenue", F.col("funded_amount") * F.lit(0.018))
    .withColumn("estimated_treasury_revenue", F.col("ach_transactions") * F.lit(0.18))
    .withColumn("estimated_total_revenue", F.col("estimated_lending_revenue") + F.col("estimated_treasury_revenue"))
    .withColumn("as_of_ts", F.current_timestamp())
)

# COMMAND ----------
snapshot.write.mode("append").format("delta").saveAsTable(
    f"{catalog}.gold_lending.management_kpi_snapshot"
)

display(snapshot)
