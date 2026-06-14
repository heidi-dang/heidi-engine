import os
from pathlib import Path
from heidi_engine.telemetry import get_run_dir as telemetry_get_run_dir, AUTOTRAIN_DIR as TELEMETRY_AUTOTRAIN_DIR
from heidi_engine.dashboard import get_run_dir as dashboard_get_run_dir, AUTOTRAIN_DIR as DASHBOARD_AUTOTRAIN_DIR

def test_telemetry_get_run_dir_sanitization():
    # Absolute path traversal
    run_id = "/tmp/evil"
    run_dir = telemetry_get_run_dir(run_id)
    assert str(run_dir) != "/tmp/evil"
    assert Path(TELEMETRY_AUTOTRAIN_DIR) in run_dir.parents

    # Relative path traversal
    run_id = "../../etc/passwd"
    run_dir = telemetry_get_run_dir(run_id)
    assert "etc" not in run_dir.parts
    assert Path(TELEMETRY_AUTOTRAIN_DIR) in run_dir.parents

    # Dot cases
    assert telemetry_get_run_dir(".").name != ""
    assert telemetry_get_run_dir("..").name != ".."

def test_dashboard_get_run_dir_sanitization():
    # Absolute path traversal
    run_id = "/tmp/evil"
    run_dir = dashboard_get_run_dir(run_id)
    assert str(run_dir) != "/tmp/evil"
    assert Path(DASHBOARD_AUTOTRAIN_DIR) in run_dir.parents

    # Relative path traversal
    run_id = "../../etc/passwd"
    run_dir = dashboard_get_run_dir(run_id)
    assert "etc" not in run_dir.parts
    assert Path(DASHBOARD_AUTOTRAIN_DIR) in run_dir.parents

    # Dot cases
    assert dashboard_get_run_dir(".").name != ""
    assert dashboard_get_run_dir("..").name != ".."
