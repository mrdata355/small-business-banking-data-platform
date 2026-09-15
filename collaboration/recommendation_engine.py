from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable


@dataclass(frozen=True)
class WorkItem:
    work_key: str
    title: str
    department: str
    requester_department: str
    status: str
    priority: str
    business_value: float
    risk_reduction: float
    urgency: float
    effort: float
    blocked_by: tuple[str, ...] = ()
    labels: tuple[str, ...] = ()
    github_ref: str | None = None
    due_at: datetime | None = None

    @property
    def base_score(self) -> float:
        priority_boost = {"P0": 8.0, "P1": 5.0, "P2": 2.5, "P3": 1.0, "P4": 0.0}.get(self.priority, 0)
        due_boost = 0.0
        if self.due_at:
            hours = max(1.0, (self.due_at - datetime.now(timezone.utc)).total_seconds() / 3600)
            due_boost = min(8.0, 72.0 / hours)
        return (self.business_value + self.risk_reduction + self.urgency + priority_boost + due_boost) / max(0.5, self.effort)


@dataclass(frozen=True)
class DepartmentObjective:
    department: str
    metric_weights: dict[str, float]
    preferred_labels: tuple[str, ...] = ()
    capacity_hours: float = 40.0


@dataclass
class RankedWork:
    work_item: WorkItem
    score: float
    rationale: list[str] = field(default_factory=list)
    predicted_helpfulness: float = 0.0
    next_action: str = "REVIEW"


class CrossDepartmentRecommendationEngine:
    """Risk-adjusted collaboration queue with explainable ranking.

    This engine is intentionally deterministic. It can consume issues from a GitHub/Jira-like
    source, live pipeline signals, and department objectives without requiring an opaque model
    to decide priority.
    """

    def __init__(self, objectives: Iterable[DepartmentObjective]):
        self.objectives = {o.department: o for o in objectives}

    def rank_for_department(self, department: str, items: Iterable[WorkItem], signals: dict[str, float] | None = None) -> list[RankedWork]:
        objective = self.objectives[department]
        signals = signals or {}
        ranked: list[RankedWork] = []
        for item in items:
            if item.status in {"DONE", "CANCELLED"}:
                continue
            score = item.base_score
            rationale = [f"base value/risk/urgency-to-effort score={item.base_score:.2f}"]

            if item.department == department:
                score *= 1.18
                rationale.append("owned by this department")
            if item.requester_department != department:
                score *= 1.07
                rationale.append(f"unblocks cross-department request from {item.requester_department}")
            if item.blocked_by:
                score *= 0.65
                rationale.append(f"blocked by {len(item.blocked_by)} dependency item(s)")
            preferred = set(objective.preferred_labels) & set(item.labels)
            if preferred:
                score *= 1 + min(0.35, .08 * len(preferred))
                rationale.append(f"matches department objective labels: {', '.join(sorted(preferred))}")

            for signal, weight in objective.metric_weights.items():
                magnitude = max(0.0, float(signals.get(signal, 0.0)))
                if magnitude:
                    boost = min(0.5, math.log1p(magnitude) * weight / 20)
                    score *= 1 + boost
                    rationale.append(f"live signal {signal} contributes {boost:.1%} boost")

            helpfulness = min(0.99, 0.45 + 0.04 * item.business_value + 0.045 * item.risk_reduction + 0.03 * item.urgency - 0.02 * item.effort)
            action = "START" if not item.blocked_by and score >= 7 else "UNBLOCK" if item.blocked_by else "REVIEW"
            ranked.append(RankedWork(item, score, rationale, helpfulness, action))

        return sorted(ranked, key=lambda x: (x.score, x.predicted_helpfulness), reverse=True)

    def portfolio(self, items: Iterable[WorkItem], signals: dict[str, float] | None = None) -> dict[str, list[RankedWork]]:
        item_list = list(items)
        return {department: self.rank_for_department(department, item_list, signals) for department in self.objectives}


DEFAULT_OBJECTIVES = [
    DepartmentObjective("DATA_PLATFORM", {"lag_ms": 1.2, "dq_failure_rate": 1.4, "reconciliation_delta": 1.8}, ("data", "pipeline", "reliability", "contract"), 80),
    DepartmentObjective("LENDING", {"application_backlog": 1.5, "decision_cycle_time": 1.2}, ("lending", "underwriting", "document"), 80),
    DepartmentObjective("RISK", {"high_risk_predictions": 1.4, "policy_exception_rate": 1.5}, ("risk", "compliance", "model"), 60),
    DepartmentObjective("TREASURY", {"payment_return_rate": 1.5, "anomaly_count": 1.3}, ("treasury", "ach", "payment"), 60),
    DepartmentObjective("FINANCE", {"cost_variance": 1.2, "margin_pressure": 1.3}, ("cost", "forecast", "kpi"), 50),
    DepartmentObjective("CUSTOMER_SUCCESS", {"negative_sentiment": 1.4, "contact_backlog": 1.2}, ("customer", "sentiment", "resolution"), 60),
    DepartmentObjective("DATA_SCIENCE", {"model_drift": 1.5, "prediction_latency": 1.1}, ("model", "feature", "mlops"), 60),
    DepartmentObjective("EXECUTIVE", {"growth_gap": 1.1, "risk_adjusted_return_gap": 1.5}, ("strategy", "shareholder", "growth"), 20),
]


def default_engine() -> CrossDepartmentRecommendationEngine:
    return CrossDepartmentRecommendationEngine(DEFAULT_OBJECTIVES)
