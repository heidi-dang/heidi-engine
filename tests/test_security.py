import os
import pytest
from pathlib import Path
from heidi_engine import telemetry

def test_get_run_dir_sanitization():
    """
    Test that get_run_dir properly sanitizes run_id to prevent path traversal.
    """
    # Save original AUTOTRAIN_DIR to restore later
    original_dir = telemetry.AUTOTRAIN_DIR
    try:
        # Use a temporary directory for testing
        test_base = "/tmp/heidi_test"
        telemetry.AUTOTRAIN_DIR = test_base
        expected_base = Path(test_base) / "runs"

        # 1. Normal run_id
        assert telemetry.get_run_dir("run_123") == expected_base / "run_123"

        # 2. Absolute path (should be stripped to filename)
        assert telemetry.get_run_dir("/etc/passwd") == expected_base / "passwd"

        # 3. Relative traversal
        assert telemetry.get_run_dir("../../../etc/passwd") == expected_base / "passwd"

        # 4. Dot/Double dot (should fallback to auto-generated ID)
        run_dir_dot = telemetry.get_run_dir(".")
        assert run_dir_dot.parent == expected_base
        assert run_dir_dot.name.startswith("run_")

        run_dir_dotdot = telemetry.get_run_dir("..")
        assert run_dir_dotdot.parent == expected_base
        assert run_dir_dotdot.name.startswith("run_")

        # 5. Empty string
        run_dir_empty = telemetry.get_run_dir("")
        assert run_dir_empty.parent == expected_base
        assert run_dir_empty.name.startswith("run_")

    finally:
        telemetry.AUTOTRAIN_DIR = original_dir
