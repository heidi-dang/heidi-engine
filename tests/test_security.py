import os
from pathlib import Path
from heidi_engine.telemetry import sanitize_run_id, get_run_dir, AUTOTRAIN_DIR

def test_sanitize_run_id():
    """Test that sanitize_run_id correctly strips path traversal components."""
    assert sanitize_run_id("test_run") == "test_run"
    assert sanitize_run_id("/etc/passwd") == "passwd"
    assert sanitize_run_id("../../etc/passwd") == "passwd"
    assert sanitize_run_id("..") == "default_run"
    assert sanitize_run_id(".") == "default_run"
    assert sanitize_run_id("") == "default_run"

def test_get_run_dir_sanitization():
    """Test that get_run_dir applies sanitization and prevents traversal."""
    run_dir = get_run_dir("/etc/passwd")
    # Should be under AUTOTRAIN_DIR/runs/
    expected_base = Path(AUTOTRAIN_DIR) / "runs"
    assert run_dir == expected_base / "passwd"

    run_dir_traversal = get_run_dir("../../etc/passwd")
    assert run_dir_traversal == expected_base / "passwd"

    run_dir_dotdot = get_run_dir("..")
    assert run_dir_dotdot == expected_base / "default_run"

def test_get_run_dir_environment_override():
    """Test that get_run_dir respects AUTOTRAIN_DIR but still sanitizes run_id."""
    # This test assumes the environment variable is not set or we can temporarily change it
    # But for a simple unit test, we just check if it's using the current AUTOTRAIN_DIR
    run_id = "normal_run"
    run_dir = get_run_dir(run_id)
    assert str(run_dir).startswith(AUTOTRAIN_DIR)
    assert run_dir.name == run_id
