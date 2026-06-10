import os
import tempfile
from pathlib import Path
from heidi_engine import telemetry

def test_get_run_dir_sanitization():
    # Use a real temporary directory for AUTOTRAIN_DIR
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir_path = Path(tmp_dir).resolve()
        telemetry.AUTOTRAIN_DIR = str(tmp_dir_path)

        # Test 1: Normal run_id
        run_id = "test_run"
        run_dir = telemetry.get_run_dir(run_id).resolve()
        assert run_dir.name == "test_run"
        assert tmp_dir_path in run_dir.parents

        # Test 2: Absolute path run_id (Attempted traversal)
        # Even if /tmp/escaped is passed, it should be sanitized
        run_id = "/tmp/escaped"
        run_dir = telemetry.get_run_dir(run_id).resolve()
        # Should be sanitized to just the name component
        assert run_dir.name == "escaped"
        assert tmp_dir_path in run_dir.parents

        # Test 3: Parent directory traversal
        run_id = "../../../etc/passwd"
        run_dir = telemetry.get_run_dir(run_id).resolve()
        assert run_dir.name == "passwd"
        assert tmp_dir_path in run_dir.parents

        # Test 4: Special case '.'
        run_id = "."
        run_dir = telemetry.get_run_dir(run_id).resolve()
        # Path(".").name is "" -> sanitized to "default"
        assert run_dir.name == "default"
        assert tmp_dir_path in run_dir.parents

        # Test 5: Special case '..'
        run_id = ".."
        run_dir = telemetry.get_run_dir(run_id).resolve()
        # Path("..").name is ".." -> sanitized to "default"
        assert run_dir.name == "default"
        assert tmp_dir_path in run_dir.parents
