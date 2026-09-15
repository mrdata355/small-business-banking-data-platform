from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable

from agents.registry import AgentProfile, REGISTRY_BY_ID, select_agents


@dataclass(frozen=True)
class Evidence:
    source: str
    metric: str
    value: float | int | str | bool | None
    observed_at: str
    weight: float = 1.0


@dataclass
class Recommendation:
    agent_id: str
    department: str
    title: str
    action: str
    rationale: str
    confidence: float
    expected_value: float
    risk_reduction: float
    urgency: float
    effort: float
    evidence: list[Evidence] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)

    @property
    def priority_score(self) -> float:
        return (self.expected_value + self.risk_reduction + self.urgency) / max(0.25, self.effort)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["priority_score"] = round(self.priority_score, 5)
        return payload


class EvidenceContext:
    def __init__(self, payload: dict[str, Any]):
        self.payload = payload
        self.now = datetime.now(timezone.utc).isoformat()

    def metric(self, path: str, default: float = 0.0) -> float:
        current: Any = self.payload
        for part in path.split("."):
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        try:
            return float(current)
        except (TypeError, ValueError):
            return default

    def evidence(self, source: str, metric: str, value: Any, weight: float = 1.0) -> Evidence:
        return Evidence(source=source, metric=metric, value=value, observed_at=self.now, weight=weight)


class PolicyEngine:
    """Deterministic policy layer used by all 128 agents.

    The mesh is intentionally evidence-first: an agent cannot emit a high-confidence
    recommendation without measurable evidence. An LLM can later be attached as an
    explanation adapter without moving decision thresholds out of tested policy code.
    """

    def evaluate(self, profile: AgentProfile, context: EvidenceContext) -> list[Recommendation]:
        methods = {
            "sentinel": self._sentinel,
            "forecaster": self._forecaster,
            "optimizer": self._optimizer,
            "reconciler": self._reconciler,
            "contract_guardian": self._contract_guardian,
            "incident_analyst": self._incident_analyst,
            "capacity_planner": self._capacity_planner,
            "portfolio_advisor": self._portfolio_advisor,
        }
        return methods[profile.specialty](profile, context)

    def _make(self, p: AgentProfile, title: str, action: str, rationale: str,
              confidence: float, value: float, risk: float, urgency: float,
              effort: float, evidence: list[Evidence], dependencies: list[str] | None = None) -> Recommendation:
        evidence_weight = min(1.0, sum(max(0.0, e.weight) for e in evidence) / 3.0)
        calibrated = max(0.05, min(0.99, confidence * (0.55 + 0.45 * evidence_weight)))
        return Recommendation(
            agent_id=p.agent_id, department=p.department, title=title, action=action,
            rationale=rationale, confidence=calibrated, expected_value=value,
            risk_reduction=risk, urgency=urgency, effort=effort, evidence=evidence,
            dependencies=dependencies or [],
        )

    def _sentinel(self, p: AgentProfile, c: EvidenceContext) -> list[Recommendation]:
        lag = c.metric("platform.p95_lag_ms")
        quarantine = c.metric("platform.quarantine_rate")
        duplicates = c.metric("platform.duplicate_rate")
        evidence = [c.evidence("platform", "p95_lag_ms", lag), c.evidence("quality", "quarantine_rate", quarantine), c.evidence("quality", "duplicate_rate", duplicates)]
        if lag > 15_000 or quarantine > 0.02:
            return [self._make(p, "Open degradation response", "open_work_item",
                f"Observed lag={lag:.0f}ms and quarantine_rate={quarantine:.3%}; preserve state and isolate the first failing stage.",
                .93, 7, 10, 10, 2, evidence)]
        return [self._make(p, "Maintain current operating posture", "recommend",
            "No monitored reliability threshold is currently breached.", .86, 2, 4, 1, .5, evidence)]

    def _forecaster(self, p: AgentProfile, c: EvidenceContext) -> list[Recommendation]:
        input_rps = c.metric("platform.input_rps")
        processed_rps = c.metric("platform.processed_rps")
        backlog = c.metric("platform.backlog")
        growth = c.metric("business.weekly_growth_rate")
        projected = input_rps * (1 + max(-.5, growth))
        headroom = processed_rps - projected
        evidence = [c.evidence("stream", "input_rps", input_rps), c.evidence("stream", "processed_rps", processed_rps), c.evidence("business", "weekly_growth_rate", growth)]
        if headroom < 0 or backlog > 10_000:
            return [self._make(p, "Increase processing headroom before demand arrives", "simulate_change",
                f"Projected input {projected:.1f} rps exceeds current sustainable headroom; validate partition and sink capacity in the twin first.",
                .89, 8, 8, 8, 3, evidence)]
        return [self._make(p, "Capacity remains inside forecast envelope", "recommend",
            f"Projected input {projected:.1f} rps remains below processing rate {processed_rps:.1f} rps.", .82, 3, 3, 2, .5, evidence)]

    def _optimizer(self, p: AgentProfile, c: EvidenceContext) -> list[Recommendation]:
        cost = c.metric("platform.daily_compute_cost")
        utilization = c.metric("platform.compute_utilization")
        small_files = c.metric("platform.small_file_ratio")
        evidence = [c.evidence("cost", "daily_compute_cost", cost), c.evidence("compute", "utilization", utilization), c.evidence("lakehouse", "small_file_ratio", small_files)]
        opportunities = []
        if utilization < .35 and cost > 0:
            opportunities.append("right-size idle compute")
        if small_files > .25:
            opportunities.append("compact small files and improve write partitioning")
        title = "Reduce unit cost without weakening SLOs" if opportunities else "No material cost optimization detected"
        rationale = "; ".join(opportunities) if opportunities else "Current utilization and file distribution do not cross optimization thresholds."
        return [self._make(p, title, "simulate_change", rationale, .84, min(10, cost / 1000), 3, 4, 2, evidence)]

    def _reconciler(self, p: AgentProfile, c: EvidenceContext) -> list[Recommendation]:
        source = c.metric("reconciliation.source_count")
        target = c.metric("reconciliation.target_count")
        quarantine = c.metric("reconciliation.quarantine_count")
        duplicate = c.metric("reconciliation.duplicate_count")
        delta = source - target - quarantine - duplicate
        evidence = [c.evidence("reconciliation", "source_count", source), c.evidence("reconciliation", "target_count", target), c.evidence("reconciliation", "unexplained_delta", delta, 1.5)]
        if abs(delta) > 0:
            return [self._make(p, "Investigate unexplained reconciliation delta", "open_work_item",
                f"source - target - quarantine - duplicate = {delta:.0f}; no unexplained row loss is acceptable for this contract.", .98, 9, 10, 10, 2, evidence)]
        return [self._make(p, "Reconciliation balanced", "recommend", "All source records are explained by canonical output, quarantine, or intentional deduplication.", .98, 2, 8, 1, .25, evidence)]

    def _contract_guardian(self, p: AgentProfile, c: EvidenceContext) -> list[Recommendation]:
        breaking = c.metric("contracts.breaking_changes")
        impacted = c.metric("contracts.impacted_assets")
        max_risk = c.metric("contracts.max_blast_radius_risk")
        evidence = [c.evidence("contracts", "breaking_changes", breaking, 1.5), c.evidence("lineage", "impacted_assets", impacted), c.evidence("twin", "max_blast_radius_risk", max_risk)]
        if breaking or max_risk >= .5:
            return [self._make(p, "Block incompatible contract promotion", "propose_test",
                f"Detected {breaking:.0f} breaking change(s) affecting {impacted:.0f} downstream assets; require consumer replay and explicit compatibility approval.", .97, 8, 10, 10, 2, evidence)]
        return [self._make(p, "Contract promotion is compatible", "recommend", "No breaking schema, grain, key, or classification change detected.", .92, 4, 7, 2, .5, evidence)]

    def _incident_analyst(self, p: AgentProfile, c: EvidenceContext) -> list[Recommendation]:
        error_rate = c.metric("platform.error_rate")
        lag = c.metric("platform.p95_lag_ms")
        sink_ms = c.metric("platform.sink_p95_ms")
        evidence = [c.evidence("platform", "error_rate", error_rate), c.evidence("stream", "p95_lag_ms", lag), c.evidence("sink", "p95_ms", sink_ms)]
        if error_rate > .01 or lag > 30_000:
            likely = "sink pressure" if sink_ms > 5_000 else "processing/shuffle pressure"
            return [self._make(p, "Preserve state and isolate the bottleneck", "propose_backfill",
                f"Telemetry points first to {likely}; preserve raw data and checkpoints before mitigation, then replay and reconcile.", .88, 7, 10, 10, 2.5, evidence)]
        return [self._make(p, "No incident signature detected", "recommend", "Current error and lag signals remain below incident thresholds.", .79, 1, 3, 1, .5, evidence)]

    def _capacity_planner(self, p: AgentProfile, c: EvidenceContext) -> list[Recommendation]:
        skew = c.metric("spark.max_partition_to_median_ratio")
        state_rows = c.metric("spark.state_rows")
        batch_ms = c.metric("spark.batch_duration_ms")
        trigger_ms = c.metric("spark.trigger_interval_ms", 5000)
        evidence = [c.evidence("spark", "max_partition_to_median_ratio", skew), c.evidence("spark", "state_rows", state_rows), c.evidence("spark", "batch_duration_ms", batch_ms)]
        if skew > 8:
            return [self._make(p, "Remove hot-key capacity bottleneck", "simulate_change", f"Maximum partition is {skew:.1f}x median; test salting, pre-aggregation, or key redesign before adding compute.", .91, 7, 8, 8, 3, evidence)]
        if batch_ms > trigger_ms:
            return [self._make(p, "Restore streaming processing headroom", "simulate_change", "Micro-batch duration exceeds trigger interval; tune partitions/join/state/sink before scaling blindly.", .9, 8, 8, 9, 3, evidence)]
        return [self._make(p, "Streaming capacity is within envelope", "recommend", "Skew and batch duration remain within configured thresholds.", .8, 2, 3, 1, .5, evidence)]

    def _portfolio_advisor(self, p: AgentProfile, c: EvidenceContext) -> list[Recommendation]:
        backlog = c.payload.get("work_items", [])
        ranked = []
        for item in backlog:
            effort = max(.25, float(item.get("effort_score", 1)))
            score = (float(item.get("business_value", 0)) + float(item.get("risk_reduction", 0)) + float(item.get("urgency_score", 0))) / effort
            ranked.append((score, item))
        ranked.sort(key=lambda x: x[0], reverse=True)
        if not ranked:
            return [self._make(p, "No work items available for prioritization", "recommend", "The current context has no backlog records.", .7, 0, 0, 0, .25, [])]
        score, top = ranked[0]
        evidence = [c.evidence("work_queue", "candidate_count", len(ranked)), c.evidence("work_queue", "top_priority_score", score)]
        return [self._make(p, f"Prioritize {top.get('work_key', 'top work item')}", "prioritize",
            f"Highest risk-adjusted value-to-effort score in the current queue: {score:.2f}.", .88,
            float(top.get("business_value", 0)), float(top.get("risk_reduction", 0)), float(top.get("urgency_score", 0)), float(top.get("effort_score", 1)), evidence)]


class AgentMesh:
    def __init__(self, policy: PolicyEngine | None = None):
        self.policy = policy or PolicyEngine()

    def run(self, context_payload: dict[str, Any], agent_ids: Iterable[str] | None = None,
            departments: Iterable[str] = (), specialties: Iterable[str] = ()) -> list[Recommendation]:
        if agent_ids is None:
            profiles = select_agents(specialties=specialties, departments=departments)
        else:
            profiles = [REGISTRY_BY_ID[agent_id] for agent_id in agent_ids]
        context = EvidenceContext(context_payload)
        recommendations = [rec for profile in profiles for rec in self.policy.evaluate(profile, context)]
        recommendations.sort(key=lambda r: (r.priority_score * r.confidence), reverse=True)
        return recommendations

    def consensus(self, context_payload: dict[str, Any], departments: Iterable[str]) -> dict[str, Any]:
        recommendations = self.run(context_payload, departments=departments)
        if not recommendations:
            return {"recommendations": [], "consensus_score": 0.0}
        top = recommendations[: min(20, len(recommendations))]
        score = sum(r.priority_score * r.confidence for r in top) / len(top)
        return {
            "recommendations": [r.to_dict() for r in top],
            "consensus_score": round(score, 5),
            "participating_agents": len(recommendations),
        }
