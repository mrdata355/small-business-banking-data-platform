# Databricks notebook source
# MAGIC %md
# MAGIC # Platform health and data-product coverage

# COMMAND ----------
from pyspark.sql import functions as F

catalog = spark.conf.get("oakbridge.catalog", "main")

assets = [
    ("silver_lending.loan_application", "lending", "silver"),
    ("silver_risk.identity_verification", "risk", "silver"),
    ("silver_treasury.ach_transaction", "treasury", "silver"),
    ("gold_lending.underwriting_readiness_queue", "lending", "gold"),
    ("gold_lending.product_profitability", "finance", "gold"),
    ("gold_treasury.processing_economics", "finance", "gold"),
    ("feature_store.application_operational_risk_features", "data_science", "feature"),
    ("feature_store.ach_behavior_features", "data_science", "feature"),
    ("ops.application_reconciliation_snapshot", "platform", "ops"),
    ("ops.model_monitoring_snapshot", "mlops", "ops"),
]

rows = []
for name, domain, layer in assets:
    fq = f"{catalog}.{name}"
    exists = spark.catalog.tableExists(fq)
    row_count = spark.table(fq).count() if exists else 0
    rows.append((fq, domain, layer, exists, row_count))

health = spark.createDataFrame(rows, "asset string, domain string, layer string, exists boolean, row_count long")
health = (
    health
    .withColumn("status", F.when(F.col("exists") & (F.col("row_count") > 0), "HEALTHY").otherwise("MISSING_OR_EMPTY"))
    .withColumn("observed_at", F.current_timestamp())
)

# COMMAND ----------
health.write.mode("append").format("delta").saveAsTable(f"{catalog}.ops.platform_asset_health")
display(health.orderBy("domain", "layer", "asset"))
