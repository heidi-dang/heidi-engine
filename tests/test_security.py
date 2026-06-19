import pytest
import os
from pathlib import Path
from heidi_engine.telemetry import get_run_dir as get_run_dir_telemetry, AUTOTRAIN_DIR as TELEMETRY_DIR
from heidi_engine.dashboard import get_run_dir as get_run_dir_dashboard, AUTOTRAIN_DIR as DASHBOARD_DIR

def test_get_run_dir_sanitization():
    # malicious_run_id
    malicious_run_id = "/etc/passwd"

    # Telemetry
    run_dir_tel = get_run_dir_telemetry(malicious_run_id)

    # Dashboard
    run_dir_dash = get_run_dir_dashboard(malicious_run_id)

    # We expect the run_dir to be a child of the respective AUTOTRAIN_DIR/runs
    # and not be the absolute path provided.

    assert str(run_dir_tel) != malicious_run_id, f"Telemetry vulnerable to absolute path traversal: {run_dir_tel}"
    assert str(run_dir_dash) != malicious_run_id, f"Dashboard vulnerable to absolute path traversal: {run_dir_dash}"

    # Verify it stays within the expected root
    # After fix, Path(run_id).name will turn "/etc/passwd" into "passwd"
    assert "passwd" in str(run_dir_tel)
    assert "/etc" not in str(run_dir_tel)

    assert "passwd" in str(run_dir_dash)
    assert "/etc" not in str(run_dir_dash)

def test_get_run_dir_relative_traversal():
    malicious_run_id = "../../../etc/passwd"

    run_dir_tel = get_run_dir_telemetry(malicious_run_id)
    run_dir_dash = get_run_dir_dashboard(malicious_run_id)

    assert ".." not in str(run_dir_tel), f"Telemetry vulnerable to relative path traversal: {run_dir_tel}"
    assert ".." not in str(run_dir_dash), f"Dashboard vulnerable to relative path traversal: {run_dir_dash}"

    assert "etc" not in str(run_dir_tel)
    assert "etc" not in str(run_dir_dash)
