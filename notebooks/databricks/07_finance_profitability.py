# Databricks notebook source
# MAGIC %md
# MAGIC # Product profitability and finance mart

# COMMAND ----------
from pyspark.sql import functions as F

catalog = spark.conf.get("oakbridge.catalog", "main")
applications = spark.table(f"{catalog}.silver_lending.loan_application")
ach = spark.table(f"{catalog}.silver_treasury.ach_transaction")

# COMMAND ----------
loan_finance = (
    applications
    .groupBy("product_code")
    .agg(
        F.count("*").alias("application_count"),
        F.sum("requested_amount").alias("requested_amount"),
        F.avg("requested_amount").alias("average_request"),
        F.sum(F.when(F.col("application_status") == "FUNDED", F.col("requested_amount")).otherwise(F.lit(0))).alias("funded_amount")
    )
    .withColumn("estimated_origination_revenue", F.col("funded_amount") * F.lit(0.018))
    .withColumn("estimated_credit_cost", F.col("funded_amount") * F.lit(0.0065))
    .withColumn("estimated_net_contribution", F.col("estimated_origination_revenue") - F.col("estimated_credit_cost"))
    .withColumn("as_of_ts", F.current_timestamp())
)

# COMMAND ----------
treasury_finance = (
    ach.groupBy("direction", "transaction_status")
    .agg(
        F.count("*").alias("transaction_count"),
        F.sum("amount").alias("gross_amount")
    )
    .withColumn("estimated_processing_revenue", F.col("transaction_count") * F.lit(0.18))
    .withColumn("as_of_ts", F.current_timestamp())
)

# COMMAND ----------
loan_finance.write.mode("overwrite").format("delta").saveAsTable(
    f"{catalog}.gold_lending.product_profitability"
)
treasury_finance.write.mode("overwrite").format("delta").saveAsTable(
    f"{catalog}.gold_treasury.processing_economics"
)

display(loan_finance.orderBy(F.desc("estimated_net_contribution")))
display(treasury_finance.orderBy(F.desc("gross_amount")))
