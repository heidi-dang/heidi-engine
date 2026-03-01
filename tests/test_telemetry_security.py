from pathlib import Path

from heidi_engine.telemetry import AUTOTRAIN_DIR, get_run_dir


def test_get_run_dir_traversal():
    """Test that get_run_dir prevents path traversal by sanitizing the run_id."""
    traversal_id = "../../traversal_test"
    run_dir = get_run_dir(traversal_id)

    # Check if the resolved path escapes the runs directory
    runs_dir = Path(AUTOTRAIN_DIR) / "runs"
    assert runs_dir in run_dir.parents, (
        f"Path traversal successful: {run_dir} is outside {runs_dir}"
    )


def test_get_run_dir_sanitization():
    """Test that get_run_dir sanitizes run_id (should pass after fix)."""
    traversal_id = "../../traversal_test"
    run_dir = get_run_dir(traversal_id)

    # After fix, run_dir should be something like AUTOTRAIN_DIR/runs/traversal_test
    # and not escape the runs directory.
    assert run_dir.name == "traversal_test"
    assert ".." not in str(run_dir)
