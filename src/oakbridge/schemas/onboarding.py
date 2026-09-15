from pyspark.sql import types as T

BUSINESS_ONBOARDING_SCHEMA = T.StructType([
    T.StructField("onboarding_event_id", T.StringType(), False),
    T.StructField("event_ts", T.TimestampType(), False),
    T.StructField("customer_id", T.StringType(), False),
    T.StructField("business_id", T.StringType(), False),
    T.StructField("owner_name", T.StringType(), False),
    T.StructField("owner_email", T.StringType(), False),
    T.StructField("owner_phone", T.StringType(), False),
    T.StructField("owner_dob", T.DateType(), False),
    T.StructField("tax_id_token", T.StringType(), False),
    T.StructField("legal_business_name", T.StringType(), False),
    T.StructField("ein_token", T.StringType(), False),
    T.StructField("naics_code", T.StringType(), False),
    T.StructField("formation_state", T.StringType(), False),
    T.StructField("formation_date", T.DateType(), False),
    T.StructField("business_address", T.StringType(), False),
    T.StructField("account_product", T.StringType(), False),
    T.StructField("kyc_status", T.StringType(), False),
    T.StructField("source_system", T.StringType(), False),
])
