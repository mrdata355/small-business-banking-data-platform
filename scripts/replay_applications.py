from oakbridge.common.spark import build_spark
from oakbridge.config.settings import Settings
from oakbridge.jobs.backfill import replay_application_range


if __name__ == "__main__":
    spark = build_spark("oakbridge-application-replay")
    replay_application_range(spark, Settings.from_env())
    spark.stop()
