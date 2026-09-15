# Test strategy

## Unit

- deterministic transform behavior
- schema and domain rules
- business-state derivation
- event precedence
- semantic metric formulas

## Contract

- JSON Schema validation
- compatible producer payloads
- required key/nullability checks
- schema-registry subject registration

## Integration

- Kafka publish -> Spark consume
- landing object -> Bronze
- duplicate delivery -> single current state
- invalid event -> quarantine
- newer version -> current-state merge
- stale version -> history only
- ACH event -> Silver -> Gold aggregate

## Recovery

- stop stream and restart from checkpoint
- replay Bronze range
- run same event twice
- run late event after newer state
- validate source-to-target reconciliation

## Deployment

- lint
- unit tests
- local Spark pipeline
- evidence rendering
- configuration/schema validation
