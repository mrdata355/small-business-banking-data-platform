from agents.orchestrator import AgentMesh
from agents.registry import REGISTRY, REGISTRY_BY_ID


def test_registry_contains_128_executable_profiles():
    assert len(REGISTRY) == 128
    assert len(REGISTRY_BY_ID) == 128
    assert {a.specialty for a in REGISTRY} == {
        'sentinel', 'forecaster', 'optimizer', 'reconciler', 'contract_guardian',
        'incident_analyst', 'capacity_planner', 'portfolio_advisor'
    }


def test_reconciler_escalates_unexplained_delta():
    context = {
        'reconciliation': {
            'source_count': 100,
            'target_count': 94,
            'quarantine_count': 2,
            'duplicate_count': 1,
        }
    }
    mesh = AgentMesh()
    recs = mesh.run(context, agent_ids=['data_platform_reconciler'])
    assert len(recs) == 1
    assert 'unexplained reconciliation delta' in recs[0].title.lower()
    assert recs[0].priority_score > 5


def test_portfolio_advisor_ranks_value_risk_urgency_over_effort():
    context = {
        'work_items': [
            {'work_key': 'LOW-1', 'business_value': 3, 'risk_reduction': 1, 'urgency_score': 1, 'effort_score': 8},
            {'work_key': 'HIGH-1', 'business_value': 8, 'risk_reduction': 9, 'urgency_score': 9, 'effort_score': 2},
        ]
    }
    mesh = AgentMesh()
    rec = mesh.run(context, agent_ids=['operations_portfolio_advisor'])[0]
    assert 'HIGH-1' in rec.title
