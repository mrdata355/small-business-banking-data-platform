from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable


@dataclass(frozen=True)
class Exposure:
    exposure_id: str
    business_id: str
    industry_code: str
    geography_code: str
    product_code: str
    committed_amount: Decimal
    outstanding_amount: Decimal
    probability_of_default: Decimal
    loss_given_default: Decimal
    exposure_at_default_factor: Decimal = Decimal("1")

    @property
    def exposure_at_default(self) -> Decimal:
        return self.outstanding_amount * self.exposure_at_default_factor

    @property
    def expected_loss(self) -> Decimal:
        return self.exposure_at_default * self.probability_of_default * self.loss_given_default


@dataclass(frozen=True)
class ConcentrationResult:
    dimension: str
    key: str
    exposure_at_default: Decimal
    expected_loss: Decimal
    share_of_portfolio: Decimal
    exposure_count: int


class ExposureAnalytics:
    def __init__(self, exposures: Iterable[Exposure]) -> None:
        self.exposures = tuple(exposures)
        self.total_ead = sum((e.exposure_at_default for e in self.exposures), Decimal("0"))
        self.total_expected_loss = sum(
            (e.expected_loss for e in self.exposures), Decimal("0")
        )

    def concentration(self, dimension: str) -> list[ConcentrationResult]:
        allowed = {
            "industry": lambda e: e.industry_code,
            "geography": lambda e: e.geography_code,
            "product": lambda e: e.product_code,
            "business": lambda e: e.business_id,
        }
        if dimension not in allowed:
            raise ValueError(f"unsupported concentration dimension: {dimension}")
        key_fn = allowed[dimension]
        buckets: dict[str, list[Exposure]] = defaultdict(list)
        for exposure in self.exposures:
            buckets[key_fn(exposure)].append(exposure)

        rows: list[ConcentrationResult] = []
        for key, items in buckets.items():
            ead = sum((item.exposure_at_default for item in items), Decimal("0"))
            expected_loss = sum((item.expected_loss for item in items), Decimal("0"))
            share = ead / self.total_ead if self.total_ead else Decimal("0")
            rows.append(
                ConcentrationResult(
                    dimension=dimension,
                    key=key,
                    exposure_at_default=ead,
                    expected_loss=expected_loss,
                    share_of_portfolio=share,
                    exposure_count=len(items),
                )
            )
        return sorted(rows, key=lambda row: row.exposure_at_default, reverse=True)

    def top_concentrations(
        self,
        dimension: str,
        limit: int = 10,
        minimum_share: Decimal = Decimal("0"),
    ) -> list[ConcentrationResult]:
        if limit <= 0:
            return []
        return [
            row
            for row in self.concentration(dimension)
            if row.share_of_portfolio >= minimum_share
        ][:limit]

    def stress(
        self,
        pd_multiplier: Decimal,
        lgd_additive: Decimal = Decimal("0"),
    ) -> dict:
        if pd_multiplier < 0:
            raise ValueError("pd_multiplier cannot be negative")
        stressed_loss = Decimal("0")
        for exposure in self.exposures:
            stressed_pd = min(Decimal("1"), exposure.probability_of_default * pd_multiplier)
            stressed_lgd = min(
                Decimal("1"), max(Decimal("0"), exposure.loss_given_default + lgd_additive)
            )
            stressed_loss += exposure.exposure_at_default * stressed_pd * stressed_lgd
        incremental_loss = stressed_loss - self.total_expected_loss
        return {
            "baseline_expected_loss": self.total_expected_loss,
            "stressed_expected_loss": stressed_loss,
            "incremental_expected_loss": incremental_loss,
            "stress_multiple": (
                stressed_loss / self.total_expected_loss
                if self.total_expected_loss
                else Decimal("0")
            ),
        }

    def limits(self, concentration_limits: dict[str, Decimal]) -> list[dict]:
        findings: list[dict] = []
        for dimension, threshold in concentration_limits.items():
            for row in self.concentration(dimension):
                if row.share_of_portfolio > threshold:
                    findings.append(
                        {
                            "dimension": dimension,
                            "key": row.key,
                            "share": row.share_of_portfolio,
                            "threshold": threshold,
                            "excess": row.share_of_portfolio - threshold,
                            "exposure_at_default": row.exposure_at_default,
                            "severity": "BREACH",
                        }
                    )
        return sorted(findings, key=lambda row: row["excess"], reverse=True)
