# Databricks notebook source
# COMMAND ----------
# Structured Streaming monitoring for deployed jobs.
from pyspark.sql import functions as F

# COMMAND ----------
for query in spark.streams.active:
    print("name:", query.name)
    print("id:", query.id)
    print("status:", query.status)
    print("lastProgress:", query.lastProgress)

# COMMAND ----------
# Inspect recent data-quality results when the ops schema is deployed.
import os
catalog = os.getenv("OAKBRIDGE_CATALOG", "oakbridge_dev")

if spark.catalog.tableExists(f"{catalog}.ops.data_quality_result"):
    display(
        spark.table(f"{catalog}.ops.data_quality_result")
        .orderBy(F.col("evaluated_at").desc())
        .limit(100)
    )

# COMMAND ----------
if spark.catalog.tableExists(f"{catalog}.ops.pipeline_reconciliation"):
    display(
        spark.table(f"{catalog}.ops.pipeline_reconciliation")
        .orderBy(F.col("run_ts").desc())
        .limit(100)
    )
