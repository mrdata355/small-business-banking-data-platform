from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOTS = ["src", "scripts", "tests", "services", "mlops", "agents", "digital_twin", "collaboration"]
JSON_ROOTS = ["contracts", "monitoring", "site"]


def validate_python() -> list[str]:
    errors: list[str] = []
    for root_name in PYTHON_ROOTS:
        root = ROOT / root_name
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            try:
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except SyntaxError as exc:
                errors.append(f"python syntax: {path.relative_to(ROOT)}:{exc.lineno}: {exc.msg}")
    return errors


def validate_json() -> list[str]:
    errors: list[str] = []
    for root_name in JSON_ROOTS:
        root = ROOT / root_name
        if not root.exists():
            continue
        for path in root.rglob("*.json"):
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                errors.append(f"json: {path.relative_to(ROOT)}: {exc}")
    return errors


def validate_required_assets() -> list[str]:
    required = [
        "docker-compose.full.yml",
        "contracts/application_event_v1.schema.json",
        "contracts/ach_event_v1.schema.json",
        "src/oakbridge/jobs/kafka_lakehouse_stream.py",
        "warehouse/star_schema.sql",
        "digital_twin/twin.py",
        "digital_twin/contract_genome.py",
        "agents/orchestrator.py",
        "collaboration/recommendation_engine.py",
        "mlops/drift_monitor.py",
        "site/twin.html",
        "site/agents.html",
        "site/collaboration.html",
    ]
    return [f"missing required asset: {item}" for item in required if not (ROOT / item).exists()]


def main() -> int:
    errors = validate_python() + validate_json() + validate_required_assets()
    if errors:
        print("Repository validation failed:")
        for error in errors:
            print(f" - {error}")
        return 1
    print("Repository validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
