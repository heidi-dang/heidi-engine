import os
import tempfile
from pathlib import Path
from heidi_engine import telemetry, dashboard

def test_telemetry_path_traversal_sanitization():
    """Verify that get_run_dir sanitizes run_id to prevent path traversal."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        telemetry.AUTOTRAIN_DIR = tmp_dir

        # Test with direct argument
        malicious_id = "../../../etc/passwd"
        run_dir = telemetry.get_run_dir(malicious_id)

        # Should be restricted to the runs directory and the name only
        expected_base = Path(tmp_dir) / "runs"
        assert str(run_dir) == str(expected_base / "passwd")
        assert "etc" not in str(run_dir)

def test_telemetry_env_sanitization():
    """Verify that get_run_id sanitizes RUN_ID from environment."""
    original_run_id = telemetry.RUN_ID
    try:
        telemetry.RUN_ID = "" # Reset global
        os.environ["RUN_ID"] = "../../../etc/shadow"

        run_id = telemetry.get_run_id()
        assert run_id == "shadow"

        # Verify get_run_dir uses the sanitized global
        with tempfile.TemporaryDirectory() as tmp_dir:
            telemetry.AUTOTRAIN_DIR = tmp_dir
            run_dir = telemetry.get_run_dir()
            expected_base = Path(tmp_dir) / "runs"
            assert str(run_dir) == str(expected_base / "shadow")
    finally:
        telemetry.RUN_ID = original_run_id
        if "RUN_ID" in os.environ:
            del os.environ["RUN_ID"]

def test_dashboard_path_traversal_sanitization():
    """Verify that dashboard.get_run_dir sanitizes run_id."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        dashboard.AUTOTRAIN_DIR = tmp_dir

        malicious_id = "/absolute/path/traversal"
        run_dir = dashboard.get_run_dir(malicious_id)

        expected_base = Path(tmp_dir) / "runs"
        assert str(run_dir) == str(expected_base / "traversal")
