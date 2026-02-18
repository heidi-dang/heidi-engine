
import os
import unittest
from pathlib import Path
import tempfile
import shutil
from heidi_engine import telemetry

class TestTelemetrySecurity(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for AUTOTRAIN_DIR
        self.test_dir = tempfile.mkdtemp()
        self.old_autotrain_dir = telemetry.AUTOTRAIN_DIR
        telemetry.AUTOTRAIN_DIR = self.test_dir

        self.runs_dir = Path(self.test_dir) / "runs"
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        telemetry.AUTOTRAIN_DIR = self.old_autotrain_dir

    def test_get_run_dir_traversal(self):
        """Test that get_run_dir prevents path traversal."""
        malicious_run_id = "../../../tmp/evil"
        run_dir = telemetry.get_run_dir(malicious_run_id)

        # Should be restricted to the name part
        self.assertEqual(run_dir.name, "evil")
        self.assertTrue(str(run_dir).startswith(str(self.runs_dir)))

    def test_rotate_events_log_traversal(self):
        """Test that _rotate_events_log prevents deletion outside authorized dir."""
        # Create a sensitive file outside the runs directory
        sensitive_dir = Path(self.test_dir) / "sensitive"
        sensitive_dir.mkdir()
        sensitive_file = sensitive_dir / f"events.jsonl.{telemetry.EVENT_LOG_RETENTION}"
        sensitive_file.write_text("SENSITIVE")

        # Create a legitimate-looking but traversal path
        normal_run_dir = self.runs_dir / "normal_run"
        normal_run_dir.mkdir()

        # events_file that attempts to traverse to sensitive_dir
        # Resolve it to make it look like what an attacker might pass
        malicious_events_file = normal_run_dir / ".." / ".." / "sensitive" / "events.jsonl"

        # Create the 'current' log file so rename has something to do if it gets that far
        malicious_events_file.write_text("current log")

        self.assertTrue(sensitive_file.exists())

        # Call the vulnerable function
        telemetry._rotate_events_log(malicious_events_file)

        # Sensitive file should still exist
        self.assertTrue(sensitive_file.exists(), "Sensitive file was deleted despite fix!")
        self.assertEqual(sensitive_file.read_text(), "SENSITIVE")

    def test_rotate_events_log_wrong_filename(self):
        """Test that _rotate_events_log only operates on events.jsonl files."""
        normal_run_dir = self.runs_dir / "normal_run"
        normal_run_dir.mkdir()

        other_file = normal_run_dir / "config.json"
        other_file.write_text("important config")

        # Try to rotate config.json (should be ignored)
        telemetry._rotate_events_log(other_file)

        # config.json should NOT have been renamed to config.json.1
        self.assertTrue(other_file.exists())
        self.assertFalse((normal_run_dir / "config.json.1").exists())

if __name__ == "__main__":
    unittest.main()
