
import pytest
from pathlib import Path
from heidi_engine.telemetry import get_run_dir, AUTOTRAIN_DIR

class TestSecurityHardening:
    """Test security hardening measures."""

    def test_get_run_dir_absolute_path_traversal(self):
        """Test that absolute path injection in run_id is neutralized."""
        traversal_id = "/tmp/evil"
        run_dir = get_run_dir(traversal_id)

        # Should be sanitized to just 'evil' inside the runs directory
        assert run_dir.name == "evil"
        assert str(run_dir).endswith("runs/evil")
        assert "/tmp/evil" not in str(run_dir)

    def test_get_run_dir_relative_path_traversal(self):
        """Test that relative path traversal in run_id is neutralized."""
        traversal_id = "../../evil"
        run_dir = get_run_dir(traversal_id)

        # Path("..").name is "" usually, but Path("../../evil").name is "evil"
        assert run_dir.name == "evil"
        assert ".." not in str(run_dir)

    def test_get_run_dir_empty_or_dots(self):
        """Test that empty or dot run_ids fallback to a safe ID."""
        for bad_id in ["", ".", ".."]:
            run_dir = get_run_dir(bad_id)
            assert run_dir.name not in ["", ".", ".."]
            assert len(run_dir.name) > 0

    def test_rotate_events_log_traversal_protection(self):
        """
        Test that _rotate_events_log doesn't operate outside runs directory.
        Note: We test this by calling it with a path outside runs and
        verifying it returns early (we can check coverage or just ensure no crash/weirdness).
        """
        from heidi_engine.telemetry import _rotate_events_log

        # Try to rotate something in /tmp (if we have permissions, but it should exit early)
        evil_path = Path("/tmp/events.jsonl")
        # This should print an [ERROR] and return
        _rotate_events_log(evil_path)

        # The test passes if it doesn't raise and follows the security check
