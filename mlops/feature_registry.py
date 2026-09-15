from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Feature:
    name: str
    entity: str
    dtype: str
    description: str
    source_asset: str
    expression: str
    freshness_seconds: int
    owner: str
    classification: str = "CONFIDENTIAL"
    online: bool = False


FEATURES = (
    Feature("application_age_minutes","application","double","Minutes since application submission.","silver_lending.loan_application","timestampdiff(MINUTE, submitted_at, current_timestamp())",120,"data-science"),
    Feature("documents_complete","application","boolean","Whether required document package is complete.","silver_lending.loan_application","documents_complete",120,"lending-data"),
    Feature("financial_package_complete","application","boolean","Whether current financial package is complete.","silver_lending.loan_application","financial_package_complete",120,"lending-data"),
    Feature("identity_verified","application","boolean","Latest canonical identity-verification outcome.","silver_risk.identity_verification","verification_status = 'VERIFIED'",300,"risk-data"),
    Feature("missing_prerequisite_count","application","integer","Count of incomplete readiness prerequisites.","gold_lending.underwriting_readiness_queue","cast(not documents_complete as int)+cast(not financial_package_complete as int)+cast(identity_verification_status <> 'VERIFIED' as int)",180,"data-science"),
    Feature("requested_amount_log","application","double","Log-scaled requested principal.","silver_lending.loan_application","ln(1 + requested_amount)",180,"data-science"),
    Feature("status_transition_count_24h","application","integer","Accepted application-state transitions in trailing 24 hours.","silver_lending.loan_application_status_history","count_if(event_ts >= feature_ts - interval 24 hours)",300,"data-science"),
    Feature("business_ach_amount_7d","business","decimal(20,2)","Posted ACH amount over the trailing seven days.","silver_treasury.ach_transaction","sum(amount) over trailing 7 days",300,"treasury-data"),
    Feature("business_ach_return_rate_30d","business","double","Returned ACH transactions divided by completed ACH activity in trailing 30 days.","silver_treasury.ach_transaction","returned_count_30d / nullif(transaction_count_30d,0)",300,"treasury-data"),
    Feature("business_ach_amount_zscore","transaction","double","Transaction amount z-score relative to historical business behavior.","silver_treasury.ach_transaction","(amount-mean_amount_90d)/nullif(stddev_amount_90d,0)",60,"data-science",online=True),
    Feature("customer_negative_sentiment_7d","customer","double","Share of recent generated interactions classified negative.","gold_customer.customer_interaction","negative_interactions_7d / nullif(interactions_7d,0)",900,"customer-analytics"),
    Feature("repeat_contact_count_72h","customer","integer","Number of customer contacts in trailing 72 hours.","gold_customer.customer_interaction","count_if(created_ts >= feature_ts - interval 72 hours)",900,"customer-analytics"),
)

FEATURE_BY_NAME = {f.name: f for f in FEATURES}


def validate_feature_set(names: Iterable[str]) -> list[Feature]:
    missing = sorted(set(names) - FEATURE_BY_NAME.keys())
    if missing:
        raise KeyError(f"unregistered feature(s): {', '.join(missing)}")
    return [FEATURE_BY_NAME[name] for name in names]


def max_freshness_seconds(names: Iterable[str]) -> int:
    features = validate_feature_set(names)
    return max((f.freshness_seconds for f in features), default=0)
