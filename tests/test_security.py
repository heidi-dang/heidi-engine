"""
Security tests for path traversal vulnerabilities.
"""

import pytest
from pathlib import Path
from heidi_engine.telemetry import get_run_dir as tel_get_run_dir
from heidi_engine.dashboard import get_run_dir as dash_get_run_dir

class TestPathTraversal:
    """Test path traversal sanitization in both telemetry and dashboard."""

    @pytest.mark.parametrize("run_id, expected_suffix", [
        ("run123", "run123"),
        ("../etc/passwd", "passwd"),
        ("/etc/passwd", "passwd"),
        ("runs/../../etc/shadow", "shadow"),
        ("..\\..\\windows\\system32\\config\\sam", "sam"),  # Windows style
    ])
    def test_telemetry_get_run_dir_sanitization(self, run_id, expected_suffix):
        """Test that telemetry.get_run_dir sanitizes run_id."""
        run_dir = tel_get_run_dir(run_id)
        # Should always be a direct child of 'runs' (or at least not escape it)
        assert run_dir.name == Path(run_id).name
        assert "runs" in str(run_dir)

    @pytest.mark.parametrize("run_id, expected_suffix", [
        ("run123", "run123"),
        ("../etc/passwd", "passwd"),
        ("/etc/passwd", "passwd"),
    ])
    def test_dashboard_get_run_dir_sanitization(self, run_id, expected_suffix):
        """Test that dashboard.get_run_dir sanitizes run_id."""
        run_dir = dash_get_run_dir(run_id)
        assert run_dir.name == Path(run_id).name
        assert "runs" in str(run_dir)

    def test_absolute_path_traversal(self):
        """Test that absolute paths don't override the base directory."""
        # On Unix, Path("/etc/passwd").name is "passwd"
        # Path(AUTOTRAIN_DIR) / "runs" / "passwd" should be the result
        malicious_id = "/etc/passwd"
        run_dir = tel_get_run_dir(malicious_id)
        assert not str(run_dir).startswith("/etc/passwd")
        assert "runs" in str(run_dir)
        assert run_dir.name == "passwd"
