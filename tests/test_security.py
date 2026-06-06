import os
from pathlib import Path
from heidi_engine.telemetry import get_run_dir, AUTOTRAIN_DIR

def test_get_run_dir_sanitization():
    """
    Verify that get_run_dir correctly handles absolute paths and directory traversals.
    """
    # Test absolute path
    abs_path = "/tmp/malicious_run"
    run_dir = get_run_dir(abs_path)
    assert run_dir.name == "malicious_run"
    assert Path(AUTOTRAIN_DIR) in run_dir.parents

    # Test directory traversal with ..
    traversal_path = "../../../etc/passwd"
    run_dir = get_run_dir(traversal_path)
    assert run_dir.name == "passwd"
    assert Path(AUTOTRAIN_DIR) in run_dir.parents

    # Test just ..
    dotdot_path = ".."
    run_dir = get_run_dir(dotdot_path)
    assert run_dir.name != ".."
    assert Path(AUTOTRAIN_DIR) in run_dir.parents

    # Test just .
    dot_path = "."
    run_dir = get_run_dir(dot_path)
    assert run_dir.name != "."
    assert Path(AUTOTRAIN_DIR) in run_dir.parents

    # Test empty string
    empty_path = ""
    run_dir = get_run_dir(empty_path)
    assert run_dir.name != ""
    assert Path(AUTOTRAIN_DIR) in run_dir.parents
