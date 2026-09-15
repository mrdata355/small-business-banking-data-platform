from pprint import pprint

from oakbridge.common.spark import build_spark
from oakbridge.config.settings import Settings
from oakbridge.jobs.ach_pipeline import run_ach_pipeline
from oakbridge.jobs.application_pipeline import run_application_pipeline
from oakbridge.jobs.gold_pipeline import build_gold_outputs
from oakbridge.jobs.identity_pipeline import run_identity_pipeline
from oakbridge.jobs.onboarding_pipeline import run_onboarding_pipeline
from oakbridge.jobs.reconciliation import reconcile_applications

from seed_data import seed


def main():
    cfg = seed(reset=True)
    spark = build_spark("oakbridge-local-platform")
    spark.sparkContext.setLogLevel("WARN")

    print("1/6 business onboarding")
    run_onboarding_pipeline(spark, cfg)

    print("2/6 lending application stream")
    run_application_pipeline(spark, cfg)

    print("3/6 identity verification files")
    run_identity_pipeline(spark, cfg)

    print("4/6 treasury / ACH stream")
    run_ach_pipeline(spark, cfg)

    print("5/6 gold outputs")
    build_gold_outputs(spark, cfg)

    print("6/6 reconciliation")
    result = reconcile_applications(spark, cfg)
    pprint(result)
    if not result["balanced"]:
        raise RuntimeError(f"Application reconciliation failed: {result}")

    spark.stop()
    print("Pipeline run completed successfully.")


if __name__ == "__main__":
    main()
