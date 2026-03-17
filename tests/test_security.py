
import pytest
from pathlib import Path
from heidi_engine.telemetry import get_run_dir, get_state, AUTOTRAIN_DIR

def test_path_traversal_prevention():
    # Base runs directory
    runs_dir = Path(AUTOTRAIN_DIR) / "runs"

    # Traversal attempt: ../secrets
    traversal_run_id = "../secrets"
    resolved_path = get_run_dir(traversal_run_id)

    # It should resolve to runs/secrets, not the sibling directory
    assert resolved_path.name == "secrets"
    assert resolved_path.parent == runs_dir

    # Absolute path attempt: /tmp/secret
    abs_run_id = "/tmp/secret"
    resolved_abs = get_run_dir(abs_run_id)
    assert resolved_abs.name == "secret"
    assert resolved_abs.parent == runs_dir

def test_name_error_fixed():
    # This should not raise NameError even if file doesn't exist
    state = get_state("non_existent_run")
    assert state["status"] == "idle"

if __name__ == "__main__":
    test_path_traversal_prevention()
    test_name_error_fixed()
    print("Security verification tests passed!")
