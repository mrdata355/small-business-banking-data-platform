from decimal import Decimal

from oakbridge.reconciliation.engine import (
    ControlTotals,
    ReconciliationBucket,
    ReconciliationEngine,
    ReconciliationStatus,
)


def test_reconciliation_balances_when_all_source_rows_are_explained():
    engine = ReconciliationEngine()
    result = engine.reconcile(
        ControlTotals(row_count=100, amount_sum=Decimal("1000")),
        ControlTotals(row_count=96, amount_sum=Decimal("960")),
        [
            ReconciliationBucket("duplicate_delivery", 2, Decimal("20")),
            ReconciliationBucket("quarantine", 2, Decimal("20")),
        ],
    )
    assert result.status == ReconciliationStatus.BALANCED
    assert result.unexplained_rows == 0
    assert result.unexplained_amount == Decimal("0")


def test_unexplained_loss_fails_control():
    engine = ReconciliationEngine()
    result = engine.reconcile(
        ControlTotals(row_count=100, amount_sum=Decimal("1000")),
        ControlTotals(row_count=98, amount_sum=Decimal("990")),
    )
    assert result.status == ReconciliationStatus.FAILED
    assert result.unexplained_rows == 2
    assert result.unexplained_amount == Decimal("10")
