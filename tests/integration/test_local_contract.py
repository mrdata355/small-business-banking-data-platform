from pathlib import Path

from oakbridge.config.settings import Settings


def test_runtime_paths_are_layered(tmp_path):
    cfg = Settings(tmp_path)
    assert Path(cfg.bronze_path("application_events")).parts[-2:] == (
        "bronze",
        "application_events",
    )
    assert Path(cfg.silver_path("loan_application")).parts[-2:] == (
        "silver",
        "loan_application",
    )
