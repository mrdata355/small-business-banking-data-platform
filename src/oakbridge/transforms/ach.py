from pyspark.sql import DataFrame, functions as F


def normalize_ach(df: DataFrame) -> DataFrame:
    return (
        df
        .withColumn("direction", F.upper(F.trim("direction")))
        .withColumn("sec_code", F.upper(F.trim("sec_code")))
        .withColumn("transaction_status", F.upper(F.trim("transaction_status")))
        .withColumn("processed_ts", F.current_timestamp())
        .filter(F.col("direction").isin("CREDIT", "DEBIT"))
        .filter(F.col("transaction_status").isin("PENDING", "POSTED", "RETURNED"))
        .filter(F.col("amount") > 0)
    )
