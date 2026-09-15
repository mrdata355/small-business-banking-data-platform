def read_kinesis_stream(spark, stream_name: str, region: str = "us-east-1"):
    """
    Databricks/AWS production adapter.

    Local development uses the file-stream adapter so the project can run without
    provisioning cloud resources.
    """
    return (
        spark.readStream
        .format("kinesis")
        .option("streamName", stream_name)
        .option("region", region)
        .option("initialPosition", "LATEST")
        .load()
    )
