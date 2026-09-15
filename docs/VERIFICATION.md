# Verification

The repository CI executes the Spark platform end to end on a clean GitHub-hosted runner rather than limiting validation to syntax checks.

## Verified run

GitHub Actions run: [CI run 2](https://github.com/mrdata355/small-business-banking-data-platform/actions/runs/34997591058)

Commit: `a46fa32512406fa6948f008a7b8ad413ec8b9d44`

The run completed successfully with:

- Ruff checks passed.
- 4 automated tests passed.
- Business-onboarding pipeline completed.
- Lending-application Structured Streaming pipeline completed.
- Identity-verification pipeline completed.
- Treasury / ACH Structured Streaming pipeline completed.
- Gold publishing completed.
- Source-to-target reconciliation balanced.

Application reconciliation result:

```text
source_count: 5
invalid_count: 1
duplicate_valid_count: 1
history_count: 3
explained_count: 5
balanced: true
```

Validated outputs included:

- `silver/business_onboarding`
- `silver/loan_application`
- `silver/identity_verification`
- `silver/ach_transaction`
- `gold/underwriting_readiness_queue`
- `gold/treasury_activity_daily`
- `ops/application_reconciliation`

The CI workflow also publishes the generated lake outputs as the `pipeline-evidence` workflow artifact for current runs.
