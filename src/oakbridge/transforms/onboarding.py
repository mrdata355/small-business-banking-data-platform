from pyspark.sql import DataFrame, functions as F


def normalize_onboarding(df: DataFrame) -> DataFrame:
    return (
        df
        .withColumn("owner_email", F.lower(F.trim("owner_email")))
        .withColumn("formation_state", F.upper(F.trim("formation_state")))
        .withColumn("account_product", F.upper(F.trim("account_product")))
        .withColumn("kyc_status", F.upper(F.trim("kyc_status")))
        .withColumn("processed_ts", F.current_timestamp())
    )
