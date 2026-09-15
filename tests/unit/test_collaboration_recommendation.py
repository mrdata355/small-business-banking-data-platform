from collaboration.recommendation_engine import WorkItem, default_engine


def test_data_platform_ranks_high_value_high_risk_low_effort_first():
    engine = default_engine()
    items = [
        WorkItem('OB-LOW','Minor cleanup','DATA_PLATFORM','PRODUCT','READY','P3',2,1,1,6),
        WorkItem('OB-HIGH','Restore reconciliation','DATA_PLATFORM','FINANCE','READY','P0',9,10,10,2),
    ]
    ranked = engine.rank_for_department('DATA_PLATFORM', items, {'reconciliation_delta': 5})
    assert ranked[0].work_item.work_key == 'OB-HIGH'
    assert ranked[0].next_action == 'START'


def test_blocked_item_is_recommended_for_unblocking_not_starting():
    engine = default_engine()
    item = WorkItem('OB-BLOCK','Blocked task','LENDING','RISK','BLOCKED','P1',9,9,8,3,blocked_by=('OB-DEP',))
    ranked = engine.rank_for_department('LENDING', [item])
    assert ranked[0].next_action == 'UNBLOCK'
