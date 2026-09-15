from __future__ import annotations

import json
import shutil
from pathlib import Path

from oakbridge.config.settings import Settings


def write_json_lines(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def seed(reset: bool = True) -> Settings:
    cfg = Settings.from_env()
    if reset and cfg.runtime_root.exists():
        shutil.rmtree(cfg.runtime_root)

    onboarding = [
        {"onboarding_event_id":"ONB-1001","event_ts":"2026-09-14T13:00:00Z","customer_id":"CUST-501","business_id":"BIZ-201","owner_name":"Jordan Ellis","owner_email":"JORDAN.ELLIS@EXAMPLE.TEST","owner_phone":"+12025550101","owner_dob":"1986-07-18","tax_id_token":"tok-tax-c501","legal_business_name":"Harbor Dental Group LLC","ein_token":"tok-ein-b201","naics_code":"621210","formation_state":"nc","formation_date":"2018-03-09","business_address":"420 Market Street, Wilmington, NC","account_product":"business_plus","kyc_status":"VERIFIED","source_system":"digital_account_opening"},
        {"onboarding_event_id":"ONB-1002","event_ts":"2026-09-14T13:08:00Z","customer_id":"CUST-502","business_id":"BIZ-202","owner_name":"Morgan Reed","owner_email":"morgan.reed@example.test","owner_phone":"+12025550102","owner_dob":"1990-11-04","tax_id_token":"tok-tax-c502","legal_business_name":"Blue Ridge Equipment Services Inc","ein_token":"tok-ein-b202","naics_code":"811310","formation_state":"VA","formation_date":"2020-08-21","business_address":"80 Commerce Drive, Roanoke, VA","account_product":"business_essential","kyc_status":"VERIFIED","source_system":"digital_account_opening"},
    ]

    applications = [
        {"event_id":"EVT-1001","event_type":"LoanApplicationSubmitted","event_version":1,"event_ts":"2026-09-14T13:10:00Z","application_id":"APP-7001","customer_id":"CUST-501","business_id":"BIZ-201","product_code":"SBA_7A","requested_amount":850000.00,"use_of_funds":"ACQUISITION","application_status":"SUBMITTED","documents_complete":False,"financial_package_complete":False,"source_system":"digital_lending","trace_id":"tr-a1"},
        {"event_id":"EVT-1002","event_type":"DocumentReceived","event_version":2,"event_ts":"2026-09-14T13:13:00Z","application_id":"APP-7001","customer_id":"CUST-501","business_id":"BIZ-201","product_code":"SBA_7A","requested_amount":850000.00,"use_of_funds":"ACQUISITION","application_status":"DOCUMENTS_PENDING","documents_complete":True,"financial_package_complete":False,"source_system":"document_service","trace_id":"tr-a2"},
        {"event_id":"EVT-1003","event_type":"FinancialPackageReceived","event_version":3,"event_ts":"2026-09-14T13:18:00Z","application_id":"APP-7001","customer_id":"CUST-501","business_id":"BIZ-201","product_code":"SBA_7A","requested_amount":850000.00,"use_of_funds":"ACQUISITION","application_status":"REVIEW","documents_complete":True,"financial_package_complete":True,"source_system":"financial_package_service","trace_id":"tr-a3"},
        {"event_id":"EVT-1003","event_type":"FinancialPackageReceived","event_version":3,"event_ts":"2026-09-14T13:18:00Z","application_id":"APP-7001","customer_id":"CUST-501","business_id":"BIZ-201","product_code":"SBA_7A","requested_amount":850000.00,"use_of_funds":"ACQUISITION","application_status":"REVIEW","documents_complete":True,"financial_package_complete":True,"source_system":"financial_package_service","trace_id":"tr-a3-retry"},
        {"event_id":"EVT-BAD-1","event_type":"ApplicationStatusChanged","event_version":0,"event_ts":"2026-09-14T13:19:00Z","application_id":"APP-7002","customer_id":"CUST-502","business_id":"BIZ-202","product_code":"CONVENTIONAL","requested_amount":325000.00,"use_of_funds":"EQUIPMENT","application_status":"REVIEW","documents_complete":True,"financial_package_complete":True,"source_system":"digital_lending","trace_id":"tr-bad"},
    ]

    identity = [
        {"vendor_record_id":"IDV-9001","application_id":"APP-7001","customer_id":"CUST-501","verification_status":"VERIFIED","verification_ts":"2026-09-14T13:25:00Z","reason_code":None,"vendor_file_id":"IDV-FILE-20260914-1325"}
    ]

    ach = [
        {"transaction_id":"ACH-3001","event_ts":"2026-09-14T14:00:00Z","account_id":"ACCT-8001","business_id":"BIZ-201","direction":"DEBIT","amount":12500.00,"sec_code":"CCD","transaction_status":"POSTED","counterparty_token":"cp-100","source_system":"treasury_payments"},
        {"transaction_id":"ACH-3002","event_ts":"2026-09-14T14:05:00Z","account_id":"ACCT-8001","business_id":"BIZ-201","direction":"CREDIT","amount":18420.50,"sec_code":"CCD","transaction_status":"POSTED","counterparty_token":"cp-200","source_system":"treasury_payments"},
        {"transaction_id":"ACH-3002","event_ts":"2026-09-14T14:05:00Z","account_id":"ACCT-8001","business_id":"BIZ-201","direction":"CREDIT","amount":18420.50,"sec_code":"CCD","transaction_status":"POSTED","counterparty_token":"cp-200","source_system":"treasury_payments"},
    ]

    write_json_lines(cfg.landing / "business_onboarding" / "part-0001.json", onboarding)
    write_json_lines(cfg.landing / "application_events" / "part-0001.json", applications)
    write_json_lines(cfg.landing / "identity_verification" / "vendor-20260914-1325.json", identity)
    write_json_lines(cfg.landing / "ach_transactions" / "part-0001.json", ach)
    return cfg


if __name__ == "__main__":
    seed()
