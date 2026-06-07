import pytest
from pathlib import Path
from heidi_engine import telemetry
import os

def test_get_run_dir_sanitization():
    """Test that get_run_dir properly sanitizes run_id to prevent path traversal."""
    AUTOTRAIN_DIR = telemetry.AUTOTRAIN_DIR

    # Normal case
    run_dir = telemetry.get_run_dir("test_run")
    assert run_dir.name == "test_run"
    assert str(run_dir.parent).endswith("runs")

    # Absolute path traversal
    evil_abs = "/etc/passwd"
    run_dir = telemetry.get_run_dir(evil_abs)
    assert run_dir.name == "passwd"  # Should take the name component
    assert str(run_dir).startswith(str(AUTOTRAIN_DIR))

    # Relative path traversal
    evil_rel = "../../evil"
    run_dir = telemetry.get_run_dir(evil_rel)
    assert run_dir.name == "evil"
    assert str(run_dir).startswith(str(AUTOTRAIN_DIR))
    assert ".." not in str(run_dir)

    # Edge case: empty string
    run_id = telemetry.get_run_id()
    run_dir = telemetry.get_run_dir("")
    assert run_dir.name == run_id # Should fall back to get_run_id()

    # Edge case: .
    run_dir = telemetry.get_run_dir(".")
    assert run_dir.name == run_id

    # Edge case: ..
    run_dir = telemetry.get_run_dir("..")
    assert run_dir.name == run_id

def test_get_state_no_nameerror():
    """Verify that get_state no longer triggers NameError."""
    # This might fail if AUTOTRAIN_DIR is not writable in this environment,
    # but we just want to ensure target_run_id is gone.
    try:
        telemetry.get_state("non_existent_run")
    except NameError as e:
        pytest.fail(f"get_state triggered NameError: {e}")
    except Exception:
        pass # Other errors (like file not found) are fine for this test
