from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import dataclass
from typing import Callable

from delta import configure_spark_with_delta_pip
from delta.tables import DeltaTable
from pyspark.sql import DataFrame, SparkSession, Window, functions as F, types as T

LOGGER = logging.getLogger(__name__)


APPLICATION_SCHEMA = T.StructType([
    T.StructField("event_id", T.StringType(), False),
    T.StructField("event_type", T.StringType(), False),
    T.StructField("event_version", T.LongType(), False),
    T.StructField("event_ts", T.TimestampType(), False),
    T.StructField("application_id", T.StringType(), False),
    T.StructField("customer_id", T.StringType(), False),
    T.StructField("business_id", T.StringType(), False),
    T.StructField("product_code", T.StringType(), False),
    T.StructField("requested_amount", T.DecimalType(18, 2), True),
    T.StructField("use_of_funds", T.StringType(), True),
    T.StructField("application_status", T.StringType(), False),
    T.StructField("documents_complete", T.BooleanType(), False),
    T.StructField("financial_package_complete", T.BooleanType(), False),
    T.StructField("identity_verification_status", T.StringType(), True),
    T.StructField("source_system", T.StringType(), False),
    T.StructField("trace_id", T.StringType(), False),
])

ACH_SCHEMA = T.StructType([
    T.StructField("transaction_id", T.StringType(), False),
    T.StructField("event_ts", T.TimestampType(), False),
    T.StructField("account_id", T.StringType(), False),
    T.StructField("business_id", T.StringType(), False),
    T.StructField("direction", T.StringType(), False),
    T.StructField("amount", T.DecimalType(18, 2), False),
    T.StructField("sec_code", T.StringType(), False),
    T.StructField("transaction_status", T.StringType(), False),
    T.StructField("counterparty_token", T.StringType(), True),
    T.StructField("source_system", T.StringType(), False),
])


@dataclass(frozen=True)
class StreamSpec:
    name: str
    topic: str
    schema: T.StructType
    event_time_column: str
    delivery_key: str
    business_key: str
    watermark: str
    bronze_path: str
    quarantine_path: str
    silver_history_path: str
    silver_current_path: str
    checkpoint_root: str

    def checkpoint(self, stage: str) -> str:
        return f"{self.checkpoint_root.rstrip('/')}/{self.name}/{stage}/v1"


@dataclass(frozen=True)
class RuntimeConfig:
    kafka_bootstrap_servers: str
    s3_endpoint: str | None
    starting_offsets: str
    fail_on_data_loss: bool
    max_offsets_per_trigger: int | None
    trigger_seconds: int

    @classmethod
    def from_env(cls) -> "RuntimeConfig":
        limit = os.getenv("MAX_OFFSETS_PER_TRIGGER")
        return cls(
            kafka_bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "redpanda:9092"),
            s3_endpoint=os.getenv("S3_ENDPOINT"),
            starting_offsets=os.getenv("KAFKA_STARTING_OFFSETS", "earliest"),
            fail_on_data_loss=os.getenv("KAFKA_FAIL_ON_DATA_LOSS", "false").lower() == "true",
            max_offsets_per_trigger=int(limit) if limit else None,
            trigger_seconds=int(os.getenv("STREAM_TRIGGER_SECONDS", "5")),
        )


class StreamingRuntime:
    def __init__(self, spark: SparkSession, config: RuntimeConfig) -> None:
        self.spark = spark
        self.config = config

    def read_kafka(self, spec: StreamSpec) -> DataFrame:
        reader = (
            self.spark.readStream
            .format("kafka")
            .option("kafka.bootstrap.servers", self.config.kafka_bootstrap_servers)
            .option("subscribe", spec.topic)
            .option("startingOffsets", self.config.starting_offsets)
            .option("failOnDataLoss", str(self.config.fail_on_data_loss).lower())
        )
        if self.config.max_offsets_per_trigger:
            reader = reader.option("maxOffsetsPerTrigger", self.config.max_offsets_per_trigger)
        return reader.load()

    @staticmethod
    def parse_kafka(raw: DataFrame, spec: StreamSpec) -> DataFrame:
        parsed = F.from_json(F.col("value").cast("string"), spec.schema)
        return (
            raw.select(
                F.col("key").cast("string").alias("kafka_key"),
                parsed.alias("record"),
                "topic", "partition", "offset",
                F.col("timestamp").alias("kafka_timestamp"),
            )
            .select("record.*", "kafka_key", "topic", "partition", "offset", "kafka_timestamp")
            .withColumn("ingest_ts", F.current_timestamp())
            .withColumn("event_date", F.to_date(F.col(spec.event_time_column)))
        )

    @staticmethod
    def application_quality(df: DataFrame) -> DataFrame:
        statuses = [
            "SUBMITTED", "DOCUMENTS_PENDING", "REVIEW", "READY_FOR_UNDERWRITING",
            "UNDERWRITING", "DECISIONED", "FUNDED", "CANCELLED",
        ]
        return df.withColumn(
            "dq_reason",
            F.when(F.col("event_id").isNull() | (F.length(F.trim("event_id")) == 0), "MISSING_EVENT_ID")
            .when(F.col("application_id").isNull(), "MISSING_APPLICATION_ID")
            .when(F.col("event_version") <= 0, "INVALID_EVENT_VERSION")
            .when(~F.col("application_status").isin(statuses), "INVALID_APPLICATION_STATUS")
            .when(F.col("requested_amount") <= 0, "INVALID_REQUESTED_AMOUNT")
            .when(F.col("event_ts").isNull(), "MISSING_EVENT_TIME")
            .when(F.col("kafka_key") != F.col("application_id"), "PARTITION_KEY_MISMATCH")
        )

    @staticmethod
    def ach_quality(df: DataFrame) -> DataFrame:
        return df.withColumn(
            "dq_reason",
            F.when(F.col("transaction_id").isNull(), "MISSING_TRANSACTION_ID")
            .when(F.col("business_id").isNull(), "MISSING_BUSINESS_ID")
            .when(~F.col("direction").isin("CREDIT", "DEBIT"), "INVALID_DIRECTION")
            .when(~F.col("transaction_status").isin("PENDING", "POSTED", "RETURNED"), "INVALID_STATUS")
            .when(F.col("amount") <= 0, "INVALID_AMOUNT")
            .when(F.col("event_ts").isNull(), "MISSING_EVENT_TIME")
            .when(F.col("kafka_key") != F.col("business_id"), "PARTITION_KEY_MISMATCH")
        )

    @staticmethod
    def split_quality(df: DataFrame) -> tuple[DataFrame, DataFrame]:
        valid = df.filter(F.col("dq_reason").isNull()).drop("dq_reason")
        invalid = (
            df.filter(F.col("dq_reason").isNotNull())
            .withColumn("quarantined_at", F.current_timestamp())
            .withColumn("quarantine_record_id", F.sha2(F.concat_ws("|", F.coalesce(F.col("kafka_key"), F.lit("")), F.col("topic"), F.col("partition"), F.col("offset")), 256))
        )
        return valid, invalid

    @staticmethod
    def add_stream_semantics(df: DataFrame, spec: StreamSpec) -> DataFrame:
        return (
            df.withWatermark(spec.event_time_column, spec.watermark)
            .dropDuplicates([spec.delivery_key])
            .withColumn("processing_ts", F.current_timestamp())
        )

    def append_delta_stream(self, df: DataFrame, path: str, checkpoint: str, partition_by: str | None = None):
        writer = (
            df.writeStream
            .format("delta")
            .option("checkpointLocation", checkpoint)
            .outputMode("append")
            .trigger(processingTime=f"{self.config.trigger_seconds} seconds")
        )
        if partition_by:
            writer = writer.partitionBy(partition_by)
        return writer.option("path", path).start()

    @staticmethod
    def merge_latest_application(batch: DataFrame, target_path: str) -> None:
        if batch.rdd.isEmpty():
            return
        latest_window = Window.partitionBy("application_id").orderBy(
            F.col("event_version").desc(), F.col("event_ts").desc(), F.col("offset").desc()
        )
        latest = (
            batch.withColumn("_rn", F.row_number().over(latest_window))
            .filter(F.col("_rn") == 1).drop("_rn")
            .withColumn(
                "ready_for_underwriting",
                F.col("documents_complete")
                & F.col("financial_package_complete")
                & (F.coalesce(F.col("identity_verification_status"), F.lit("PENDING")) == "VERIFIED"),
            )
        )
        if not DeltaTable.isDeltaTable(batch.sparkSession, target_path):
            latest.write.format("delta").mode("overwrite").save(target_path)
            return
        target = DeltaTable.forPath(batch.sparkSession, target_path)
        assignments = {column: f"s.{column}" for column in latest.columns}
        (
            target.alias("t")
            .merge(latest.alias("s"), "t.application_id = s.application_id")
            .whenMatchedUpdate(
                condition="s.event_version > t.event_version OR (s.event_version = t.event_version AND s.event_ts >= t.event_ts)",
                set=assignments,
            )
            .whenNotMatchedInsert(values=assignments)
            .execute()
        )

    @staticmethod
    def merge_latest_ach(batch: DataFrame, target_path: str) -> None:
        if batch.rdd.isEmpty():
            return
        window = Window.partitionBy("transaction_id").orderBy(F.col("event_ts").desc(), F.col("offset").desc())
        latest = batch.withColumn("_rn", F.row_number().over(window)).filter("_rn = 1").drop("_rn")
        if not DeltaTable.isDeltaTable(batch.sparkSession, target_path):
            latest.write.format("delta").mode("overwrite").save(target_path)
            return
        target = DeltaTable.forPath(batch.sparkSession, target_path)
        assignments = {column: f"s.{column}" for column in latest.columns}
        (
            target.alias("t")
            .merge(latest.alias("s"), "t.transaction_id = s.transaction_id")
            .whenMatchedUpdate(condition="s.event_ts >= t.event_ts", set=assignments)
            .whenNotMatchedInsert(values=assignments)
            .execute()
        )

    def run_domain(
        self,
        spec: StreamSpec,
        quality_fn: Callable[[DataFrame], DataFrame],
        merge_fn: Callable[[DataFrame, str], None],
    ) -> list:
        raw = self.read_kafka(spec)
        parsed = self.parse_kafka(raw, spec)
        bronze_query = self.append_delta_stream(
            parsed, spec.bronze_path, spec.checkpoint("bronze"), partition_by="event_date"
        )
        checked = quality_fn(parsed)
        valid, invalid = self.split_quality(checked)
        quarantine_query = self.append_delta_stream(
            invalid, spec.quarantine_path, spec.checkpoint("quarantine"), partition_by="event_date"
        )
        canonical = self.add_stream_semantics(valid, spec)
        history_query = self.append_delta_stream(
            canonical, spec.silver_history_path, spec.checkpoint("history"), partition_by="event_date"
        )
        current_query = (
            canonical.writeStream
            .foreachBatch(lambda batch, _: merge_fn(batch, spec.silver_current_path))
            .option("checkpointLocation", spec.checkpoint("current"))
            .trigger(processingTime=f"{self.config.trigger_seconds} seconds")
            .start()
        )
        return [bronze_query, quarantine_query, history_query, current_query]


def build_spark(app_name: str, config: RuntimeConfig) -> SparkSession:
    builder = (
        SparkSession.builder.appName(app_name)
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.adaptive.skewJoin.enabled", "true")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.streaming.stateStore.providerClass", "org.apache.spark.sql.execution.streaming.state.RocksDBStateStoreProvider")
    )
    if config.s3_endpoint:
        builder = (
            builder.config("spark.hadoop.fs.s3a.endpoint", config.s3_endpoint)
            .config("spark.hadoop.fs.s3a.path.style.access", "true")
            .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
            .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
        )
    return configure_spark_with_delta_pip(builder).getOrCreate()


def application_spec() -> StreamSpec:
    return StreamSpec(
        name="lending_application",
        topic="lending.application-events.v1",
        schema=APPLICATION_SCHEMA,
        event_time_column="event_ts",
        delivery_key="event_id",
        business_key="application_id",
        watermark="2 hours",
        bronze_path="s3a://oakbridge-bronze/lending/application_event/",
        quarantine_path="s3a://oakbridge-quarantine/lending/application_event/",
        silver_history_path="s3a://oakbridge-silver/lending/loan_application_status_history/",
        silver_current_path="s3a://oakbridge-silver/lending/loan_application/",
        checkpoint_root="s3a://oakbridge-checkpoints",
    )


def ach_spec() -> StreamSpec:
    return StreamSpec(
        name="treasury_ach",
        topic="treasury.ach-events.v1",
        schema=ACH_SCHEMA,
        event_time_column="event_ts",
        delivery_key="transaction_id",
        business_key="business_id",
        watermark="2 hours",
        bronze_path="s3a://oakbridge-bronze/treasury/ach_event/",
        quarantine_path="s3a://oakbridge-quarantine/treasury/ach_event/",
        silver_history_path="s3a://oakbridge-silver/treasury/ach_transaction_history/",
        silver_current_path="s3a://oakbridge-silver/treasury/ach_transaction/",
        checkpoint_root="s3a://oakbridge-checkpoints",
    )


def query_snapshot(queries: list) -> list[dict]:
    rows = []
    for query in queries:
        progress = query.lastProgress or {}
        rows.append({
            "id": str(query.id),
            "name": query.name,
            "status": query.status,
            "is_active": query.isActive,
            "input_rows_per_second": progress.get("inputRowsPerSecond"),
            "processed_rows_per_second": progress.get("processedRowsPerSecond"),
            "batch_id": progress.get("batchId"),
            "duration_ms": progress.get("durationMs"),
            "state_operators": progress.get("stateOperators"),
            "sources": progress.get("sources"),
            "sink": progress.get("sink"),
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", choices=["lending", "treasury", "all"], default="all")
    args = parser.parse_args()
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    config = RuntimeConfig.from_env()
    spark = build_spark("oakbridge-principal-streaming-runtime", config)
    runtime = StreamingRuntime(spark, config)
    queries = []
    if args.domain in {"lending", "all"}:
        queries += runtime.run_domain(application_spec(), runtime.application_quality, runtime.merge_latest_application)
    if args.domain in {"treasury", "all"}:
        queries += runtime.run_domain(ach_spec(), runtime.ach_quality, runtime.merge_latest_ach)
    LOGGER.info("started streaming queries: %s", json.dumps(query_snapshot(queries), default=str))
    spark.streams.awaitAnyTermination()


if __name__ == "__main__":
    main()
