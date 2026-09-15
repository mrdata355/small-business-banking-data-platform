# MLOps architecture

## Tracking and registry

MLflow stores experiment metadata in its backend store and model artifacts in the MinIO `oakbridge-ml-artifacts` bucket. Both generated models are registered and the active version receives the `champion` alias.

Registered models:

```text
application_operational_risk
ach_anomaly_detector
```

## Training

`mlops/train_models.py` creates deterministic generated training sets, trains both models, logs parameters/metrics/artifacts and promotes the newest registered versions to `champion`.

## Serving

`services/model_api.py` loads the current champion aliases and exposes:

```text
POST /score/application-risk
POST /score/ach-anomaly
GET  /health
GET  /metrics
```

## Monitoring

The API exposes Prometheus scoring counters and latency histograms. The live internet demo separately persists model predictions so model outcomes can be inspected without starting the local MLflow environment.

## Promotion model

A production deployment would extend this with explicit quality thresholds, challenger evaluation, approval policy, shadow scoring, drift monitoring and rollback. The local platform intentionally keeps promotion deterministic and reproducible.
