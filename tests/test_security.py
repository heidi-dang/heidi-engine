import os
import pytest
from pathlib import Path
from heidi_engine import telemetry
from heidi_engine import dashboard

def test_get_run_dir_sanitization():
    """
    Test that get_run_dir sanitizes run_id to prevent path traversal.
    """
    AUTOTRAIN_DIR = "/tmp/heidi-test"
    telemetry.AUTOTRAIN_DIR = AUTOTRAIN_DIR
    dashboard.AUTOTRAIN_DIR = AUTOTRAIN_DIR

    # Test cases: (input_run_id, expected_leaf_name)
    test_cases = [
        ("normal_run", "normal_run"),
        ("/etc/passwd", "passwd"),
        ("../../../etc/passwd", "passwd"),
        ("..", "default_run"),
        (".", "default_run"),
        ("", "default_run"),
        ("/", "default_run"),
        ("run/id", "id"),
    ]

    for input_id, expected_leaf in test_cases:
        # Test telemetry
        res_tel = telemetry.get_run_dir(input_id)
        assert res_tel.name == expected_leaf
        assert Path(AUTOTRAIN_DIR) in res_tel.parents

        # Test dashboard
        res_dash = dashboard.get_run_dir(input_id)
        assert res_dash.name == expected_leaf
        assert Path(AUTOTRAIN_DIR) in res_dash.parents

def test_get_run_dir_none():
    """Test get_run_dir with None (should use current run ID)."""
    # Just ensure it doesn't crash and returns a path within AUTOTRAIN_DIR
    res = telemetry.get_run_dir(None)
    assert Path(telemetry.AUTOTRAIN_DIR) in res.parents
