# Databricks notebook source
# MAGIC %md
# MAGIC # Feature engineering

# COMMAND ----------
from pyspark.sql import functions as F

catalog = spark.conf.get("oakbridge.catalog", "main")
applications = spark.table(f"{catalog}.silver_lending.loan_application")
identity = spark.table(f"{catalog}.silver_risk.identity_verification")
ach = spark.table(f"{catalog}.silver_treasury.ach_transaction")

# COMMAND ----------
ach_features = (
    ach.groupBy("business_id")
    .agg(
        F.count("*").alias("ach_txn_count"),
        F.sum("amount").alias("ach_gross_amount"),
        F.avg("amount").alias("ach_avg_amount"),
        F.max("amount").alias("ach_max_amount"),
        F.sum(F.when(F.col("transaction_status") == "RETURNED", 1).otherwise(0)).alias("ach_return_count"),
        F.sum(F.when(F.col("direction") == "DEBIT", F.col("amount")).otherwise(F.lit(0))).alias("ach_debit_amount"),
        F.sum(F.when(F.col("direction") == "CREDIT", F.col("amount")).otherwise(F.lit(0))).alias("ach_credit_amount")
    )
    .withColumn("ach_return_rate", F.col("ach_return_count") / F.greatest(F.col("ach_txn_count"), F.lit(1)))
)

application_features = (
    applications.alias("a")
    .join(identity.select("application_id", "verification_status").alias("i"), "application_id", "left")
    .join(ach_features.alias("t"), "business_id", "left")
    .select(
        "application_id", "customer_id", "business_id", "product_code",
        F.col("requested_amount").cast("double").alias("requested_amount"),
        F.col("documents_complete").cast("int").alias("documents_complete"),
        F.col("financial_package_complete").cast("int").alias("financial_package_complete"),
        F.when(F.col("verification_status") == "VERIFIED", 1).otherwise(0).alias("identity_verified"),
        F.coalesce("ach_txn_count", F.lit(0)).alias("ach_txn_count"),
        F.coalesce("ach_gross_amount", F.lit(0)).cast("double").alias("ach_gross_amount"),
        F.coalesce("ach_avg_amount", F.lit(0)).cast("double").alias("ach_avg_amount"),
        F.coalesce("ach_return_rate", F.lit(0.0)).alias("ach_return_rate"),
        F.current_timestamp().alias("feature_ts")
    )
    .withColumn(
        "operational_risk_score",
        F.least(
            F.lit(1.0),
            F.lit(0.20)
            + (F.lit(1) - F.col("identity_verified")) * F.lit(0.25)
            + (F.lit(1) - F.col("documents_complete")) * F.lit(0.15)
            + (F.lit(1) - F.col("financial_package_complete")) * F.lit(0.15)
            + F.col("ach_return_rate") * F.lit(0.25)
        )
    )
)

# COMMAND ----------
application_features.write.mode("overwrite").format("delta").saveAsTable(
    f"{catalog}.feature_store.application_operational_risk_features"
)
ach_features.write.mode("overwrite").format("delta").saveAsTable(
    f"{catalog}.feature_store.ach_behavior_features"
)

display(application_features.orderBy(F.desc("operational_risk_score")).limit(100))
