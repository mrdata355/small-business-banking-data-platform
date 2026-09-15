# MLOps

The local stack runs MLflow with a persistent SQLite metadata store and MinIO-backed artifacts.

## Models

### application_operational_risk
Gradient-boosted classification model trained on generated lending workflow features.

Inputs:
- requested_amount
- documents_complete
- financials_complete
- identity_verified
- event_version
- age_minutes

### ach_anomaly_detector
Isolation Forest for generated ACH activity.

Inputs:
- amount
- direction_debit
- hour
- return_rate

## Lifecycle

1. `model-trainer` waits for MLflow.
2. `mlops/train_models.py` trains both models and logs parameters, metrics and artifacts.
3. Each registered model receives the `champion` alias.
4. `model-api` loads the current champion alias and exposes scoring endpoints.
5. Prometheus scrapes scoring request metrics.
6. MLflow UI is available at `http://localhost:5000`.

All training data is generated for this project.
