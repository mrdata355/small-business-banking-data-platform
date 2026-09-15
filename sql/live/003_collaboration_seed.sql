INSERT INTO departments(department_code,department_name,mission,service_tier) VALUES
('DATA_PLATFORM','Data Platform','Provide trusted, observable and economical data products.','TIER_0'),
('LENDING','Lending','Move qualified business borrowers from application to funding with clarity and speed.','TIER_0'),
('TREASURY','Treasury','Operate reliable business payment and cash-management data products.','TIER_0'),
('RISK','Risk','Identify, measure and mitigate credit, operational and model risk.','TIER_0'),
('COMPLIANCE','Compliance','Maintain evidence-backed controls, lineage and policy adherence.','TIER_0'),
('FINANCE','Finance','Measure performance, forecast outcomes and explain economic drivers.','TIER_1'),
('OPERATIONS','Operations','Reduce queue time, manual rework and avoidable exceptions.','TIER_1'),
('DATA_SCIENCE','Data Science','Build monitored models and decision-support systems.','TIER_1'),
('CUSTOMER_SUCCESS','Customer Success','Reduce customer effort and resolve issues quickly.','TIER_1'),
('PRODUCT','Product','Improve digital workflows and time to customer value.','TIER_1'),
('SRE','SRE','Protect availability, latency, recovery and error budgets.','TIER_0'),
('SECURITY','Security','Protect identities, data, secrets and least-privilege boundaries.','TIER_0'),
('EXECUTIVE','Executive','Balance growth, service, risk and efficiency across the enterprise.','TIER_1'),
('SHAREHOLDER','Shareholder Analytics','Explain durable growth, profitability and risk-adjusted performance.','TIER_2')
ON CONFLICT (department_code) DO UPDATE SET mission=EXCLUDED.mission, service_tier=EXCLUDED.service_tier;

WITH d AS (SELECT department_code, department_id FROM departments)
INSERT INTO stakeholder_profiles(stakeholder_type,display_name,department_id,objective_weights)
SELECT * FROM (VALUES
('ENGINEERING','Platform Engineering',(SELECT department_id FROM d WHERE department_code='DATA_PLATFORM'),' {"correctness":1.0,"freshness":0.9,"cost":0.7}'::jsonb),
('PRODUCT','Digital Product',(SELECT department_id FROM d WHERE department_code='PRODUCT'),' {"conversion":1.0,"task_success":0.9,"adoption":0.8}'::jsonb),
('RISK','Enterprise Risk',(SELECT department_id FROM d WHERE department_code='RISK'),' {"loss_avoidance":1.0,"exceptions":0.9}'::jsonb),
('COMPLIANCE','Compliance',(SELECT department_id FROM d WHERE department_code='COMPLIANCE'),' {"control_coverage":1.0,"lineage":0.9}'::jsonb),
('FINANCE','Finance',(SELECT department_id FROM d WHERE department_code='FINANCE'),' {"margin":1.0,"forecast_accuracy":0.9}'::jsonb),
('OPERATIONS','Operations',(SELECT department_id FROM d WHERE department_code='OPERATIONS'),' {"cycle_time":1.0,"rework":0.9}'::jsonb),
('EXECUTIVE','Executive Management',(SELECT department_id FROM d WHERE department_code='EXECUTIVE'),' {"growth":1.0,"risk_adjusted_return":1.0,"service":0.8}'::jsonb),
('SHAREHOLDER','Shareholder View',(SELECT department_id FROM d WHERE department_code='SHAREHOLDER'),' {"growth":1.0,"profitability":1.0,"asset_quality":1.0}'::jsonb),
('CUSTOMER_SUCCESS','Customer Success',(SELECT department_id FROM d WHERE department_code='CUSTOMER_SUCCESS'),' {"resolution_time":1.0,"sentiment":0.8}'::jsonb),
('DATA_SCIENCE','Data Science',(SELECT department_id FROM d WHERE department_code='DATA_SCIENCE'),' {"model_value":1.0,"drift":0.9}'::jsonb)
) x(stakeholder_type,display_name,department_id,objective_weights)
WHERE NOT EXISTS (SELECT 1 FROM stakeholder_profiles s WHERE s.stakeholder_type=x.stakeholder_type AND s.display_name=x.display_name);

WITH d AS (SELECT department_code, department_id FROM departments)
INSERT INTO work_items(work_key,title,description,work_type,status,priority,requester_department_id,owner_department_id,pipeline_component,estimated_hours,business_value,risk_reduction,urgency_score,effort_score,metadata) VALUES
('OB-00001','Eliminate unexplained reconciliation deltas','Require every lending source row to resolve to canonical history, quarantine or intentional dedupe.','DATA_CONTRACT','READY','P0',(SELECT department_id FROM d WHERE department_code='FINANCE'),(SELECT department_id FROM d WHERE department_code='DATA_PLATFORM'),'lending-reconciliation',12,9.5,10,10,3,'{"control":"source-target-reconciliation"}'),
('OB-00002','Reduce underwriting readiness queue age','Analyze document and identity-verification wait states and surface the most actionable bottlenecks.','STORY','READY','P1',(SELECT department_id FROM d WHERE department_code='LENDING'),(SELECT department_id FROM d WHERE department_code='DATA_PLATFORM'),'underwriting-readiness',20,10,6,9,4,'{"metric":"readiness_age"}'),
('OB-00003','Counterfactual contract replay before schema promotion','Run the Contract Genome blast-radius engine for every proposed schema, grain or key change.','EPIC','IN_PROGRESS','P1',(SELECT department_id FROM d WHERE department_code='RISK'),(SELECT department_id FROM d WHERE department_code='DATA_PLATFORM'),'contract-genome',32,8,10,7,5,'{"gate":"pre-merge"}'),
('OB-00004','Treasury anomaly review queue','Route high anomaly-score ACH events with evidence and disposition feedback to improve monitoring.','MODEL','READY','P1',(SELECT department_id FROM d WHERE department_code='TREASURY'),(SELECT department_id FROM d WHERE department_code='DATA_SCIENCE'),'ach-anomaly',24,8,9,8,4,'{"model":"ach_anomaly_detector"}'),
('OB-00005','Shareholder KPI forecast confidence bands','Publish generated management KPI forecasts with explicit uncertainty and driver attribution.','STORY','BACKLOG','P2',(SELECT department_id FROM d WHERE department_code='SHAREHOLDER'),(SELECT department_id FROM d WHERE department_code='FINANCE'),'management-kpi',28,8,4,5,5,'{"audience":"shareholder"}'),
('OB-00006','Negative sentiment early-warning signal','Join customer interaction sentiment with application wait-state and repeat-contact features.','MODEL','BACKLOG','P2',(SELECT department_id FROM d WHERE department_code='CUSTOMER_SUCCESS'),(SELECT department_id FROM d WHERE department_code='DATA_SCIENCE'),'customer-sentiment',30,7,5,6,5,'{"signal":"negative_sentiment"}'),
('OB-00007','Automated checkpoint recovery drill','Prove stream restart, raw replay and idempotent current-state recovery from a controlled failure.','TASK','READY','P1',(SELECT department_id FROM d WHERE department_code='SRE'),(SELECT department_id FROM d WHERE department_code='DATA_PLATFORM'),'spark-streaming',16,6,10,8,3,'{"runbook":"stream-recovery"}'),
('OB-00008','Restricted-field lineage and access evidence','Generate lineage evidence for restricted PII fields from landing through semantic views.','RISK','READY','P1',(SELECT department_id FROM d WHERE department_code='COMPLIANCE'),(SELECT department_id FROM d WHERE department_code='DATA_PLATFORM'),'lineage',22,6,10,7,4,'{"classification":"RESTRICTED"}')
ON CONFLICT (work_key) DO NOTHING;
