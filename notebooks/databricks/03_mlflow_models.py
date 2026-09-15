# Databricks notebook source
# COMMAND ----------
# Registered model inspection for a Databricks/MLflow deployment.
import mlflow
from mlflow import MlflowClient

client = MlflowClient()

# COMMAND ----------
for name in ["application_operational_risk", "ach_anomaly_detector"]:
    print(f"\n{name}")
    try:
        model = client.get_registered_model(name)
        print(model)
        versions = client.search_model_versions(f"name='{name}'")
        for version in versions:
            print("version", version.version, "status", version.status, "run_id", version.run_id)
    except Exception as exc:
        print("model not registered in this workspace:", exc)

# COMMAND ----------
# Example model load after registry deployment.
# model = mlflow.pyfunc.load_model("models:/application_operational_risk@champion")
