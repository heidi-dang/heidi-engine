import os
from pathlib import Path
from heidi_engine.telemetry import get_run_dir as telemetry_get_run_dir, AUTOTRAIN_DIR as TELEMETRY_AUTOTRAIN_DIR
from heidi_engine.dashboard import get_run_dir as dashboard_get_run_dir, AUTOTRAIN_DIR as DASHBOARD_AUTOTRAIN_DIR

def test_get_run_dir_sanitization():
    # Test cases for both telemetry and dashboard get_run_dir
    test_cases = [
        # (run_id, expected_name)
        ("valid_run", "valid_run"),
        ("/etc/passwd", "passwd"),
        ("../../etc/passwd", "passwd"),
        ("..", "default_run"),
        (".", "default_run"),
        ("/", "default_run"),
        ("", "default_run"),
    ]

    # Test Telemetry get_run_dir
    for run_id, expected_name in test_cases:
        run_dir = telemetry_get_run_dir(run_id)
        assert run_dir.name == expected_name
        # Ensure it's under the base directory
        assert Path(TELEMETRY_AUTOTRAIN_DIR) in run_dir.parents

    # Test Dashboard get_run_dir
    for run_id, expected_name in test_cases:
        run_dir = dashboard_get_run_dir(run_id)
        assert run_dir.name == expected_name
        # Ensure it's under the base directory
        assert Path(DASHBOARD_AUTOTRAIN_DIR) in run_dir.parents
