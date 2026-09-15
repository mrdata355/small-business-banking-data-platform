from scale.transaction_universe import (
    UNIVERSE_CARDINALITY,
    build_block_manifest,
    manifest_summary,
    transaction_for_ordinal,
    validate_determinism,
)


def test_universe_is_exactly_one_trillion_addressable_records():
    blocks = build_block_manifest()
    summary = manifest_summary(blocks)
    assert summary["logical_transaction_cardinality"] == 1_000_000_000_000
    assert summary["logical_transaction_cardinality"] == UNIVERSE_CARDINALITY
    assert blocks[0].start_ordinal == 0
    assert blocks[-1].end_ordinal == UNIVERSE_CARDINALITY - 1


def test_any_ordinal_is_reproducible_without_materializing_prior_rows():
    ordinal = 999_999_999_999
    a = transaction_for_ordinal(ordinal)
    b = transaction_for_ordinal(ordinal)
    assert a == b
    assert a.ordinal == ordinal
    assert a.transaction_id.startswith("ACH-999999999999-")


def test_determinism_probe_has_no_collisions_in_sample():
    result = validate_determinism(samples=1000, seed=17)
    assert result["deterministic"] is True
    assert result["mismatch_count"] == 0
    assert result["id_collision_count"] == 0
