from oakbridge.config.settings import PRODUCTION_NAMES


def test_production_name_map_has_streams_and_tables():
    assert PRODUCTION_NAMES["application_event_stream"].endswith("-v1")
    assert ".silver_lending." in PRODUCTION_NAMES["application_table"]
    assert ".gold_lending." in PRODUCTION_NAMES["readiness_table"]
