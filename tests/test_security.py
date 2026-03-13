import os
import pytest
from pathlib import Path
from heidi_engine import telemetry
from heidi_engine import dashboard

def test_telemetry_get_run_dir_traversal(tmp_path):
    """
    Test that telemetry.get_run_dir prevents path traversal.
    """
    # Set AUTOTRAIN_DIR to a temporary path
    telemetry.AUTOTRAIN_DIR = str(tmp_path)

    # Malicious run_id
    malicious_id = "../../forbidden"

    # Get run dir
    run_dir = telemetry.get_run_dir(malicious_id)

    # It should be sanitized to just the name
    assert run_dir.name == "forbidden"
    assert ".." not in str(run_dir)

    # The parent should be the runs directory under tmp_path
    expected_parent = Path(tmp_path) / "runs"
    assert run_dir.parent.resolve() == expected_parent.resolve()

def test_dashboard_get_run_dir_traversal(tmp_path):
    """
    Test that dashboard.get_run_dir prevents path traversal.
    """
    # Set AUTOTRAIN_DIR to a temporary path
    dashboard.AUTOTRAIN_DIR = str(tmp_path)

    # Malicious run_id
    malicious_id = "/etc/passwd"

    # Get run dir
    run_dir = dashboard.get_run_dir(malicious_id)

    # It should be sanitized to just the name
    assert run_dir.name == "passwd"

    # The parent should be the runs directory under tmp_path
    expected_parent = Path(tmp_path) / "runs"
    assert run_dir.parent.resolve() == expected_parent.resolve()

def test_telemetry_absolute_path_injection(tmp_path):
    """
    Test that absolute paths are sanitized.
    """
    telemetry.AUTOTRAIN_DIR = str(tmp_path)

    malicious_id = "/tmp/malicious"
    run_dir = telemetry.get_run_dir(malicious_id)

    assert run_dir.name == "malicious"
    assert str(run_dir).startswith(str(Path(tmp_path) / "runs"))
