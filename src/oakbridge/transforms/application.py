from pyspark.sql import DataFrame, functions as F

VALID_EVENT_TYPES = [
    "LoanApplicationSubmitted",
    "ApplicationStatusChanged",
    "DocumentReceived",
    "FinancialPackageReceived",
]
VALID_APPLICATION_STATUS = [
    "SUBMITTED",
    "DOCUMENTS_PENDING",
    "REVIEW",
    "READY_FOR_UNDERWRITING",
    "DECISIONED",
    "FUNDED",
]


def with_application_dq(df: DataFrame) -> DataFrame:
    return df.withColumn(
        "dq_reason",
        F.when(F.col("event_id").isNull(), F.lit("MISSING_EVENT_ID"))
        .when(F.col("application_id").isNull(), F.lit("MISSING_APPLICATION_ID"))
        .when(~F.col("event_type").isin(VALID_EVENT_TYPES), F.lit("INVALID_EVENT_TYPE"))
        .when(
            ~F.col("application_status").isin(VALID_APPLICATION_STATUS),
            F.lit("INVALID_APPLICATION_STATUS"),
        )
        .when(F.col("event_version") < 1, F.lit("INVALID_EVENT_VERSION"))
    )


def normalize_application(df: DataFrame) -> DataFrame:
    return (
        df
        .withColumn("application_status", F.upper(F.trim("application_status")))
        .withColumn("product_code", F.upper(F.trim("product_code")))
        .withColumn("use_of_funds", F.upper(F.trim("use_of_funds")))
        .withColumn("processed_ts", F.current_timestamp())
    )
