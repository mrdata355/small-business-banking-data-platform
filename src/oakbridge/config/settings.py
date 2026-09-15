from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    runtime_root: Path

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(Path(os.getenv("OAKBRIDGE_RUNTIME_ROOT", "runtime")).resolve())

    @property
    def landing(self) -> Path:
        return self.runtime_root / "landing"

    @property
    def lake(self) -> Path:
        return self.runtime_root / "lake"

    @property
    def checkpoints(self) -> Path:
        return self.runtime_root / "checkpoints"

    def landing_path(self, domain: str) -> str:
        return str(self.landing / domain)

    def bronze_path(self, domain: str) -> str:
        return str(self.lake / "bronze" / domain)

    def quarantine_path(self, domain: str) -> str:
        return str(self.lake / "quarantine" / domain)

    def silver_path(self, name: str) -> str:
        return str(self.lake / "silver" / name)

    def gold_path(self, name: str) -> str:
        return str(self.lake / "gold" / name)

    def ops_path(self, name: str) -> str:
        return str(self.lake / "ops" / name)

    def checkpoint_path(self, name: str) -> str:
        return str(self.checkpoints / name)


PRODUCTION_NAMES = {
    "application_event_stream": "oakbridge-prod-us-east-1-lending-application-events-v1",
    "ach_event_stream": "oakbridge-prod-us-east-1-treasury-ach-events-v1",
    "data_bucket": "s3://oakbridge-prod-data-us-east-1",
    "state_bucket": "s3://oakbridge-prod-stream-state-us-east-1",
    "vendor_identity_landing": (
        "s3://oakbridge-prod-data-us-east-1/landing/vendor/identity_verification/"
    ),
    "application_table": "oakbridge_prod.silver_lending.loan_application",
    "business_table": "oakbridge_prod.silver_customer.business",
    "customer_table": "oakbridge_prod.silver_customer.customer",
    "identity_table": "oakbridge_prod.silver_risk.identity_verification",
    "ach_table": "oakbridge_prod.silver_treasury.ach_transaction",
    "readiness_table": "oakbridge_prod.gold_lending.underwriting_readiness_queue",
}
