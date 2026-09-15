from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from digital_twin.twin import TwinPolicy, compare_policies


@dataclass(frozen=True)
class StakeholderUtility:
    name: str
    cycle_time_weight: float
    funding_weight: float
    contact_weight: float
    reliability_weight: float


@dataclass(frozen=True)
class ChangeProposal:
    proposal_id: str
    title: str
    baseline_policy: TwinPolicy
    candidate_policy: TwinPolicy
    estimated_monthly_cost_delta: float
    reliability_risk_delta: float


STAKEHOLDERS = (
    StakeholderUtility("customer", 1.0, .8, .9, .8),
    StakeholderUtility("lending_operations", 1.0, .7, .5, .9),
    StakeholderUtility("risk", .3, .4, .2, 1.0),
    StakeholderUtility("finance", .4, .8, .2, .7),
    StakeholderUtility("shareholder", .4, 1.0, .2, .8),
    StakeholderUtility("data_platform", .2, .2, .1, 1.0),
)


def evaluate_change(proposal: ChangeProposal, applications: int = 500, seeds: Iterable[int] = range(5)) -> dict:
    comparison = compare_policies(proposal.baseline_policy, proposal.candidate_policy, applications=applications, seeds=seeds)
    cycle_delta = comparison["median_time_to_decision_minutes"]["delta"]
    funding_delta = comparison["funded_rate"]["delta"]
    contact_delta = comparison["customer_contacts"]["delta"]

    utilities = []
    for s in STAKEHOLDERS:
        benefit = (
            (-cycle_delta / 60) * s.cycle_time_weight
            + (funding_delta * 100) * s.funding_weight
            + (-contact_delta / max(1, applications)) * 10 * s.contact_weight
            + (-proposal.reliability_risk_delta * 10) * s.reliability_weight
        )
        utilities.append({"stakeholder": s.name, "utility_delta": round(benefit, 6)})

    min_utility = min(x["utility_delta"] for x in utilities)
    avg_utility = sum(x["utility_delta"] for x in utilities) / len(utilities)
    cost_penalty = proposal.estimated_monthly_cost_delta / 10_000
    decision_score = avg_utility - cost_penalty
    return {
        "proposal_id": proposal.proposal_id,
        "title": proposal.title,
        "comparison": comparison,
        "stakeholder_utilities": utilities,
        "minimum_stakeholder_utility": min_utility,
        "average_stakeholder_utility": round(avg_utility, 6),
        "estimated_monthly_cost_delta": proposal.estimated_monthly_cost_delta,
        "decision_score": round(decision_score, 6),
        "governance_decision": "REJECT" if min_utility < -2 else "REVIEW" if decision_score <= 0 else "ADVANCE_TO_CANARY",
    }
