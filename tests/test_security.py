import pytest
from pathlib import Path
from heidi_engine import telemetry
from heidi_engine import dashboard

def test_path_traversal_telemetry():
    malicious_run_id = "../../../etc/passwd"
    run_dir = telemetry.get_run_dir(malicious_run_id)
    assert run_dir.name == "passwd"
    assert "etc" not in str(run_dir.parent)
    assert str(run_dir).startswith(str(Path(telemetry.AUTOTRAIN_DIR) / "runs"))

def test_path_traversal_dashboard():
    malicious_run_id = "../../../etc/passwd"
    run_dir = dashboard.get_run_dir(malicious_run_id)
    assert run_dir.name == "passwd"
    assert "etc" not in str(run_dir.parent)
    assert str(run_dir).startswith(str(Path(dashboard.AUTOTRAIN_DIR) / "runs"))

def test_absolute_path_injection():
    malicious_run_id = "/etc/passwd"
    run_dir = telemetry.get_run_dir(malicious_run_id)
    assert run_dir.name == "passwd"
    assert str(run_dir).startswith(str(Path(telemetry.AUTOTRAIN_DIR) / "runs"))
