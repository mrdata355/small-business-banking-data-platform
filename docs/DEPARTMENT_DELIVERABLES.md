# Cross-department deliverables

The platform treats each department as a consumer and producer of governed data products. Every deliverable has an explicit source, grain, owner, downstream consumers and verification path.

| Department | Primary deliverables | Principal inputs | Main consumers |
|---|---|---|---|
| Data Platform | canonical models, contracts, lineage, replay, reconciliation, SLOs | raw events, vendor files, infrastructure telemetry | all departments |
| Data Science | feature sets, risk scores, anomaly scores, drift reports, model-promotion evidence | canonical lending/treasury/customer state | Risk, Treasury, Product, Customer Success |
| Finance | product profitability, funds-transfer charge, expected loss attribution, capital allocation, management scorecards | lending, balances, treasury, platform cost | Executive, Shareholder, Product |
| Lending Operations | application readiness queue, lifecycle state, exception queues, cycle-time metrics | application/document/identity events | Operations, Product, Customer Success |
| Treasury | ACH canonical history, returns, transaction volumes, anomaly triage | payment events, business/account dimensions | Risk, Finance, Operations |
| Risk | exposure, concentration, expected loss, stress scenarios, model controls | lending, customer, treasury, models | Executive, Compliance, Finance |
| Compliance | contract and lineage evidence, control attestations, data classification, retention evidence | catalog, lineage, quality, security controls | Audit/Executive |
| Product | funnel friction, adoption, customer journey and service-level metrics | lending lifecycle, interactions, channel | Executive, Customer Success |
| Customer Success | proactive service intervention signals, contact outcomes, sentiment trends | lifecycle, interaction, model scores | Product, Operations |
| SRE | freshness, lag, throughput, trigger duration, state growth, error budgets, capacity forecast | Spark/Kafka/storage/runtime telemetry | Data Platform, Executive |
| Security | encryption, IAM, tokenization, secret handling, software-supply-chain evidence | IaC, catalog classification, CI | Compliance, SRE |
| Data Quality | rule failures, quarantine clusters, source quality scorecards, root-cause backlog | all pipeline stages | Producer teams, Finance, Risk |
| Enterprise Architecture | contract compatibility, dependency graph, technology standards, blast-radius analysis | contracts, lineage, deployment topology | Engineering, Compliance |
| Operations | cross-team work graph, incidents, dependencies, service controls | department work items and platform telemetry | Executive |
| Executive | operating scorecard, growth/risk/cost/customer outcome views | finance, risk, platform, product | leadership |
| Shareholder Analytics | durable growth, return-on-capital, efficiency and risk-adjusted KPI snapshots | finance, risk, customer and reliability marts | management/shareholder reporting |

## Shared contract rules

Every data product should define:

1. business grain;
2. stable business key;
3. source and event-time semantics;
4. data classification;
5. owner and accountable consumer;
6. freshness and availability SLO;
7. duplicate and late-data policy;
8. quality rules and quarantine behavior;
9. replay/backfill behavior;
10. source-to-target reconciliation;
11. lineage and downstream blast radius;
12. deployment and rollback evidence.

## Work management

The live collaboration schema persists departments, stakeholders, work items, dependencies, comments, recommendations and agent runs. The connected Linear project provides a separate execution surface while GitHub remains the code/evidence system of record.

Linear project: https://linear.app/mrdata355/project/banking-data-platform-cross-department-delivery-ea0554167dc5

GitHub PR: https://github.com/mrdata355/small-business-banking-data-platform/pull/1
