from __future__ import annotations

import os

from delta import configure_spark_with_delta_pip
from delta.tables import DeltaTable
from pyspark.sql import SparkSession, Window, functions as F, types as T

from oakbridge.observability.spark_streaming_metrics import install_streaming_metrics

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "redpanda:9092")
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://minio:9000")
ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin123")

APP_TOPIC = "lending.application-events.v1"
ACH_TOPIC = "treasury.ach-events.v1"

APP_BRONZE = "s3a://oakbridge-bronze/lending/application_event"
APP_HISTORY = "s3a://oakbridge-silver/lending/loan_application_status_history"
APP_CURRENT = "s3a://oakbridge-silver/lending/loan_application"
APP_QUARANTINE = "s3a://oakbridge-quarantine/lending/application_event"
ACH_BRONZE = "s3a://oakbridge-bronze/treasury/ach_event"
ACH_SILVER = "s3a://oakbridge-silver/treasury/ach_transaction"
CHECKPOINT_ROOT = "s3a://oakbridge-checkpoints"

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
    T.StructField("identity_verification_status", T.StringType(), False),
    T.StructField("source_system", T.StringType(), False),
    T.StructField("trace_id", T.StringType(), True),
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


def build_spark() -> SparkSession:
    packages = [
        "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3",
        "org.apache.hadoop:hadoop-aws:3.3.4",
        "com.amazonaws:aws-java-sdk-bundle:1.12.262",
    ]
    builder = (
        SparkSession.builder.appName("oakbridge-kafka-lakehouse")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.sql.shuffle.partitions", "12")
        .config("spark.hadoop.fs.s3a.endpoint", S3_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key", ACCESS_KEY)
        .config("spark.hadoop.fs.s3a.secret.key", SECRET_KEY)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
    )
    spark = configure_spark_with_delta_pip(builder, extra_packages=packages).getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark


def kafka_json_stream(spark: SparkSession, topic: str, schema: T.StructType):
    raw = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
        .option("subscribe", topic)
        .option("startingOffsets", "latest")
        .option("failOnDataLoss", "false")
        .load()
    )
    return (
        raw.select(
            F.from_json(F.col("value").cast("string"), schema).alias("record"),
            F.col("topic").alias("_kafka_topic"),
            F.col("partition").alias("_kafka_partition"),
            F.col("offset").alias("_kafka_offset"),
            F.col("timestamp").alias("_kafka_timestamp"),
        )
        .select("record.*", "_kafka_topic", "_kafka_partition", "_kafka_offset", "_kafka_timestamp")
        .withColumn("_ingest_ts", F.current_timestamp())
    )


def application_dq(df):
    valid_status = ["SUBMITTED", "DOCUMENTS_PENDING", "REVIEW", "READY_FOR_UNDERWRITING", "DECISIONED", "FUNDED", "DECLINED"]
    return df.withColumn(
        "dq_reason",
        F.when(F.col("event_id").isNull(), "MISSING_EVENT_ID")
        .when(F.col("application_id").isNull(), "MISSING_APPLICATION_ID")
        .when(F.col("event_version") < 1, "INVALID_EVENT_VERSION")
        .when(~F.col("application_status").isin(valid_status), "INVALID_APPLICATION_STATUS")
        .when(F.col("requested_amount") < 0, "NEGATIVE_REQUESTED_AMOUNT"),
    )


def upsert_application_current(batch_df, batch_id: int) -> None:
    if batch_df.isEmpty():
        return
    window = Window.partitionBy("application_id").orderBy(F.col("event_version").desc(), F.col("event_ts").desc())
    latest = batch_df.withColumn("_rn", F.row_number().over(window)).filter("_rn = 1").drop("_rn")
    if DeltaTable.isDeltaTable(batch_df.sparkSession, APP_CURRENT):
        target = DeltaTable.forPath(batch_df.sparkSession, APP_CURRENT)
        (
            target.alias("t")
            .merge(latest.alias("s"), "t.application_id = s.application_id")
            .whenMatchedUpdateAll(
                condition="s.event_version > t.event_version OR (s.event_version = t.event_version AND s.event_ts > t.event_ts)"
            )
            .whenNotMatchedInsertAll()
            .execute()
        )
    else:
        latest.write.format("delta").mode("overwrite").save(APP_CURRENT)


def process_application_batch(batch_df, batch_id: int) -> None:
    if batch_df.isEmpty():
        return
    checked = application_dq(batch_df).cache()
    checked.write.format("delta").mode("append").save(APP_BRONZE)
    invalid = checked.filter(F.col("dq_reason").isNotNull())
    if not invalid.isEmpty():
        invalid.write.format("delta").mode("append").save(APP_QUARANTINE)
    valid = checked.filter(F.col("dq_reason").isNull()).drop("dq_reason")
    if not valid.isEmpty():
        valid.write.format("delta").mode("append").save(APP_HISTORY)
        upsert_application_current(valid, batch_id)
    checked.unpersist()


def process_ach_batch(batch_df, batch_id: int) -> None:
    if batch_df.isEmpty():
        return
    batch_df.write.format("delta").mode("append").save(ACH_BRONZE)
    valid = (
        batch_df.filter(F.col("amount") > 0)
        .filter(F.col("direction").isin("CREDIT", "DEBIT"))
        .filter(F.col("transaction_status").isin("PENDING", "POSTED", "RETURNED"))
    )
    if not valid.isEmpty():
        valid.write.format("delta").mode("append").save(ACH_SILVER)


def main() -> None:
    spark = build_spark()
    install_streaming_metrics(spark, 9108)

    applications = (
        kafka_json_stream(spark, APP_TOPIC, APPLICATION_SCHEMA)
        .withWatermark("event_ts", "2 hours")
        .dropDuplicates(["event_id"])
    )
    ach = (
        kafka_json_stream(spark, ACH_TOPIC, ACH_SCHEMA)
        .withWatermark("event_ts", "2 hours")
        .dropDuplicates(["transaction_id"])
    )

    application_query = (
        applications.writeStream.queryName("lending_application_stream")
        .foreachBatch(process_application_batch)
        .option("checkpointLocation", f"{CHECKPOINT_ROOT}/lending/application_stream")
        .trigger(processingTime="5 seconds")
        .start()
    )
    ach_query = (
        ach.writeStream.queryName("treasury_ach_stream")
        .foreachBatch(process_ach_batch)
        .option("checkpointLocation", f"{CHECKPOINT_ROOT}/treasury/ach_stream")
        .trigger(processingTime="5 seconds")
        .start()
    )

    spark.streams.awaitAnyTermination()
    application_query.stop()
    ach_query.stop()


if __name__ == "__main__":
    main()
