import os
import shutil
import tempfile
import unittest
from pathlib import Path
from heidi_engine import telemetry

class TestPathTraversal(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.old_autotrain_dir = telemetry.AUTOTRAIN_DIR
        telemetry.AUTOTRAIN_DIR = self.test_dir
        # Reset global state
        telemetry.RUN_ID = ""

    def tearDown(self):
        telemetry.AUTOTRAIN_DIR = self.old_autotrain_dir
        shutil.rmtree(self.test_dir)

    def test_get_run_dir_sanitization(self):
        """Test that get_run_dir sanitizes malicious run_ids."""
        malicious_id = "../../etc"
        run_dir = telemetry.get_run_dir(malicious_id)

        # Ensure the run_dir is still within the test_dir/runs/
        expected_base = Path(self.test_dir) / "runs"
        self.assertTrue(str(run_dir).startswith(str(expected_base)), f"Path escaped base: {run_dir}")
        self.assertEqual(run_dir.name, "etc")

    def test_get_run_dir_fallback(self):
        """Test that get_run_dir falls back to a safe ID for dangerous inputs."""
        for dangerous_id in (".", "..", "/"):
            run_dir = telemetry.get_run_dir(dangerous_id)
            self.assertTrue(run_dir.name.startswith("safe_"), f"Failed for {dangerous_id}: {run_dir.name}")

    def test_get_run_id_env_sanitization(self):
        """Test that get_run_id sanitizes RUN_ID from environment."""
        os.environ["RUN_ID"] = "../hidden_run"
        try:
            run_id = telemetry.get_run_id()
            self.assertEqual(run_id, "hidden_run")
        finally:
            del os.environ["RUN_ID"]

    def test_get_run_id_env_unsafe_fallback(self):
        """Test that get_run_id regenerates if environment RUN_ID is unsafe."""
        os.environ["RUN_ID"] = ".."
        try:
            run_id = telemetry.get_run_id()
            self.assertFalse(run_id == "..")
            self.assertTrue(run_id.startswith("run_"))
        finally:
            del os.environ["RUN_ID"]

    def test_init_telemetry_sanitization(self):
        """Test that init_telemetry sanitizes direct run_id input."""
        malicious_id = "../evil"
        run_id = telemetry.init_telemetry(run_id=malicious_id)
        self.assertEqual(run_id, "evil")

        # Verify directory exists with sanitized name
        run_dir = Path(self.test_dir) / "runs" / "evil"
        self.assertTrue(run_dir.exists())

if __name__ == "__main__":
    unittest.main()
