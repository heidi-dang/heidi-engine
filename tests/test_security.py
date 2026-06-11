
import os
import pytest
from pathlib import Path
from heidi_engine.telemetry import get_run_dir as get_telemetry_run_dir, AUTOTRAIN_DIR as TELEMETRY_AUTOTRAIN_DIR
from heidi_engine.dashboard import get_run_dir as get_dashboard_run_dir, AUTOTRAIN_DIR as DASHBOARD_AUTOTRAIN_DIR

def test_get_run_dir_sanitization():
    """
    Test that get_run_dir sanitizes run_id to prevent path traversal.
    """
    traversal_ids = [
        "/etc/passwd",
        "../../etc/passwd",
        "runs/test",
        "C:\\Windows\\System32" if os.name == "nt" else "/bin/sh",
        ".",
        "..",
        ""
    ]

    # Test Telemetry
    for tid in traversal_ids:
        run_dir = get_telemetry_run_dir(tid)
        # Ensure the resulting path is under AUTOTRAIN_DIR
        assert Path(TELEMETRY_AUTOTRAIN_DIR) in run_dir.parents
        assert ".." not in run_dir.parts

        # Ensure it's not pointing to sensitive system files
        assert str(run_dir) != "/etc/passwd"
        assert str(run_dir) != "/bin/sh"

    # Test Dashboard
    for tid in traversal_ids:
        if not tid: continue # dashboard get_run_dir requires a string
        run_dir = get_dashboard_run_dir(tid)
        assert Path(DASHBOARD_AUTOTRAIN_DIR) in run_dir.parents
        assert ".." not in run_dir.parts
        assert str(run_dir) != "/etc/passwd"
