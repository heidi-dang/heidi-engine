import pytest
import os
from pathlib import Path
from heidi_engine.telemetry import get_run_dir as telemetry_get_run_dir
from heidi_engine.dashboard import get_run_dir as dashboard_get_run_dir

def test_get_run_dir_sanitization():
    # Test absolute path traversal
    evil_id = "/tmp/evil"

    telemetry_dir = telemetry_get_run_dir(evil_id)
    dashboard_dir = dashboard_get_run_dir(evil_id)

    # Verify they are sanitized
    assert telemetry_dir.name == "evil"
    assert "/tmp/evil" not in str(telemetry_dir)
    assert dashboard_dir.name == "evil"
    assert "/tmp/evil" not in str(dashboard_dir)

    # Check that they are inside the expected base directory
    # telemetry uses heidi_engine, dashboard uses heidi-engine (based on default)
    assert "runs" in [p.name for p in telemetry_dir.parents]
    assert "runs" in [p.name for p in dashboard_dir.parents]

    # Test relative traversal
    evil_id_2 = "../../etc/passwd"
    telemetry_dir_2 = telemetry_get_run_dir(evil_id_2)

    assert telemetry_dir_2.name == "passwd"
    assert "etc" not in [p.name for p in telemetry_dir_2.parents]
    assert "runs" in [p.name for p in telemetry_dir_2.parents]

    # Test dot/dot-dot
    assert telemetry_get_run_dir(".").name not in (".", "")
    assert telemetry_get_run_dir("..").name not in ("..", "")
