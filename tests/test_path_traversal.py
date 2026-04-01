import os
import unittest
from pathlib import Path
import heidi_engine.telemetry
from heidi_engine.telemetry import get_run_dir, init_telemetry, get_run_id

class TestPathTraversal(unittest.TestCase):
    def setUp(self):
        # Use a safe temporary directory for testing
        self.test_dir = "/tmp/heidi_test"
        # Mock the AUTOTRAIN_DIR in the module
        heidi_engine.telemetry.AUTOTRAIN_DIR = self.test_dir
        # Reset global RUN_ID
        heidi_engine.telemetry.RUN_ID = ""
        if "RUN_ID" in os.environ:
            del os.environ["RUN_ID"]

    def test_get_run_dir_absolute_path(self):
        # Should sanitize absolute path
        malicious_id = "/etc/passwd"
        run_dir = get_run_dir(malicious_id)
        # Should be something like /tmp/heidi_test/runs/passwd
        self.assertTrue(str(run_dir).startswith(self.test_dir))
        self.assertEqual(run_dir.name, "passwd")
        self.assertNotEqual(str(run_dir), malicious_id)

    def test_get_run_dir_traversal(self):
        # Should sanitize relative traversal
        malicious_id = "../../etc/passwd"
        run_dir = get_run_dir(malicious_id)
        self.assertTrue(str(run_dir).startswith(self.test_dir))
        self.assertEqual(run_dir.name, "passwd")

    def test_get_run_dir_invalid(self):
        # Should fallback for invalid IDs
        for invalid_id in [".", "..", ""]:
            run_dir = get_run_dir(invalid_id)
            self.assertTrue(str(run_dir).startswith(self.test_dir))
            self.assertNotIn(run_dir.name, [".", "..", ""])
            self.assertTrue(run_dir.name.startswith("safe_"))

    def test_init_telemetry_sanitization(self):
        # init_telemetry should also sanitize
        malicious_id = "/tmp/bad_run"
        final_id = init_telemetry(run_id=malicious_id)
        self.assertEqual(final_id, "bad_run")

        run_dir = get_run_dir()
        self.assertTrue(str(run_dir).startswith(self.test_dir))
        self.assertTrue(str(run_dir).endswith("bad_run"))

    def test_env_var_sanitization(self):
        # RUN_ID env var should be sanitized
        os.environ["RUN_ID"] = "/etc/shadow"
        final_id = get_run_id()
        self.assertEqual(final_id, "shadow")

if __name__ == "__main__":
    unittest.main()
