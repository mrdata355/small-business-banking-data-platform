from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelScorecard:
    version: str
    roc_auc: float
    precision: float
    recall: float
    brier_score: float
    inference_p95_ms: float
    drift_psi: float
    fairness_gap: float
    cost_per_1000: float


@dataclass(frozen=True)
class PromotionDecision:
    promote: bool
    score_delta: float
    reasons: tuple[str, ...]
    required_actions: tuple[str, ...]


def utility(s: ModelScorecard) -> float:
    predictive = .28 * s.roc_auc + .18 * s.precision + .18 * s.recall + .12 * (1 - min(1, s.brier_score))
    operational = .08 * max(0, 1 - s.inference_p95_ms / 1000) + .06 * max(0, 1 - s.cost_per_1000 / 10)
    controls = .05 * max(0, 1 - s.drift_psi / .25) + .05 * max(0, 1 - s.fairness_gap / .10)
    return predictive + operational + controls


def evaluate(champion: ModelScorecard, challenger: ModelScorecard) -> PromotionDecision:
    reasons: list[str] = []
    actions: list[str] = []
    hard_block = False

    if challenger.drift_psi >= .25:
        hard_block = True; reasons.append("challenger input drift exceeds severe PSI threshold"); actions.append("refresh training population and rerun drift report")
    if challenger.fairness_gap >= .10:
        hard_block = True; reasons.append("challenger fairness gap exceeds policy threshold"); actions.append("run segment error analysis and mitigation review")
    if challenger.inference_p95_ms > max(1000, champion.inference_p95_ms * 2):
        hard_block = True; reasons.append("challenger latency breaches serving guardrail"); actions.append("profile serving path or reduce feature/model complexity")

    delta = utility(challenger) - utility(champion)
    if delta <= 0.005:
        reasons.append(f"risk-adjusted utility improvement {delta:.4f} is below promotion threshold")
        actions.append("retain champion and continue shadow evaluation")

    promote = not hard_block and delta > 0.005
    if promote:
        reasons.append(f"challenger improves risk-adjusted utility by {delta:.4f}")
        actions += ["run shadow traffic", "verify rollback artifact", "promote after approval gate"]

    return PromotionDecision(promote, delta, tuple(dict.fromkeys(reasons)), tuple(dict.fromkeys(actions)))
