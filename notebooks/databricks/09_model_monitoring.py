# Databricks notebook source
# MAGIC %md
# MAGIC # Model monitoring

# COMMAND ----------
from pyspark.sql import functions as F

catalog = spark.conf.get("oakbridge.catalog", "main")
features = spark.table(f"{catalog}.feature_store.application_operational_risk_features")

# COMMAND ----------
monitoring = (
    features.agg(
        F.count("*").alias("feature_rows"),
        F.avg("operational_risk_score").alias("mean_risk_score"),
        F.expr("percentile_approx(operational_risk_score, 0.50)").alias("p50_risk_score"),
        F.expr("percentile_approx(operational_risk_score, 0.95)").alias("p95_risk_score"),
        F.sum(F.when(F.col("operational_risk_score") >= 0.70, 1).otherwise(0)).alias("high_risk_count"),
        F.sum(F.when(F.col("identity_verified") == 0, 1).otherwise(0)).alias("unverified_identity_count"),
        F.avg("ach_return_rate").alias("mean_ach_return_rate")
    )
    .withColumn("high_risk_rate", F.col("high_risk_count") / F.greatest(F.col("feature_rows"), F.lit(1)))
    .withColumn(
        "monitor_status",
        F.when(F.col("high_risk_rate") > 0.35, "ALERT")
         .when(F.col("high_risk_rate") > 0.20, "REVIEW")
         .otherwise("PASS")
    )
    .withColumn("run_ts", F.current_timestamp())
)

# COMMAND ----------
monitoring.write.mode("append").format("delta").saveAsTable(
    f"{catalog}.ops.model_monitoring_snapshot"
)

display(monitoring)
