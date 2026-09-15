from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import StructType


def read_json_stream(spark: SparkSession, path: str, schema: StructType, max_files_per_trigger: int = 10) -> DataFrame:
    return spark.readStream.schema(schema).option("maxFilesPerTrigger", max_files_per_trigger).json(path)


def read_parquet_stream(spark: SparkSession, path: str, schema: StructType) -> DataFrame:
    return spark.readStream.schema(schema).parquet(path)
