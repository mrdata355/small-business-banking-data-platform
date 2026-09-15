from pyspark.sql import DataFrame, functions as F


def normalize_identity(df: DataFrame) -> DataFrame:
    return (
        df
        .withColumn("verification_status", F.upper(F.trim("verification_status")))
        .filter(F.col("verification_status").isin("PENDING", "VERIFIED", "REVIEW", "FAILED"))
    )
