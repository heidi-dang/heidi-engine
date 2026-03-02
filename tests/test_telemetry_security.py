"""
Security tests for telemetry module.
Focuses on path traversal prevention in get_run_dir.
"""

from pathlib import Path

from heidi_engine.telemetry import AUTOTRAIN_DIR, get_run_dir


class TestTelemetrySecurity:
    """Test security measures in telemetry module."""

    def test_get_run_dir_safe(self):
        """Test that normal run_id works as expected."""
        run_id = "test_run_123"
        run_dir = get_run_dir(run_id)
        assert run_id in str(run_dir)
        assert str(run_dir).endswith(run_id)
        assert Path(AUTOTRAIN_DIR) in run_dir.parents

    def test_get_run_dir_path_traversal_dot_dot(self):
        """Test that .. is blocked in run_id."""
        run_id = "../../etc/passwd"
        run_dir = get_run_dir(run_id)
        # Should only take the filename part, but even then 'passwd' is better than traversal.
        # However, our implementation takes Path(run_id).name which is 'passwd'.
        assert "etc" not in str(run_dir)
        assert "passwd" in str(run_dir)
        assert Path(AUTOTRAIN_DIR) / "runs" in run_dir.parents

    def test_get_run_dir_path_traversal_absolute(self):
        """Test that absolute paths are blocked in run_id."""
        run_id = "/tmp/malicious"
        run_dir = get_run_dir(run_id)
        assert "tmp" not in str(run_dir)
        assert "malicious" in str(run_dir)
        assert Path(AUTOTRAIN_DIR) / "runs" in run_dir.parents

    def test_get_run_dir_blocked_values(self):
        """Test that '.', '..', and empty strings fall back to default_run."""
        for blocked in [".", "..", ""]:
            run_dir = get_run_dir(blocked)
            assert "default_run" in str(run_dir)
            if blocked:
                assert blocked not in str(run_dir).split("/")[-1]
            assert Path(AUTOTRAIN_DIR) / "runs" in run_dir.parents
