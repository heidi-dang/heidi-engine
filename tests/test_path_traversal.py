import os
import unittest
from pathlib import Path
from heidi_engine.telemetry import get_run_dir, get_run_id, init_telemetry, AUTOTRAIN_DIR

class TestPathTraversal(unittest.TestCase):
    def setUp(self):
        # Use a consistent run ID for testing
        os.environ["RUN_ID"] = ""
        import heidi_engine.telemetry
        heidi_engine.telemetry.RUN_ID = ""

    def test_run_id_sanitization_basename(self):
        """Test that run_id is sanitized via basename."""
        os.environ["RUN_ID"] = "test/run"
        run_id = get_run_id()
        self.assertEqual(run_id, "run")

    def test_run_id_sanitization_traversal(self):
        """Test that directory traversal is prevented."""
        os.environ["RUN_ID"] = "../../../etc/passwd"
        run_id = get_run_id()
        self.assertEqual(run_id, "passwd")

    def test_run_id_fallback_on_unsafe(self):
        """Test that unsafe IDs fallback to UUID generation."""
        os.environ["RUN_ID"] = ".."
        run_id = get_run_id()
        self.assertTrue(run_id.startswith("run_"))
        self.assertNotEqual(run_id, "..")

    def test_get_run_dir_sanitization(self):
        """Test that get_run_dir sanitizes its input."""
        # Reset RUN_ID to ensure a fresh one is generated if needed
        import heidi_engine.telemetry
        heidi_engine.telemetry.RUN_ID = "safe_default"

        # Test with dangerous input
        path = get_run_dir("../danger")
        self.assertEqual(path.name, "danger")
        self.assertIn("runs/danger", str(path))

    def test_init_telemetry_sanitization(self):
        """Test that init_telemetry sanitizes the provided run_id."""
        run_id = init_telemetry(run_id="evil/path", force=True)
        self.assertEqual(run_id, "path")
        self.assertTrue(get_run_dir().exists())

if __name__ == "__main__":
    unittest.main()
