import pytest
from pathlib import Path
from heidi_engine.telemetry import get_run_dir as get_run_dir_telemetry
from heidi_engine.dashboard import get_run_dir as get_run_dir_dashboard

def test_get_run_dir_sanitization():
    """Test that get_run_dir sanitizes run_id to prevent path traversal."""

    # Test cases for both telemetry and dashboard get_run_dir
    test_cases = [
        ("/tmp/evil", "evil"),
        ("../../etc/passwd", "passwd"),
        (".", "default"),
        ("..", "default"),
        ("", "default"),
        ("normal_run", "normal_run"),
        ("run_20240101", "run_20240101"),
    ]

    for input_id, expected_name in test_cases:
        # Test telemetry version
        dir_telemetry = get_run_dir_telemetry(input_id)
        assert dir_telemetry.name == expected_name
        # Ensure it's under the runs directory
        assert "runs" in dir_telemetry.parts

        # Test dashboard version
        dir_dashboard = get_run_dir_dashboard(input_id)
        assert dir_dashboard.name == expected_name
        assert "runs" in dir_dashboard.parts

def test_path_traversal_blocked():
    """Explicitly verify that absolute paths don't escape the base directory."""
    malicious_id = "/tmp/evil"

    # Telemetry
    run_dir_telemetry = get_run_dir_telemetry(malicious_id)
    assert run_dir_telemetry.name == "evil"
    # Dashboard
    run_dir_dashboard = get_run_dir_dashboard(malicious_id)
    assert run_dir_dashboard.name == "evil"
