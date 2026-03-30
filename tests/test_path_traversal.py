
import os
import tempfile
import uuid
from pathlib import Path
from heidi_engine import telemetry

def test_get_run_dir_path_traversal():
    with tempfile.TemporaryDirectory() as tmp_dir:
        telemetry.AUTOTRAIN_DIR = tmp_dir
        expected_base = Path(tmp_dir) / "runs"

        # Relative traversal
        malicious_id = "../../evil"
        run_dir = telemetry.get_run_dir(malicious_id)
        assert run_dir.name == "evil"
        assert run_dir.parent == expected_base

        # Absolute traversal
        absolute_id = "/tmp/evil_abs"
        run_dir_abs = telemetry.get_run_dir(absolute_id)
        assert run_dir_abs.name == "evil_abs"
        assert run_dir_abs.parent == expected_base

        # Dangerous names (., ..)
        for dangerous in (".", "..", ""):
            run_dir_dangerous = telemetry.get_run_dir(dangerous)
            assert run_dir_dangerous.name.startswith("safe_")
            assert run_dir_dangerous.parent == expected_base

def test_init_telemetry_sanitization():
    with tempfile.TemporaryDirectory() as tmp_dir:
        telemetry.AUTOTRAIN_DIR = tmp_dir

        # Should sanitize run_id passed to init_telemetry
        malicious_id = "../sanitized_run"
        run_id = telemetry.init_telemetry(run_id=malicious_id)

        assert run_id == "sanitized_run"
        assert (Path(tmp_dir) / "runs" / "sanitized_run").exists()

def test_get_run_id_env_sanitization():
    with tempfile.TemporaryDirectory() as tmp_dir:
        telemetry.AUTOTRAIN_DIR = tmp_dir

        # Mock environment variable
        os.environ["RUN_ID"] = "../../env_malicious"
        telemetry.RUN_ID = "" # Reset global

        run_id = telemetry.get_run_id()
        assert run_id == "env_malicious"

        # Clean up
        del os.environ["RUN_ID"]
        telemetry.RUN_ID = ""

def test_get_run_id_dangerous_env_fallback():
    with tempfile.TemporaryDirectory() as tmp_dir:
        telemetry.AUTOTRAIN_DIR = tmp_dir

        # Mock dangerous environment variable
        os.environ["RUN_ID"] = ".."
        telemetry.RUN_ID = "" # Reset global

        run_id = telemetry.get_run_id()
        assert run_id.startswith("run_")
        assert run_id != ".."

        # Clean up
        del os.environ["RUN_ID"]
        telemetry.RUN_ID = ""
