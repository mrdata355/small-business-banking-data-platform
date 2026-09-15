import json
from pathlib import Path

import requests

REGISTRY = "http://redpanda:8081"
SUBJECTS = {
    "lending.application-events.v1-value": "contracts/application_event_v1.schema.json",
    "treasury.ach-events.v1-value": "contracts/ach_event_v1.schema.json",
}

for subject, path in SUBJECTS.items():
    schema = Path(path).read_text(encoding="utf-8")
    payload = {"schemaType": "JSON", "schema": schema}
    response = requests.post(
        f"{REGISTRY}/subjects/{subject}/versions",
        json=payload,
        timeout=20,
    )
    response.raise_for_status()
    print(subject, response.json())
