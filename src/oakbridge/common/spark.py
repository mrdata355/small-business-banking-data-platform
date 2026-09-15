from pyspark.sql import SparkSession


def build_spark(app_name: str) -> SparkSession:
    return (
        SparkSession.builder
        .master("local[2]")
        .appName(app_name)
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true")
        .getOrCreate()
    )
