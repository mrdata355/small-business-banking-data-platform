from pathlib import Path

from oakbridge.common.spark import build_spark
from oakbridge.config.settings import Settings

DATASETS = [
    ("Silver business onboarding", "silver", "business_onboarding"),
    ("Silver loan application", "silver", "loan_application"),
    ("Silver identity verification", "silver", "identity_verification"),
    ("Silver ACH transaction", "silver", "ach_transaction"),
    ("Gold underwriting readiness", "gold", "underwriting_readiness_queue"),
    ("Gold treasury activity daily", "gold", "treasury_activity_daily"),
]


def main():
    cfg = Settings.from_env()
    spark = build_spark("oakbridge-results")
    spark.sparkContext.setLogLevel("WARN")

    for title, layer, name in DATASETS:
        path = getattr(cfg, f"{layer}_path")(name)
        print("\n" + "=" * 90)
        print(title)
        print(path)
        if Path(path).exists():
            spark.read.parquet(path).show(truncate=False)
        else:
            print("not created")

    spark.stop()


if __name__ == "__main__":
    main()
