from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass(frozen=True)
class AgentProfile:
    agent_id: str
    name: str
    department: str
    specialty: str
    objective: str
    inputs: tuple[str, ...]
    actions: tuple[str, ...]
    guardrails: tuple[str, ...]
    priority_metrics: tuple[str, ...]


DEPARTMENTS = {
    "DATA_PLATFORM": ("Data Platform", ("freshness", "correctness", "cost", "recovery")),
    "LENDING": ("Lending", ("cycle_time", "readiness", "conversion", "quality")),
    "TREASURY": ("Treasury", ("payment_success", "anomaly_rate", "settlement", "experience")),
    "RISK": ("Risk", ("loss_avoidance", "exceptions", "model_risk", "concentration")),
    "COMPLIANCE": ("Compliance", ("control_coverage", "exceptions", "lineage", "retention")),
    "FINANCE": ("Finance", ("margin", "growth", "forecast_accuracy", "unit_economics")),
    "OPERATIONS": ("Operations", ("throughput", "backlog", "sla", "rework")),
    "DATA_SCIENCE": ("Data Science", ("precision", "recall", "drift", "business_value")),
    "CUSTOMER_SUCCESS": ("Customer Success", ("resolution_time", "sentiment", "contact_rate", "retention")),
    "PRODUCT": ("Product", ("adoption", "conversion", "task_success", "time_to_value")),
    "SRE": ("SRE", ("availability", "latency", "error_budget", "mttr")),
    "SECURITY": ("Security", ("least_privilege", "exposure", "secrets", "auditability")),
    "EXECUTIVE": ("Executive", ("growth", "risk_adjusted_return", "service", "efficiency")),
    "SHAREHOLDER": ("Shareholder", ("growth", "profitability", "asset_quality", "operating_leverage")),
    "ARCHITECTURE": ("Architecture", ("coupling", "resilience", "reuse", "change_failure_rate")),
    "QUALITY": ("Data Quality", ("completeness", "validity", "uniqueness", "reconciliation")),
}

SPECIALTIES = (
    ("sentinel", "Detect abnormal behavior and create evidence-backed intervention recommendations."),
    ("forecaster", "Forecast workload, service pressure and KPI movement with uncertainty bounds."),
    ("optimizer", "Identify the highest-value feasible optimization under cost and risk constraints."),
    ("reconciler", "Explain every material source-to-target delta and isolate unexplained differences."),
    ("contract_guardian", "Assess schema and data-contract compatibility before deployment."),
    ("incident_analyst", "Rank likely failure causes from telemetry and propose the smallest safe mitigation."),
    ("capacity_planner", "Predict capacity pressure and recommend scaling or partition changes."),
    ("portfolio_advisor", "Prioritize work by business value, risk reduction, urgency and effort."),
)

INPUTS = (
    "pipeline_metrics", "data_quality_results", "work_items", "deployment_history",
    "model_predictions", "customer_interactions", "business_kpis", "lineage_graph",
)

ACTIONS = (
    "recommend", "prioritize", "open_work_item", "request_evidence", "simulate_change",
    "flag_risk", "propose_test", "propose_backfill", "propose_rollback", "explain_tradeoff",
)

GUARDRAILS = (
    "never fabricate evidence",
    "never mutate production data without an approved action path",
    "never expose restricted identifiers",
    "attach evidence and confidence to every recommendation",
    "prefer reversible actions when impact is uncertain",
)


def build_registry() -> list[AgentProfile]:
    profiles: list[AgentProfile] = []
    for dept_code, (dept_name, metrics) in DEPARTMENTS.items():
        for specialty, objective in SPECIALTIES:
            agent_id = f"{dept_code.lower()}_{specialty}"
            profiles.append(
                AgentProfile(
                    agent_id=agent_id,
                    name=f"{dept_name} {specialty.replace('_', ' ').title()}",
                    department=dept_code,
                    specialty=specialty,
                    objective=objective,
                    inputs=INPUTS,
                    actions=ACTIONS,
                    guardrails=GUARDRAILS,
                    priority_metrics=metrics,
                )
            )
    return profiles


REGISTRY = build_registry()
REGISTRY_BY_ID = {profile.agent_id: profile for profile in REGISTRY}


def registry_as_dicts() -> list[dict]:
    return [asdict(profile) for profile in REGISTRY]


def agents_for_department(department: str) -> list[AgentProfile]:
    return [profile for profile in REGISTRY if profile.department == department]


def select_agents(specialties: Iterable[str] = (), departments: Iterable[str] = ()) -> list[AgentProfile]:
    specialty_set = set(specialties)
    department_set = set(departments)
    return [
        profile for profile in REGISTRY
        if (not specialty_set or profile.specialty in specialty_set)
        and (not department_set or profile.department in department_set)
    ]


assert len(REGISTRY) == 128
