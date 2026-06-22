import os
import tempfile
from pathlib import Path
from heidi_engine import telemetry

def test_run_id_path_traversal():
    with tempfile.TemporaryDirectory() as tmp_dir:
        telemetry.AUTOTRAIN_DIR = tmp_dir

        # Test case 1: Basic traversal
        malicious_id = "../../../etc/passwd"
        run_dir = telemetry.get_run_dir(malicious_id)

        # Should be sanitized to just "passwd"
        assert run_dir.name == "passwd"
        assert str(run_dir).startswith(tmp_dir)

        # Test case 2: traversal with dot dot
        malicious_id = ".."
        run_dir = telemetry.get_run_dir(malicious_id)
        # Should be sanitized to "default_run"
        assert run_dir.name == "default_run"

        # Test case 3: empty string
        malicious_id = ""
        # If passed directly to get_run_dir, it might call get_run_id()
        # which would generate a new one if not set.
        # But let's test sanitize_run_id directly or get_run_dir with it
        assert telemetry.sanitize_run_id("") == "default_run"

        # Test case 4: complex traversal
        malicious_id = "/absolute/path/traversal"
        run_dir = telemetry.get_run_dir(malicious_id)
        assert run_dir.name == "traversal"
        assert str(run_dir).startswith(tmp_dir)

def test_env_run_id_sanitization():
    with tempfile.TemporaryDirectory() as tmp_dir:
        telemetry.AUTOTRAIN_DIR = tmp_dir
        # Reset global RUN_ID
        telemetry.RUN_ID = ""

        os.environ["RUN_ID"] = "../../dangerous"
        try:
            run_id = telemetry.get_run_id()
            assert run_id == "dangerous"

            run_dir = telemetry.get_run_dir()
            assert run_dir.name == "dangerous"
        finally:
            if "RUN_ID" in os.environ:
                del os.environ["RUN_ID"]
            telemetry.RUN_ID = ""
