# Databricks notebook source
# COMMAND ----------
# Lakehouse table inspection. Application logic remains in the packaged Python project.
import os

catalog = os.getenv("OAKBRIDGE_CATALOG", "oakbridge_dev")

# COMMAND ----------
display(spark.sql(f"SHOW SCHEMAS IN {catalog}"))

# COMMAND ----------
tables = [
    f"{catalog}.bronze_lending.loan_application_event_raw",
    f"{catalog}.silver_lending.loan_application_status_history",
    f"{catalog}.silver_lending.loan_application",
    f"{catalog}.gold_lending.underwriting_readiness_queue",
    f"{catalog}.ops.data_quality_result",
]

for table in tables:
    print(f"\n--- {table} ---")
    spark.sql(f"DESCRIBE DETAIL {table}").show(truncate=False)
    spark.table(table).limit(20).show(truncate=False)
