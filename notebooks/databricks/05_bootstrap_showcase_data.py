# Databricks notebook source
# MAGIC %md
# MAGIC # Development data bootstrap
# MAGIC Generates synthetic banking-domain records for the development catalog.

# COMMAND ----------
from pyspark.sql import functions as F

catalog = spark.conf.get("oakbridge.catalog", "main")

schemas = [
    "bronze_lending", "bronze_treasury", "silver_lending", "silver_treasury",
    "silver_customer", "silver_risk", "gold_lending", "gold_treasury", "ops",
    "feature_store"
]
for schema in schemas:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")

# COMMAND ----------
application_count = 100_000
applications = (
    spark.range(application_count)
    .select(
        F.concat(F.lit("APP-DEV-"), F.lpad(F.col("id"), 10, "0")).alias("application_id"),
        F.concat(F.lit("CUST-DEV-"), F.lpad((F.col("id") % 50_000), 9, "0")).alias("customer_id"),
        F.concat(F.lit("BIZ-DEV-"), F.lpad((F.col("id") % 30_000), 9, "0")).alias("business_id"),
        F.when((F.col("id") % 4) == 0, "SBA_7A")
         .when((F.col("id") % 4) == 1, "USDA")
         .when((F.col("id") % 4) == 2, "CONVENTIONAL")
         .otherwise("CUSTOM").alias("product_code"),
        (F.lit(50_000) + (F.col("id") % 950_000)).cast("decimal(18,2)").alias("requested_amount"),
        F.when((F.col("id") % 5) == 0, "ACQUISITION")
         .when((F.col("id") % 5) == 1, "WORKING_CAPITAL")
         .when((F.col("id") % 5) == 2, "EQUIPMENT")
         .when((F.col("id") % 5) == 3, "CRE")
         .otherwise("REFINANCE").alias("use_of_funds"),
        F.when((F.col("id") % 6) == 0, "SUBMITTED")
         .when((F.col("id") % 6) == 1, "DOCUMENTS_PENDING")
         .when((F.col("id") % 6) == 2, "REVIEW")
         .when((F.col("id") % 6) == 3, "READY_FOR_UNDERWRITING")
         .when((F.col("id") % 6) == 4, "DECISIONED")
         .otherwise("FUNDED").alias("application_status"),
        ((F.col("id") % 3) != 0).alias("documents_complete"),
        ((F.col("id") % 4) != 0).alias("financial_package_complete"),
        (F.col("id") + 1).cast("long").alias("event_version"),
        F.current_timestamp().alias("event_ts"),
        F.lit("development_generator").alias("source_system"),
        F.concat(F.lit("trace-dev-"), F.col("id")).alias("trace_id")
    )
)
applications.write.mode("overwrite").format("delta").saveAsTable(
    f"{catalog}.silver_lending.loan_application"
)

# COMMAND ----------
ach_count = 250_000
ach = (
    spark.range(ach_count)
    .select(
        F.concat(F.lit("ACH-DEV-"), F.lpad(F.col("id"), 12, "0")).alias("transaction_id"),
        F.current_timestamp().alias("event_ts"),
        F.concat(F.lit("ACCT-"), F.lpad((F.col("id") % 40_000), 9, "0")).alias("account_id"),
        F.concat(F.lit("BIZ-DEV-"), F.lpad((F.col("id") % 30_000), 9, "0")).alias("business_id"),
        F.when((F.col("id") % 2) == 0, "CREDIT").otherwise("DEBIT").alias("direction"),
        (F.lit(25) + (F.col("id") % 100_000) / F.lit(10)).cast("decimal(18,2)").alias("amount"),
        F.when((F.col("id") % 3) == 0, "CCD").when((F.col("id") % 3) == 1, "PPD").otherwise("WEB").alias("sec_code"),
        F.when((F.col("id") % 20) == 0, "RETURNED").otherwise("POSTED").alias("transaction_status"),
        F.sha2(F.concat(F.lit("counterparty-"), F.col("id")), 256).alias("counterparty_token"),
        F.lit("development_generator").alias("source_system")
    )
)
ach.write.mode("overwrite").format("delta").saveAsTable(
    f"{catalog}.silver_treasury.ach_transaction"
)

# COMMAND ----------
identity = (
    applications.select("application_id", "customer_id")
    .withColumn("verification_status", F.when((F.xxhash64("application_id") % 10) == 0, "REVIEW").otherwise("VERIFIED"))
    .withColumn("verification_ts", F.current_timestamp())
    .withColumn("vendor_file_id", F.lit("DEV-IDENTITY-GENERATOR"))
)
identity.write.mode("overwrite").format("delta").saveAsTable(
    f"{catalog}.silver_risk.identity_verification"
)

# COMMAND ----------
print({
    "catalog": catalog,
    "applications": spark.table(f"{catalog}.silver_lending.loan_application").count(),
    "ach_transactions": spark.table(f"{catalog}.silver_treasury.ach_transaction").count(),
    "identity_records": spark.table(f"{catalog}.silver_risk.identity_verification").count(),
})
