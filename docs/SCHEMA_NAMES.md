# Catalog and schema names

```text
oakbridge_prod
├── bronze_lending
│   └── loan_application_event_raw
├── bronze_treasury
│   └── ach_event_raw
├── bronze_customer
│   └── business_onboarding_raw
├── bronze_risk
│   └── identity_verification_raw
├── silver_lending
│   ├── loan_application
│   └── loan_application_status_history
├── silver_customer
│   ├── customer
│   ├── business
│   └── guarantor_relationship
├── silver_risk
│   └── identity_verification
├── silver_treasury
│   └── ach_transaction
├── gold_lending
│   ├── underwriting_readiness_queue
│   └── application_funnel_daily
├── gold_treasury
│   └── activity_daily
├── gold_customer
│   └── customer_360
├── feature_store
│   ├── application_risk_features
│   └── ach_anomaly_features
└── ops
    ├── pipeline_reconciliation
    ├── data_quality_result
    ├── schema_contract_result
    ├── stream_health
    └── model_monitoring
```

These names are owned by this project and are not representations of any bank's private catalog.
