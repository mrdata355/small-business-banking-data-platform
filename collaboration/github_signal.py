from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from collaboration.recommendation_engine import WorkItem


LABEL_DEPARTMENT = {
    "data-platform": "DATA_PLATFORM",
    "lending": "LENDING",
    "risk": "RISK",
    "treasury": "TREASURY",
    "finance": "FINANCE",
    "customer-success": "CUSTOMER_SUCCESS",
    "ml": "DATA_SCIENCE",
    "executive": "EXECUTIVE",
}

PRIORITY_LABELS = {"p0": "P0", "p1": "P1", "p2": "P2", "p3": "P3", "p4": "P4", "critical": "P0", "high": "P1"}


def _labels(record: dict[str, Any]) -> list[str]:
    values = []
    for label in record.get("labels", []):
        values.append(label.get("name", "") if isinstance(label, dict) else str(label))
    return [v.strip().lower() for v in values if v]


def _department(labels: list[str], fallback: str = "DATA_PLATFORM") -> str:
    for label in labels:
        if label in LABEL_DEPARTMENT:
            return LABEL_DEPARTMENT[label]
    return fallback


def _priority(labels: list[str]) -> str:
    for label in labels:
        if label in PRIORITY_LABELS:
            return PRIORITY_LABELS[label]
    return "P2"


def _score_from_labels(labels: list[str], positive: set[str], default: float) -> float:
    return min(10.0, default + sum(2.0 for label in labels if label in positive))


def issue_to_work_item(issue: dict[str, Any], repo_full_name: str) -> WorkItem:
    labels = _labels(issue)
    department = _department(labels)
    requester = _department([l.removeprefix("requester:") for l in labels if l.startswith("requester:")], "PRODUCT")
    number = issue.get("number")
    html_url = issue.get("html_url") or f"https://github.com/{repo_full_name}/issues/{number}"
    state = str(issue.get("state", "open")).lower()
    status = "DONE" if state == "closed" else "BLOCKED" if "blocked" in labels else "IN_PROGRESS" if "in-progress" in labels else "READY"
    due = None
    if issue.get("due_at"):
        due = datetime.fromisoformat(str(issue["due_at"]).replace("Z", "+00:00"))
    return WorkItem(
        work_key=f"GH-{number}",
        title=str(issue.get("title", "Untitled issue")),
        department=department,
        requester_department=requester,
        status=status,
        priority=_priority(labels),
        business_value=_score_from_labels(labels, {"growth", "customer", "revenue", "strategic"}, 4),
        risk_reduction=_score_from_labels(labels, {"risk", "security", "compliance", "reliability"}, 3),
        urgency=_score_from_labels(labels, {"incident", "outage", "deadline", "critical"}, 3),
        effort=float(issue.get("effort_score", 3)),
        blocked_by=tuple(str(x) for x in issue.get("blocked_by", [])),
        labels=tuple(labels),
        github_ref=html_url,
        due_at=due,
    )


def pull_request_signal(pr: dict[str, Any]) -> dict[str, Any]:
    labels = _labels(pr)
    additions = int(pr.get("additions", 0) or 0)
    deletions = int(pr.get("deletions", 0) or 0)
    files = int(pr.get("changed_files", 0) or 0)
    churn = additions + deletions
    complexity_score = min(10.0, (churn / 500) + (files / 8))
    risk_score = complexity_score
    if any(label in {"schema", "migration", "security", "breaking-change", "production"} for label in labels):
        risk_score = min(10.0, risk_score + 3)
    return {
        "number": pr.get("number"),
        "title": pr.get("title"),
        "url": pr.get("html_url"),
        "department": _department(labels),
        "labels": labels,
        "changed_files": files,
        "code_churn": churn,
        "complexity_score": round(complexity_score, 3),
        "change_risk_score": round(risk_score, 3),
        "recommended_checks": _recommended_checks(labels, risk_score),
    }


def _recommended_checks(labels: list[str], risk_score: float) -> list[str]:
    checks = ["unit-tests", "lint", "contract-tests"]
    if any(label in {"schema", "migration", "breaking-change"} for label in labels):
        checks += ["contract-genome", "counterfactual-replay", "lineage-blast-radius"]
    if any(label in {"streaming", "kafka", "spark"} for label in labels):
        checks += ["stream-replay-idempotency", "watermark-lateness", "checkpoint-recovery"]
    if any(label in {"security", "pii", "compliance"} for label in labels):
        checks += ["classification-policy", "secret-scan", "least-privilege-review"]
    if risk_score >= 7:
        checks += ["load-test", "rollback-drill", "two-person-approval"]
    return sorted(set(checks))
