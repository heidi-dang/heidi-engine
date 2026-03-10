
import os
import pytest
from pathlib import Path
from heidi_engine.telemetry import get_run_dir, AUTOTRAIN_DIR

def test_get_run_dir_path_traversal_protection():
    """
    Test that get_run_dir sanitizes run_id to prevent path traversal.
    """
    malicious_run_id = "../../../../../../../../../etc/passwd"
    run_dir = get_run_dir(malicious_run_id)

    # It should only take the 'name' part (passwd)
    assert run_dir.name == "passwd"

    # It should be located inside AUTOTRAIN_DIR/runs
    expected_base = Path(AUTOTRAIN_DIR).resolve() / "runs"
    assert str(run_dir.resolve()).startswith(str(expected_base))

def test_get_run_dir_absolute_path_protection():
    """
    Test that get_run_dir sanitizes absolute run_id to prevent escaping.
    """
    malicious_run_id = "/tmp/evil_run"
    run_dir = get_run_dir(malicious_run_id)

    # It should only take the 'name' part (evil_run)
    assert run_dir.name == "evil_run"

    # It should be located inside AUTOTRAIN_DIR/runs
    expected_base = Path(AUTOTRAIN_DIR).resolve() / "runs"
    assert str(run_dir.resolve()).startswith(str(expected_base))
