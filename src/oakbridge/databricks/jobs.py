from __future__ import annotations

import os

from pyspark.sql import SparkSession, functions as F

from oakbridge.schemas.ach import ACH_EVENT_SCHEMA
from oakbridge.schemas.application import APPLICATION_EVENT_SCHEMA
from oakbridge.schemas.identity import IDENTITY_SCHEMA
from oakbridge.schemas.onboarding import BUSINESS_ONBOARDING_SCHEMA
from oakbridge.transforms.ach import normalize_ach
from oakbridge.transforms.application import normalize_application, with_application_dq
from oakbridge.transforms.identity import normalize_identity
from oakbridge.transforms.onboarding import normalize_onboarding


def _spark() -> SparkSession:
    return SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()


def _env(name: str, default: str) -> str:
    return os.getenv(name, default)


def _catalog() -> str:
    return _env("OAKBRIDGE_CATALOG", "oakbridge_dev")


def _stream_name(kind: str) -> str:
    defaults = {
        "application": "oakbridge-dev-us-east-1-lending-application-events-v1",
        "ach": "oakbridge-dev-us-east-1-treasury-ach-events-v1",
    }
    return _env(f"OAKBRIDGE_{kind.upper()}_STREAM", defaults[kind])


def _checkpoint(name: str) -> str:
    root = _env(
        "OAKBRIDGE_CHECKPOINT_ROOT",
        "s3://oakbridge-dev-stream-state-us-east-1/checkpoints",
    ).rstrip("/")
    return f"{root}/{name}"


def _landing(name: str) -> str:
    root = _env(
        "OAKBRIDGE_DATA_ROOT",
        "s3://oakbridge-dev-data-us-east-1",
    ).rstrip("/")
    return f"{root}/landing/{name}"


def _parse_kinesis(stream_name: str, schema):
    spark = _spark()
    raw = (
        spark.readStream
        .format("kinesis")
        .option("streamName", stream_name)
        .option("region", _env("AWS_REGION", "us-east-1"))
        .option("initialPosition", "LATEST")
        .load()
    )
    return (
        raw.select(
            F.from_json(F.col("data").cast("string"), schema).alias("record"),
            F.col("partitionKey").cast("string").alias("_partition_key"),
            F.col("sequenceNumber").cast("string").alias("_sequence_number"),
            F.col("approximateArrivalTimestamp").alias("_arrival_ts"),
        )
        .select("record.*", "_partition_key", "_sequence_number", "_arrival_ts")
    )


def application_main() -> None:
    spark = _spark()
    catalog = _catalog()
    parsed = _parse_kinesis(_stream_name("application"), APPLICATION_EVENT_SCHEMA)

    bronze_table = f"{catalog}.bronze_lending.loan_application_event_raw"
    quarantine_table = f"{catalog}.ops.application_event_quarantine"
    current_table = f"{catalog}.silver_lending.loan_application"
    history_table = f"{catalog}.silver_lending.loan_application_status_history"

    def persist(batch_df, batch_id):
        batch_df.write.mode("append").saveAsTable(bronze_table)
        checked = with_application_dq(batch_df)
        checked.filter(F.col("dq_reason").isNotNull()).write.mode("append").saveAsTable(
            quarantine_table
        )
        valid = normalize_application(
            checked.filter(F.col("dq_reason").isNull()).drop("dq_reason")
        ).dropDuplicates(["event_id"])
        valid.write.mode("append").saveAsTable(history_table)
        valid.createOrReplaceTempView("application_updates")
        spark.sql(
            f"""
            MERGE INTO {current_table} AS t
            USING application_updates AS s
              ON t.application_id = s.application_id
            WHEN MATCHED AND (
              s.event_version > t.event_version OR
              (s.event_version = t.event_version AND s.event_ts > t.event_ts)
            ) THEN UPDATE SET *
            WHEN NOT MATCHED THEN INSERT *
            """
        )

    (
        parsed.withWatermark("event_ts", "2 hours")
        .dropDuplicates(["event_id"])
        .writeStream.foreachBatch(persist)
        .option("checkpointLocation", _checkpoint("application_stream"))
        .trigger(processingTime="30 seconds")
        .start()
        .awaitTermination()
    )


def identity_main() -> None:
    spark = _spark()
    catalog = _catalog()
    schema_root = _env(
        "OAKBRIDGE_SCHEMA_ROOT",
        "s3://oakbridge-dev-stream-state-us-east-1/schemas",
    ).rstrip("/")
    df = (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", f"{schema_root}/identity")
        .schema(IDENTITY_SCHEMA)
        .load(_landing("identity_verification"))
        .transform(normalize_identity)
    )
    (
        df.writeStream.option("checkpointLocation", _checkpoint("identity"))
        .trigger(availableNow=True)
        .toTable(f"{catalog}.silver_risk.identity_verification")
        .awaitTermination()
    )


def onboarding_main() -> None:
    spark = _spark()
    catalog = _catalog()
    schema_root = _env(
        "OAKBRIDGE_SCHEMA_ROOT",
        "s3://oakbridge-dev-stream-state-us-east-1/schemas",
    ).rstrip("/")
    df = (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", f"{schema_root}/onboarding")
        .schema(BUSINESS_ONBOARDING_SCHEMA)
        .load(_landing("business_onboarding"))
        .withWatermark("event_ts", "2 hours")
        .dropDuplicates(["onboarding_event_id"])
        .transform(normalize_onboarding)
    )
    (
        df.writeStream.option("checkpointLocation", _checkpoint("onboarding"))
        .trigger(availableNow=True)
        .toTable(f"{catalog}.silver_customer.business_onboarding")
        .awaitTermination()
    )


def ach_main() -> None:
    catalog = _catalog()
    df = (
        _parse_kinesis(_stream_name("ach"), ACH_EVENT_SCHEMA)
        .withWatermark("event_ts", "2 hours")
        .dropDuplicates(["transaction_id"])
        .transform(normalize_ach)
    )
    (
        df.writeStream.option("checkpointLocation", _checkpoint("ach_stream"))
        .trigger(processingTime="30 seconds")
        .toTable(f"{catalog}.silver_treasury.ach_transaction")
        .awaitTermination()
    )


def gold_main() -> None:
    spark = _spark()
    catalog = _catalog()
    spark.sql(
        f"""
        CREATE OR REPLACE TABLE {catalog}.gold_lending.underwriting_readiness_queue AS
        SELECT
          a.*,
          i.verification_status AS identity_verification_status,
          (a.documents_complete
           AND a.financial_package_complete
           AND i.verification_status = 'VERIFIED') AS ready_for_underwriting
        FROM {catalog}.silver_lending.loan_application a
        LEFT JOIN {catalog}.silver_risk.identity_verification i
          ON a.application_id = i.application_id
        """
    )
    spark.sql(
        f"""
        CREATE OR REPLACE TABLE {catalog}.gold_treasury.activity_daily AS
        SELECT
          CAST(event_ts AS DATE) AS activity_date,
          business_id,
          direction,
          transaction_status,
          COUNT(*) AS transaction_count,
          SUM(amount) AS total_amount
        FROM {catalog}.silver_treasury.ach_transaction
        GROUP BY 1,2,3,4
        """
    )


def reconciliation_main() -> None:
    spark = _spark()
    catalog = _catalog()
    spark.sql(
        f"""
        CREATE OR REPLACE TABLE {catalog}.ops.pipeline_reconciliation AS
        SELECT
          current_timestamp() AS run_ts,
          (SELECT COUNT(*) FROM {catalog}.bronze_lending.loan_application_event_raw) AS bronze_count,
          (SELECT COUNT(*) FROM {catalog}.silver_lending.loan_application_status_history) AS history_count,
          (SELECT COUNT(*) FROM {catalog}.ops.application_event_quarantine) AS quarantine_count
        """
    )
