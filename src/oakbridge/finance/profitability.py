from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable


MONEY = Decimal("0.01")
RATE = Decimal("0.0000001")


def _d(value: Decimal | int | float | str) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def money(value: Decimal | int | float | str) -> Decimal:
    return _d(value).quantize(MONEY, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class ProductEconomics:
    product_code: str
    average_balance: Decimal
    contractual_rate: Decimal
    transfer_price_rate: Decimal
    servicing_cost: Decimal
    expected_loss_rate: Decimal
    capital_rate: Decimal
    capital_charge_rate: Decimal
    fee_income: Decimal = Decimal("0")
    direct_operating_cost: Decimal = Decimal("0")


@dataclass(frozen=True)
class ProfitabilityResult:
    product_code: str
    interest_income: Decimal
    funds_transfer_charge: Decimal
    net_interest_income: Decimal
    fee_income: Decimal
    expected_credit_loss: Decimal
    servicing_cost: Decimal
    direct_operating_cost: Decimal
    allocated_capital: Decimal
    capital_charge: Decimal
    risk_adjusted_contribution: Decimal
    risk_adjusted_return_on_capital: Decimal


class ProfitabilityEngine:
    """Deterministic unit-economics engine for generated banking data products.

    The engine keeps transfer pricing, expected loss, servicing expense and capital
    attribution explicit so management metrics can be reconciled to their components.
    It is intentionally policy-driven rather than embedding any real bank assumptions.
    """

    def __init__(self, annualization_days: int = 365) -> None:
        if annualization_days <= 0:
            raise ValueError("annualization_days must be positive")
        self.annualization_days = Decimal(annualization_days)

    def evaluate(self, economics: ProductEconomics, days: int = 30) -> ProfitabilityResult:
        if days <= 0:
            raise ValueError("days must be positive")
        balance = _d(economics.average_balance)
        if balance < 0:
            raise ValueError("average_balance cannot be negative")

        period = Decimal(days) / self.annualization_days
        interest_income = money(balance * _d(economics.contractual_rate) * period)
        transfer_charge = money(balance * _d(economics.transfer_price_rate) * period)
        net_interest_income = money(interest_income - transfer_charge)
        expected_loss = money(balance * _d(economics.expected_loss_rate) * period)
        allocated_capital = money(balance * _d(economics.capital_rate))
        capital_charge = money(
            allocated_capital * _d(economics.capital_charge_rate) * period
        )
        fee_income = money(economics.fee_income)
        servicing_cost = money(economics.servicing_cost)
        direct_cost = money(economics.direct_operating_cost)
        contribution = money(
            net_interest_income
            + fee_income
            - expected_loss
            - servicing_cost
            - direct_cost
            - capital_charge
        )
        if allocated_capital == 0:
            raroc = Decimal("0")
        else:
            annualized_contribution = contribution / period
            raroc = (annualized_contribution / allocated_capital).quantize(RATE)

        return ProfitabilityResult(
            product_code=economics.product_code,
            interest_income=interest_income,
            funds_transfer_charge=transfer_charge,
            net_interest_income=net_interest_income,
            fee_income=fee_income,
            expected_credit_loss=expected_loss,
            servicing_cost=servicing_cost,
            direct_operating_cost=direct_cost,
            allocated_capital=allocated_capital,
            capital_charge=capital_charge,
            risk_adjusted_contribution=contribution,
            risk_adjusted_return_on_capital=raroc,
        )

    def portfolio(self, products: Iterable[ProductEconomics], days: int = 30) -> dict:
        rows = [self.evaluate(product, days=days) for product in products]
        totals = {
            "interest_income": sum((r.interest_income for r in rows), Decimal("0")),
            "funds_transfer_charge": sum(
                (r.funds_transfer_charge for r in rows), Decimal("0")
            ),
            "net_interest_income": sum((r.net_interest_income for r in rows), Decimal("0")),
            "fee_income": sum((r.fee_income for r in rows), Decimal("0")),
            "expected_credit_loss": sum(
                (r.expected_credit_loss for r in rows), Decimal("0")
            ),
            "servicing_cost": sum((r.servicing_cost for r in rows), Decimal("0")),
            "direct_operating_cost": sum(
                (r.direct_operating_cost for r in rows), Decimal("0")
            ),
            "allocated_capital": sum((r.allocated_capital for r in rows), Decimal("0")),
            "capital_charge": sum((r.capital_charge for r in rows), Decimal("0")),
            "risk_adjusted_contribution": sum(
                (r.risk_adjusted_contribution for r in rows), Decimal("0")
            ),
        }
        capital = totals["allocated_capital"]
        totals["portfolio_raroc_proxy"] = (
            (totals["risk_adjusted_contribution"] * Decimal("12") / capital).quantize(RATE)
            if capital
            else Decimal("0")
        )
        return {"products": rows, "totals": totals}
