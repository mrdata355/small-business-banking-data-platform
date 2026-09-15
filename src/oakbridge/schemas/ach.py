from pyspark.sql import types as T

ACH_EVENT_SCHEMA = T.StructType([
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
