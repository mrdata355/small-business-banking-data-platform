# Object/file naming

## Lending event object

```text
EVT-<12_HEX>.json
```

Full landing key:

```text
landing/lending/application-events/event_date=YYYY-MM-DD/application_id=APP-<ID>/EVT-<ID>.json
```

## Identity verification vendor file

```text
identity_verification_<vendor>_<YYYYMMDDTHHMMSSZ>_<batch_id>.jsonl
```

Landing key:

```text
landing/vendor/identity-verification/vendor=<vendor>/file_date=YYYY-MM-DD/<filename>
```

## Business onboarding file

```text
business_onboarding_<YYYYMMDDTHHMMSSZ>_<batch_id>.jsonl
```

## ACH event object

```text
ACH-<12_HEX>.json
```

Full landing key:

```text
landing/treasury/ach-events/event_date=YYYY-MM-DD/business_id=BIZ-<ID>/ACH-<ID>.json
```

## Checkpoint directories

Checkpoint paths are stable by pipeline and version; they are never derived from transient deployment ids.

```text
checkpoints/lending/application_stream/v1/
checkpoints/treasury/ach_stream/v1/
checkpoints/risk/identity_verification/v1/
```
