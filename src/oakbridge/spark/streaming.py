from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from pyspark.sql import DataFrame, SparkSession, functions as F, types as T
from pyspark.sql.streaming import StreamingQuery


@dataclass(frozen=True)
class KafkaSourceConfig:
    bootstrap_servers: str
    topic: str
    starting_offsets: str = "latest"
    fail_on_data_loss: bool = False
    max_offsets_per_trigger: int | None = None


@dataclass(frozen=True)
class StreamPolicy:
    event_time_column: str
    watermark: str
    dedupe_keys: tuple[str, ...]
    checkpoint_location: str
    query_name: str
    trigger_interval: str = "5 seconds"


@dataclass(frozen=True)
class ParsedStream:
    valid: DataFrame
    malformed: DataFrame
    source_envelope: DataFrame


def kafka_source(spark: SparkSession, config: KafkaSourceConfig) -> DataFrame:
    reader = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", config.bootstrap_servers)
        .option("subscribe", config.topic)
        .option("startingOffsets", config.starting_offsets)
        .option("failOnDataLoss", str(config.fail_on_data_loss).lower())
    )
    if config.max_offsets_per_trigger is not None:
        reader = reader.option("maxOffsetsPerTrigger", config.max_offsets_per_trigger)
    return reader.load()


def parse_json_envelope(raw: DataFrame, schema: T.StructType) -> ParsedStream:
    envelope = raw.select(
        F.col("key").cast("string").alias("kafka_key"),
        F.col("value").cast("string").alias("raw_json"),
        F.col("topic"),
        F.col("partition").alias("kafka_partition"),
        F.col("offset").alias("kafka_offset"),
        F.col("timestamp").alias("kafka_timestamp"),
    ).withColumn(
        "record",
        F.from_json(
            "raw_json",
            schema,
            {"mode": "PERMISSIVE", "columnNameOfCorruptRecord": "_corrupt_record"},
        ),
    )

    valid = envelope.filter(F.col("record").isNotNull()).select(
        "kafka_key",
        "topic",
        "kafka_partition",
        "kafka_offset",
        "kafka_timestamp",
        "raw_json",
        "record.*",
    )
    malformed = envelope.filter(F.col("record").isNull()).select(
        "kafka_key",
        "topic",
        "kafka_partition",
        "kafka_offset",
        "kafka_timestamp",
        "raw_json",
    )
    return ParsedStream(valid=valid, malformed=malformed, source_envelope=envelope)


def apply_event_time_policy(df: DataFrame, policy: StreamPolicy) -> DataFrame:
    if not policy.dedupe_keys:
        raise ValueError("at least one stable dedupe key is required")
    missing = [column for column in (policy.event_time_column, *policy.dedupe_keys) if column not in df.columns]
    if missing:
        raise ValueError(f"stream is missing required columns: {missing}")
    return df.withWatermark(policy.event_time_column, policy.watermark).dropDuplicates(
        list(policy.dedupe_keys)
    )


def with_operational_metadata(df: DataFrame, pipeline_name: str) -> DataFrame:
    return (
        df.withColumn("_pipeline_name", F.lit(pipeline_name))
        .withColumn("_processed_at", F.current_timestamp())
        .withColumn("_source_partition", F.col("kafka_partition"))
        .withColumn("_source_offset", F.col("kafka_offset"))
    )


def write_foreach_batch(
    df: DataFrame,
    policy: StreamPolicy,
    handler: Callable[[DataFrame, int], None],
) -> StreamingQuery:
    return (
        df.writeStream.queryName(policy.query_name)
        .foreachBatch(handler)
        .option("checkpointLocation", policy.checkpoint_location)
        .trigger(processingTime=policy.trigger_interval)
        .start()
    )


def write_append(
    df: DataFrame,
    policy: StreamPolicy,
    format_name: str,
    output_path: str,
    partition_by: tuple[str, ...] = (),
) -> StreamingQuery:
    writer = (
        df.writeStream.queryName(policy.query_name)
        .format(format_name)
        .outputMode("append")
        .option("path", output_path)
        .option("checkpointLocation", policy.checkpoint_location)
        .trigger(processingTime=policy.trigger_interval)
    )
    if partition_by:
        writer = writer.partitionBy(*partition_by)
    return writer.start()


def stream_progress_snapshot(query: StreamingQuery) -> dict:
    progress = query.lastProgress or {}
    sources = progress.get("sources", [])
    source = sources[0] if sources else {}
    state = progress.get("stateOperators", [])
    state_rows = sum(int(item.get("numRowsTotal", 0)) for item in state)
    duration = progress.get("durationMs", {})
    return {
        "query_name": query.name,
        "query_id": str(query.id),
        "run_id": str(query.runId),
        "status": query.status,
        "input_rows_per_second": float(progress.get("inputRowsPerSecond", 0) or 0),
        "processed_rows_per_second": float(progress.get("processedRowsPerSecond", 0) or 0),
        "num_input_rows": int(progress.get("numInputRows", 0) or 0),
        "batch_id": progress.get("batchId"),
        "batch_duration_ms": int(duration.get("triggerExecution", 0) or 0),
        "state_rows": state_rows,
        "source_start_offset": source.get("startOffset"),
        "source_end_offset": source.get("endOffset"),
        "source_latest_offset": source.get("latestOffset"),
        "event_time": progress.get("eventTime", {}),
    }
