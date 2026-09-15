# Counterfactual banking digital twin

The twin is an event-driven simulation of generated small-business banking workflows. It is designed to answer a different question from a dashboard: **what is likely to happen if the operating policy or data platform changes?**

## Components

- `digital_twin/twin.py` — deterministic discrete-event banking workflow simulation.
- `digital_twin/contract_genome.py` — contract identity, compatibility and lineage blast-radius analysis.
- `digital_twin/shadow_governor.py` — paired-scenario stakeholder utility and promotion gate.
- `site/twin.html` — interactive browser scenario runner.

## Counterfactual replay

A baseline and candidate policy are evaluated with identical random seeds. That paired design reduces noise when comparing changes such as:

- faster document processing,
- different identity-verification latency,
- changes in financial-package cycle time,
- processing incidents,
- changed underwriting service time,
- changed funding service time.

The output reports approval/funding rates, median and p95 decision cycle time, funding cycle time, customer-contact pressure and platform degradation signals.

## Contract Genome

A data contract is represented by:

```text
asset + version + grain + business keys + fields/types/nullability
+ freshness SLO + owner + classification + lineage + quality rules
```

The canonical representation is hashed to a deterministic genome. A proposed change is compared with the deployed contract for:

- grain changes,
- business-key changes,
- removed fields,
- type changes,
- tightened nullability,
- new required fields,
- classification changes,
- freshness-policy changes.

The lineage graph then calculates direct and transitive impact paths. Critical paths to Gold, risk, finance, management and model assets increase the change-risk score.

## Shadow Governor

The Shadow Governor combines paired simulation results with stakeholder utility functions for customers, lending operations, risk, finance, shareholders and the data platform. It does not automatically change production. It produces one of:

- `ADVANCE_TO_CANARY`
- `REVIEW`
- `REJECT`

This creates a pre-production decision record connecting the proposed change, measured counterfactual effect, estimated cost and affected stakeholder objectives.
