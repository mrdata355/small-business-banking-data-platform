from dataclasses import replace

from digital_twin.contract_genome import ContractChange, default_contract_graph
from digital_twin.twin import BankingDigitalTwin, TwinPolicy, compare_policies


def test_twin_is_deterministic_for_same_seed():
    a = BankingDigitalTwin(seed=99)
    a.seed_applications(50)
    ra = a.run()

    b = BankingDigitalTwin(seed=99)
    b.seed_applications(50)
    rb = b.run()

    assert ra.approved == rb.approved
    assert ra.funded == rb.funded
    assert ra.p95_time_to_decision_minutes == rb.p95_time_to_decision_minutes


def test_faster_document_policy_improves_decision_cycle_time():
    baseline = TwinPolicy(document_minutes_p50=60, financial_package_minutes_p50=120)
    candidate = TwinPolicy(document_minutes_p50=20, financial_package_minutes_p50=45)
    result = compare_policies(baseline, candidate, applications=150, seeds=range(3))
    assert (
        result["median_time_to_decision_minutes"]["candidate"]
        < result["median_time_to_decision_minutes"]["baseline"]
    )


def test_contract_genome_flags_business_key_change_and_lineage_blast_radius():
    graph = default_contract_graph()
    previous = graph.contracts["silver_lending.loan_application"]
    proposed = replace(
        previous,
        version="2.0.0",
        business_keys=("application_id", "event_version"),
    )
    blast = graph.evaluate(ContractChange(previous.asset, previous, proposed))
    assert blast.compatibility == "BREAKING"
    assert blast.estimated_risk >= 0.5
    assert "gold_lending.underwriting_readiness_queue" in blast.transitively_impacted
