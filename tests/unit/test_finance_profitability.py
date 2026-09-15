from decimal import Decimal

from oakbridge.finance.profitability import ProductEconomics, ProfitabilityEngine


def test_profitability_components_reconcile():
    engine = ProfitabilityEngine()
    result = engine.evaluate(
        ProductEconomics(
            product_code="GENERATED_LOAN",
            average_balance=Decimal("1000000"),
            contractual_rate=Decimal("0.08"),
            transfer_price_rate=Decimal("0.04"),
            servicing_cost=Decimal("500"),
            expected_loss_rate=Decimal("0.012"),
            capital_rate=Decimal("0.08"),
            capital_charge_rate=Decimal("0.10"),
            fee_income=Decimal("1000"),
            direct_operating_cost=Decimal("250"),
        ),
        days=30,
    )
    expected = (
        result.net_interest_income
        + result.fee_income
        - result.expected_credit_loss
        - result.servicing_cost
        - result.direct_operating_cost
        - result.capital_charge
    )
    assert result.risk_adjusted_contribution == expected
    assert result.allocated_capital == Decimal("80000.00")


def test_portfolio_totals_equal_product_results():
    engine = ProfitabilityEngine()
    products = [
        ProductEconomics(
            product_code=f"P{i}",
            average_balance=Decimal("250000"),
            contractual_rate=Decimal("0.075"),
            transfer_price_rate=Decimal("0.035"),
            servicing_cost=Decimal("100"),
            expected_loss_rate=Decimal("0.01"),
            capital_rate=Decimal("0.08"),
            capital_charge_rate=Decimal("0.09"),
        )
        for i in range(3)
    ]
    result = engine.portfolio(products)
    assert len(result["products"]) == 3
    assert result["totals"]["allocated_capital"] == Decimal("60000.00")
