from __future__ import annotations

import json
import os
import random
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import boto3
from botocore.client import Config
from confluent_kafka import Producer
from fastapi import FastAPI, HTTPException
from jsonschema import Draft202012Validator
from prometheus_client import Counter, Histogram, make_asgi_app

APP_TOPIC = "lending.application-events.v1"
ACH_TOPIC = "treasury.ach-events.v1"

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "redpanda:9092")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
LANDING_BUCKET = os.getenv("MINIO_LANDING_BUCKET", "oakbridge-landing")

app = FastAPI(title="Banking Stream Gateway", version="1.0.0")
producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP, "enable.idempotence": True})
s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    config=Config(signature_version="s3v4"),
    region_name="us-east-1",
)

application_schema = json.loads(Path("contracts/application_event_v1.schema.json").read_text())
ach_schema = json.loads(Path("contracts/ach_event_v1.schema.json").read_text())
application_validator = Draft202012Validator(application_schema)
ach_validator = Draft202012Validator(ach_schema)

EVENTS_ACCEPTED = Counter("gateway_events_accepted_total", "Accepted events", ["topic"])
EVENTS_REJECTED = Counter("gateway_events_rejected_total", "Rejected events", ["topic", "reason"])
REQUEST_LATENCY = Histogram("gateway_request_seconds", "Gateway request latency", ["route"])

app.mount("/metrics", make_asgi_app())


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def random_suffix() -> str:
    return uuid.uuid4().hex[:10].upper()


def validate_or_raise(payload: dict, validator: Draft202012Validator, topic: str) -> None:
    errors = sorted(validator.iter_errors(payload), key=lambda e: e.path)
    if errors:
        reason = errors[0].message[:120]
        EVENTS_REJECTED.labels(topic=topic, reason="schema_validation").inc()
        raise HTTPException(status_code=422, detail=reason)


def persist_landing(topic: str, payload: dict, event_id: str) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    epoch_ms = int(time.time() * 1000)
    prefix = topic.replace(".", "/")
    key = f"landing/{prefix}/event_date={today}/{event_id.lower()}-{epoch_ms}.json"
    s3.put_object(
        Bucket=LANDING_BUCKET,
        Key=key,
        Body=(json.dumps(payload, sort_keys=True) + "\n").encode("utf-8"),
        ContentType="application/json",
        Metadata={"topic": topic, "event-id": event_id},
    )
    return key


def publish(topic: str, key: str, payload: dict) -> None:
    producer.produce(topic, key=key, value=json.dumps(payload).encode("utf-8"))
    producer.flush(10)
    EVENTS_ACCEPTED.labels(topic=topic).inc()


def make_application_event(application_id: str | None = None, event_version: int = 1, event_type: str = "LoanApplicationSubmitted") -> dict:
    suffix = application_id.split("-")[-1] if application_id else random_suffix()
    application_id = application_id or f"APP-{suffix}"
    status = "SUBMITTED"
    docs = False
    financials = False
    identity = "PENDING"
    if event_type == "DocumentReceived":
        status, docs = "DOCUMENTS_PENDING", True
    elif event_type == "FinancialPackageReceived":
        status, docs, financials = "REVIEW", True, True
    elif event_type == "IdentityVerificationUpdated":
        status, docs, financials, identity = "REVIEW", True, True, "VERIFIED"
    elif event_type == "Decisioned":
        status, docs, financials, identity = "DECISIONED", True, True, "VERIFIED"
    return {
        "event_id": f"EVT-{random_suffix()}",
        "event_type": event_type,
        "event_version": event_version,
        "event_ts": utc_now(),
        "application_id": application_id,
        "customer_id": f"CUST-{suffix}",
        "business_id": f"BIZ-{suffix}",
        "product_code": random.choice(["SBA_7A", "USDA_BI", "CONVENTIONAL", "CUSTOM"]),
        "requested_amount": float(random.choice([125000, 250000, 500000, 850000, 1250000])),
        "use_of_funds": random.choice(["WORKING_CAPITAL", "ACQUISITION", "EQUIPMENT", "CRE"]),
        "application_status": status,
        "documents_complete": docs,
        "financial_package_complete": financials,
        "identity_verification_status": identity,
        "source_system": "stream_gateway",
        "trace_id": f"tr-{uuid.uuid4().hex[:16]}",
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "kafka": KAFKA_BOOTSTRAP, "landing_bucket": LANDING_BUCKET}


@app.post("/events/application")
def ingest_application(payload: dict) -> dict:
    with REQUEST_LATENCY.labels(route="application").time():
        validate_or_raise(payload, application_validator, APP_TOPIC)
        key = persist_landing(APP_TOPIC, payload, payload["event_id"])
        publish(APP_TOPIC, payload["application_id"], payload)
        return {"accepted": True, "topic": APP_TOPIC, "object_key": key, "payload": payload}


@app.post("/events/ach")
def ingest_ach(payload: dict) -> dict:
    with REQUEST_LATENCY.labels(route="ach").time():
        validate_or_raise(payload, ach_validator, ACH_TOPIC)
        key = persist_landing(ACH_TOPIC, payload, payload["transaction_id"])
        publish(ACH_TOPIC, payload["business_id"], payload)
        return {"accepted": True, "topic": ACH_TOPIC, "object_key": key, "payload": payload}


@app.post("/demo/application")
def demo_application() -> dict:
    payload = make_application_event()
    return ingest_application(payload)


@app.post("/demo/application/{application_id}/{event_version}/{event_type}")
def demo_application_step(application_id: str, event_version: int, event_type: str) -> dict:
    allowed = {"DocumentReceived", "FinancialPackageReceived", "IdentityVerificationUpdated", "Decisioned"}
    if event_type not in allowed:
        raise HTTPException(400, f"Unsupported event type: {event_type}")
    return ingest_application(make_application_event(application_id, event_version, event_type))


@app.post("/demo/batch/{count}")
def demo_batch(count: int) -> dict:
    count = max(1, min(count, 250))
    results = []
    for _ in range(count):
        results.append(demo_application())
    return {"count": count, "objects": [r["object_key"] for r in results]}


@app.post("/demo/ach")
def demo_ach() -> dict:
    suffix = random_suffix()
    payload = {
        "transaction_id": f"ACH-{suffix}",
        "event_ts": utc_now(),
        "account_id": f"ACCT-{suffix[:6]}",
        "business_id": f"BIZ-{suffix[:6]}",
        "direction": random.choice(["CREDIT", "DEBIT"]),
        "amount": round(random.uniform(100.0, 50000.0), 2),
        "sec_code": random.choice(["CCD", "CTX", "PPD", "WEB"]),
        "transaction_status": random.choice(["PENDING", "POSTED", "RETURNED"]),
        "counterparty_token": f"cp-{uuid.uuid4().hex[:12]}",
        "source_system": "stream_gateway",
    }
    return ingest_ach(payload)
