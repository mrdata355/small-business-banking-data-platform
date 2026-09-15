from __future__ import annotations

import hashlib
import json
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class DataContract:
    asset: str
    version: str
    grain: str
    business_keys: tuple[str, ...]
    fields: tuple[tuple[str, str, bool], ...]
    freshness_slo_seconds: int
    owner: str
    classification: str
    upstream: tuple[str, ...] = ()
    downstream: tuple[str, ...] = ()
    quality_rules: tuple[str, ...] = ()

    def canonical_payload(self) -> dict:
        return {
            "asset": self.asset,
            "version": self.version,
            "grain": self.grain,
            "business_keys": sorted(self.business_keys),
            "fields": sorted(self.fields),
            "freshness_slo_seconds": self.freshness_slo_seconds,
            "owner": self.owner,
            "classification": self.classification,
            "upstream": sorted(self.upstream),
            "downstream": sorted(self.downstream),
            "quality_rules": sorted(self.quality_rules),
        }

    @property
    def genome(self) -> str:
        payload = json.dumps(self.canonical_payload(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()


@dataclass(frozen=True)
class ContractChange:
    asset: str
    previous: DataContract
    proposed: DataContract


@dataclass
class BlastRadius:
    changed_asset: str
    compatibility: str
    reasons: list[str] = field(default_factory=list)
    directly_impacted: list[str] = field(default_factory=list)
    transitively_impacted: list[str] = field(default_factory=list)
    critical_paths: list[list[str]] = field(default_factory=list)
    estimated_risk: float = 0.0


class ContractGenomeGraph:
    """Lineage graph that scores data-contract changes before deployment.

    The genome is a content hash of grain, keys, schema, SLO, ownership and quality
    policy. Counterfactual changes can be evaluated without mutating production state.
    """

    def __init__(self, contracts: Iterable[DataContract]):
        self.contracts = {c.asset: c for c in contracts}
        self.edges: dict[str, set[str]] = defaultdict(set)
        for contract in self.contracts.values():
            for downstream in contract.downstream:
                self.edges[contract.asset].add(downstream)
            for upstream in contract.upstream:
                self.edges[upstream].add(contract.asset)

    @staticmethod
    def classify(previous: DataContract, proposed: DataContract) -> tuple[str, list[str], float]:
        reasons: list[str] = []
        risk = 0.0
        old_fields = {name: (dtype, nullable) for name, dtype, nullable in previous.fields}
        new_fields = {name: (dtype, nullable) for name, dtype, nullable in proposed.fields}

        removed = sorted(set(old_fields) - set(new_fields))
        type_changes = sorted(name for name in set(old_fields) & set(new_fields) if old_fields[name][0] != new_fields[name][0])
        tightened_nullability = sorted(name for name in set(old_fields) & set(new_fields) if old_fields[name][1] and not new_fields[name][1])
        added_required = sorted(name for name in set(new_fields) - set(old_fields) if not new_fields[name][1])

        if previous.grain != proposed.grain:
            reasons.append(f"grain changed: {previous.grain} -> {proposed.grain}")
            risk += 0.45
        if previous.business_keys != proposed.business_keys:
            reasons.append("business key changed")
            risk += 0.45
        if removed:
            reasons.append(f"removed fields: {', '.join(removed)}")
            risk += min(0.35, 0.08 * len(removed))
        if type_changes:
            reasons.append(f"type changes: {', '.join(type_changes)}")
            risk += min(0.35, 0.1 * len(type_changes))
        if tightened_nullability:
            reasons.append(f"nullability tightened: {', '.join(tightened_nullability)}")
            risk += min(0.2, 0.05 * len(tightened_nullability))
        if added_required:
            reasons.append(f"new required fields: {', '.join(added_required)}")
            risk += min(0.25, 0.06 * len(added_required))
        if proposed.freshness_slo_seconds < previous.freshness_slo_seconds:
            reasons.append("freshness SLO tightened")
            risk += 0.08
        if proposed.classification != previous.classification:
            reasons.append(f"classification changed: {previous.classification} -> {proposed.classification}")
            risk += 0.18

        risk = min(1.0, risk)
        if risk >= 0.5:
            return "BREAKING", reasons, risk
        if risk > 0:
            return "REVIEW_REQUIRED", reasons, risk
        return "BACKWARD_COMPATIBLE", reasons, risk

    def descendants(self, asset: str) -> list[str]:
        visited: set[str] = set()
        queue = deque(self.edges.get(asset, ()))
        while queue:
            node = queue.popleft()
            if node in visited:
                continue
            visited.add(node)
            queue.extend(self.edges.get(node, ()))
        return sorted(visited)

    def _paths(self, source: str, targets: set[str], limit: int = 25) -> list[list[str]]:
        result: list[list[str]] = []
        queue: deque[list[str]] = deque([[source]])
        while queue and len(result) < limit:
            path = queue.popleft()
            node = path[-1]
            if node in targets and node != source:
                result.append(path)
            for nxt in sorted(self.edges.get(node, ())):
                if nxt not in path:
                    queue.append(path + [nxt])
        return result

    def evaluate(self, change: ContractChange) -> BlastRadius:
        compatibility, reasons, base_risk = self.classify(change.previous, change.proposed)
        direct = sorted(self.edges.get(change.asset, ()))
        transitive = self.descendants(change.asset)
        critical_targets = {
            asset for asset in transitive
            if any(token in asset.lower() for token in ("gold", "underwriting", "risk", "finance", "regulatory", "shareholder"))
        }
        paths = self._paths(change.asset, critical_targets)
        amplification = min(0.35, len(transitive) * 0.015 + len(paths) * 0.025)
        return BlastRadius(
            changed_asset=change.asset,
            compatibility=compatibility,
            reasons=reasons,
            directly_impacted=direct,
            transitively_impacted=transitive,
            critical_paths=paths,
            estimated_risk=min(1.0, base_risk + amplification),
        )


def default_contract_graph() -> ContractGenomeGraph:
    contracts = [
        DataContract(
            asset="bronze_lending.loan_application_event_raw", version="1.0.0",
            grain="one row per delivered application event", business_keys=("event_id",),
            fields=(("event_id","string",False),("application_id","string",False),("event_version","long",False),("event_ts","timestamp",False),("application_status","string",False)),
            freshness_slo_seconds=120, owner="data-platform", classification="CONFIDENTIAL",
            downstream=("silver_lending.loan_application_status_history","silver_lending.loan_application"),
            quality_rules=("event_id_not_null","event_version_positive","status_domain"),
        ),
        DataContract(
            asset="silver_lending.loan_application_status_history", version="1.0.0",
            grain="one row per accepted business event", business_keys=("event_id",),
            fields=(("event_id","string",False),("application_id","string",False),("event_version","long",False),("event_ts","timestamp",False)),
            freshness_slo_seconds=150, owner="lending-data", classification="CONFIDENTIAL",
            upstream=("bronze_lending.loan_application_event_raw",), downstream=("ops.pipeline_reconciliation",),
        ),
        DataContract(
            asset="silver_lending.loan_application", version="1.0.0",
            grain="one current row per application", business_keys=("application_id",),
            fields=(("application_id","string",False),("event_version","long",False),("application_status","string",False),("ready_for_underwriting","boolean",False)),
            freshness_slo_seconds=180, owner="lending-data", classification="CONFIDENTIAL",
            upstream=("bronze_lending.loan_application_event_raw",), downstream=("gold_lending.underwriting_readiness_queue","feature_store.application_risk_features"),
        ),
        DataContract(
            asset="gold_lending.underwriting_readiness_queue", version="1.0.0",
            grain="one current row per application meeting readiness rules", business_keys=("application_id",),
            fields=(("application_id","string",False),("ready_for_underwriting","boolean",False)),
            freshness_slo_seconds=240, owner="lending-operations", classification="CONFIDENTIAL",
            upstream=("silver_lending.loan_application",), downstream=("shareholder.lending_funnel_kpi",),
        ),
        DataContract(
            asset="feature_store.application_risk_features", version="1.0.0",
            grain="one feature vector per application scoring timestamp", business_keys=("application_id","feature_ts"),
            fields=(("application_id","string",False),("feature_ts","timestamp",False),("missing_document_count","int",False)),
            freshness_slo_seconds=300, owner="data-science", classification="CONFIDENTIAL",
            upstream=("silver_lending.loan_application",), downstream=("ml.application_operational_risk"),
        ),
        DataContract(
            asset="ml.application_operational_risk", version="1.0.0",
            grain="one model prediction per application score", business_keys=("prediction_id",),
            fields=(("prediction_id","string",False),("application_id","string",False),("risk_probability","double",False)),
            freshness_slo_seconds=360, owner="ml-platform", classification="CONFIDENTIAL",
            upstream=("feature_store.application_risk_features",), downstream=("risk.application_monitoring",),
        ),
        DataContract(
            asset="ops.pipeline_reconciliation", version="1.0.0",
            grain="one reconciliation record per pipeline run", business_keys=("run_id",),
            fields=(("run_id","string",False),("balanced","boolean",False)), freshness_slo_seconds=3600,
            owner="data-platform", classification="INTERNAL", upstream=("silver_lending.loan_application_status_history",),
        ),
        DataContract(
            asset="shareholder.lending_funnel_kpi", version="1.0.0", grain="one metric row per date/product/industry",
            business_keys=("date_key","product_key","industry_key"), fields=(("metric_value","decimal",False),),
            freshness_slo_seconds=86400, owner="finance-analytics", classification="INTERNAL",
            upstream=("gold_lending.underwriting_readiness_queue",),
        ),
    ]
    return ContractGenomeGraph(contracts)
