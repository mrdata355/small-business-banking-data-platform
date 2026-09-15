from pyspark.sql import types as T

IDENTITY_SCHEMA = T.StructType([
    T.StructField("vendor_record_id", T.StringType(), False),
    T.StructField("application_id", T.StringType(), False),
    T.StructField("customer_id", T.StringType(), False),
    T.StructField("verification_status", T.StringType(), False),
    T.StructField("verification_ts", T.TimestampType(), False),
    T.StructField("reason_code", T.StringType(), True),
    T.StructField("vendor_file_id", T.StringType(), False),
])
