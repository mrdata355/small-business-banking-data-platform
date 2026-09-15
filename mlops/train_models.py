from __future__ import annotations

import os

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from mlflow import MlflowClient
from sklearn.ensemble import GradientBoostingClassifier, IsolationForest
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split

TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
mlflow.set_tracking_uri(TRACKING_URI)


def latest_version(client: MlflowClient, name: str) -> str:
    versions = client.search_model_versions(f"name='{name}'")
    return str(max(int(v.version) for v in versions))


def train_application_risk(rng: np.random.Generator) -> None:
    n = 5000
    requested_amount = rng.uniform(50_000, 1_500_000, n)
    documents_complete = rng.integers(0, 2, n)
    financials_complete = rng.integers(0, 2, n)
    identity_verified = rng.binomial(1, 0.82, n)
    event_version = rng.integers(1, 8, n)
    age_minutes = rng.gamma(2.2, 45.0, n)

    raw_risk = (
        0.00000035 * requested_amount
        + 0.55 * (1 - documents_complete)
        + 0.65 * (1 - financials_complete)
        + 0.90 * (1 - identity_verified)
        + 0.0017 * age_minutes
        - 0.035 * event_version
        + rng.normal(0, 0.25, n)
    )
    y = (raw_risk > np.quantile(raw_risk, 0.62)).astype(int)
    X = pd.DataFrame(
        {
            "requested_amount": requested_amount,
            "documents_complete": documents_complete,
            "financials_complete": financials_complete,
            "identity_verified": identity_verified,
            "event_version": event_version,
            "age_minutes": age_minutes,
        }
    )
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    model = GradientBoostingClassifier(random_state=42)
    model.fit(X_train, y_train)
    prob = model.predict_proba(X_test)[:, 1]
    pred = (prob >= 0.5).astype(int)

    mlflow.set_experiment("application_operational_risk")
    with mlflow.start_run(run_name="gradient_boosting_v1"):
        mlflow.log_params({"model_type": "GradientBoostingClassifier", "rows": n})
        mlflow.log_metrics(
            {
                "roc_auc": float(roc_auc_score(y_test, prob)),
                "accuracy": float(accuracy_score(y_test, pred)),
            }
        )
        mlflow.sklearn.log_model(
            model,
            artifact_path="model",
            registered_model_name="application_operational_risk",
            input_example=X_train.head(5),
        )

    client = MlflowClient()
    version = latest_version(client, "application_operational_risk")
    client.set_registered_model_alias("application_operational_risk", "champion", version)
    print(f"application_operational_risk champion=v{version}")


def train_ach_anomaly(rng: np.random.Generator) -> None:
    n = 6000
    normal_amount = rng.lognormal(mean=8.4, sigma=1.0, size=n)
    direction_debit = rng.integers(0, 2, n)
    hour = rng.integers(0, 24, n)
    return_rate = rng.beta(1.2, 18.0, n)
    X = pd.DataFrame(
        {
            "amount": normal_amount,
            "direction_debit": direction_debit,
            "hour": hour,
            "return_rate": return_rate,
        }
    )
    model = IsolationForest(
        n_estimators=250,
        contamination=0.025,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X)
    anomaly_fraction = float((model.predict(X) == -1).mean())

    mlflow.set_experiment("ach_anomaly_detection")
    with mlflow.start_run(run_name="isolation_forest_v1"):
        mlflow.log_params(
            {"model_type": "IsolationForest", "rows": n, "contamination": 0.025}
        )
        mlflow.log_metric("predicted_anomaly_fraction", anomaly_fraction)
        mlflow.sklearn.log_model(
            model,
            artifact_path="model",
            registered_model_name="ach_anomaly_detector",
            input_example=X.head(5),
        )

    client = MlflowClient()
    version = latest_version(client, "ach_anomaly_detector")
    client.set_registered_model_alias("ach_anomaly_detector", "champion", version)
    print(f"ach_anomaly_detector champion=v{version}")


def main() -> None:
    rng = np.random.default_rng(42)
    train_application_risk(rng)
    train_ach_anomaly(rng)


if __name__ == "__main__":
    main()
