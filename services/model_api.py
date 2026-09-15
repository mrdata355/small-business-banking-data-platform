from __future__ import annotations

import os
from functools import lru_cache

import mlflow
import mlflow.pyfunc
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, make_asgi_app

TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
mlflow.set_tracking_uri(TRACKING_URI)

app = FastAPI(title="Banking Model API", version="1.0.0")
SCORES = Counter("model_scores_total", "Model scoring requests", ["model"])
LATENCY = Histogram("model_score_seconds", "Model scoring latency", ["model"])
app.mount("/metrics", make_asgi_app())


class ApplicationRiskRequest(BaseModel):
    requested_amount: float = Field(gt=0)
    documents_complete: int = Field(ge=0, le=1)
    financials_complete: int = Field(ge=0, le=1)
    identity_verified: int = Field(ge=0, le=1)
    event_version: int = Field(ge=1)
    age_minutes: float = Field(ge=0)


class AchAnomalyRequest(BaseModel):
    amount: float = Field(gt=0)
    direction_debit: int = Field(ge=0, le=1)
    hour: int = Field(ge=0, le=23)
    return_rate: float = Field(ge=0, le=1)


@lru_cache(maxsize=4)
def load_model(uri: str):
    return mlflow.pyfunc.load_model(uri)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "tracking_uri": TRACKING_URI}


@app.post("/score/application-risk")
def score_application(req: ApplicationRiskRequest) -> dict:
    with LATENCY.labels(model="application_operational_risk").time():
        model = load_model("models:/application_operational_risk@champion")
        frame = pd.DataFrame([req.model_dump()])
        prediction = model.predict(frame)
        SCORES.labels(model="application_operational_risk").inc()
        value = float(prediction[0])
        return {"prediction": value, "risk_band": "HIGH" if value >= 0.5 else "LOW"}


@app.post("/score/ach-anomaly")
def score_ach(req: AchAnomalyRequest) -> dict:
    with LATENCY.labels(model="ach_anomaly_detector").time():
        model = load_model("models:/ach_anomaly_detector@champion")
        frame = pd.DataFrame([req.model_dump()])
        prediction = int(model.predict(frame)[0])
        SCORES.labels(model="ach_anomaly_detector").inc()
        return {"prediction": prediction, "is_anomaly": prediction == -1}
