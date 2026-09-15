# Databricks notebook source
# MAGIC %md
# MAGIC # Reconciliation control tower

# COMMAND ----------
from pyspark.sql import functions as F

catalog = spark.conf.get("oakbridge.catalog", "main")

application = spark.table(f"{catalog}.silver_lending.loan_application")
identity = spark.table(f"{catalog}.silver_risk.identity_verification")
ach = spark.table(f"{catalog}.silver_treasury.ach_transaction")

# COMMAND ----------
application_recon = (
    application.agg(
        F.count("*").alias("application_rows"),
        F.countDistinct("application_id").alias("distinct_applications"),
        F.sum(F.when(F.col("application_id").isNull(), 1).otherwise(0)).alias("null_application_keys"),
        F.sum("requested_amount").alias("requested_amount_total")
    )
    .withColumn("run_ts", F.current_timestamp())
    .withColumn("domain", F.lit("lending"))
)

identity_recon = (
    identity.agg(
        F.count("*").alias("identity_rows"),
        F.countDistinct("application_id").alias("identity_applications"),
        F.sum(F.when(F.col("verification_status") == "REVIEW", 1).otherwise(0)).alias("manual_review_count")
    )
    .withColumn("run_ts", F.current_timestamp())
)

ach_recon = (
    ach.agg(
        F.count("*").alias("transaction_rows"),
        F.countDistinct("transaction_id").alias("distinct_transactions"),
        F.sum("amount").alias("gross_transaction_amount"),
        F.sum(F.when(F.col("transaction_status") == "RETURNED", 1).otherwise(0)).alias("returned_count")
    )
    .withColumn("run_ts", F.current_timestamp())
)

# COMMAND ----------
application_recon.write.mode("append").format("delta").saveAsTable(
    f"{catalog}.ops.application_reconciliation_snapshot"
)
identity_recon.write.mode("append").format("delta").saveAsTable(
    f"{catalog}.ops.identity_reconciliation_snapshot"
)
ach_recon.write.mode("append").format("delta").saveAsTable(
    f"{catalog}.ops.ach_reconciliation_snapshot"
)

# COMMAND ----------
display(application_recon)
display(identity_recon)
display(ach_recon)
