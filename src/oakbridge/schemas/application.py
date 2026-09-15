from pyspark.sql import types as T

APPLICATION_EVENT_SCHEMA = T.StructType([
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
    T.StructField("source_system", T.StringType(), False),
    T.StructField("trace_id", T.StringType(), False),
])
