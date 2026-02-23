
import pytest
from pathlib import Path
from heidi_engine.telemetry import get_run_dir, AUTOTRAIN_DIR

def test_get_run_dir_path_traversal():
    """Test that get_run_dir is protected against path traversal."""
    malicious_run_id = "../../../tmp/evil_run"
    run_dir = get_run_dir(malicious_run_id)

    # The resolved path should be under AUTOTRAIN_DIR/runs
    expected_parent = Path(AUTOTRAIN_DIR) / "runs"

    # Check if the resolved run_dir is actually a child of the expected parent
    # In the vulnerable version, this will be False if it escaped
    assert expected_parent in run_dir.parents
    assert run_dir.name == "evil_run"
    assert ".." not in str(run_dir)

def test_get_run_dir_safe():
    """Test get_run_dir with a safe run_id."""
    safe_run_id = "run_20240215_123456"
    run_dir = get_run_dir(safe_run_id)
    expected = Path(AUTOTRAIN_DIR) / "runs" / safe_run_id
    assert run_dir == expected
