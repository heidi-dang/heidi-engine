import os
from pathlib import Path
from heidi_engine.telemetry import get_run_dir as telemetry_get_run_dir
from heidi_engine.telemetry import AUTOTRAIN_DIR as TELEMETRY_BASE
from heidi_engine.dashboard import get_run_dir as dashboard_get_run_dir
from heidi_engine.dashboard import AUTOTRAIN_DIR as DASHBOARD_BASE

def test_get_run_dir_sanitization():
    """Verify that get_run_dir sanitizes malicious run_ids."""

    malicious_inputs = [
        "../../../tmp/evil",
        "/tmp/evil_abs",
        "..",
        ".",
        "../../etc/passwd",
        "run/secret"
    ]

    tel_expected_base = Path(TELEMETRY_BASE) / "runs"
    dash_expected_base = Path(DASHBOARD_BASE) / "runs"

    for run_id in malicious_inputs:
        # Test telemetry version
        run_dir = telemetry_get_run_dir(run_id)
        assert run_dir.name not in ("", ".", "..")
        assert run_dir.parent == tel_expected_base

        # Test dashboard version
        run_dir = dashboard_get_run_dir(run_id)
        assert run_dir.name not in ("", ".", "..")
        assert run_dir.parent == dash_expected_base

def test_get_run_dir_normal():
    """Verify that normal run_ids work correctly."""
    run_id = "run_20240101_120000_abc123"

    assert telemetry_get_run_dir(run_id) == Path(TELEMETRY_BASE) / "runs" / run_id
    assert dashboard_get_run_dir(run_id) == Path(DASHBOARD_BASE) / "runs" / run_id
