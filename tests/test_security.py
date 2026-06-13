import os
import pytest
import json
from pathlib import Path
from heidi_engine.telemetry import get_run_dir, get_state, AUTOTRAIN_DIR

def test_get_run_dir_sanitization():
    # Test that absolute paths are sanitized
    run_dir = get_run_dir("/tmp/evil")
    assert "/tmp/evil" not in str(run_dir)
    assert run_dir.name == "evil"

    # Test that parent directory markers are sanitized
    run_dir = get_run_dir("../evil")
    assert ".." not in str(run_dir.name)
    assert run_dir.name == "evil"

    # Test that it still stays under AUTOTRAIN_DIR/runs
    expected_base = Path(AUTOTRAIN_DIR).expanduser() / "runs"
    # Normalize paths for comparison
    assert expected_base.resolve() in run_dir.resolve().parents

def test_get_state_name_error_regression(tmp_path):
    # Setup a dummy run directory and state file
    run_id = "test_run_123"
    # We need to mock AUTOTRAIN_DIR or just rely on the fact that it will try to read a file
    # get_state calls get_state_path which calls get_run_dir

    run_dir = get_run_dir(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    state_file = run_dir / "state.json"
    with open(state_file, "w") as f:
        json.dump({"run_id": run_id, "status": "running"}, f)

    try:
        # This should hit the broken cache check after verifying file existence
        get_state(run_id)
    except NameError as e:
        pytest.fail(f"get_state raised NameError: {e}")
    except TypeError as e:
        pytest.fail(f"get_state raised TypeError: {e}")
    finally:
        # Cleanup
        if state_file.exists():
            state_file.unlink()
        if run_dir.exists():
            run_dir.rmdir()
