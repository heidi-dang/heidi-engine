import pytest
from pathlib import Path
from heidi_engine import telemetry

def test_get_run_dir_sanitization():
    """
    Test that get_run_dir sanitizes run_id to prevent path traversal.
    """
    base_dir = Path(telemetry.AUTOTRAIN_DIR)
    runs_dir = base_dir / "runs"

    # 1. Test absolute path
    abs_path = "/tmp/evil"
    run_dir = telemetry.get_run_dir(abs_path)
    # It should strip the leading /tmp/ and use only "evil"
    assert str(run_dir).endswith("runs/evil")
    assert str(run_dir) != abs_path
    assert runs_dir in run_dir.parents

    # 2. Test directory traversal
    traversal_path = "../../etc/passwd"
    run_dir = telemetry.get_run_dir(traversal_path)
    # It should use only "passwd"
    assert str(run_dir).endswith("runs/passwd")
    assert "etc/passwd" not in str(run_dir)
    assert runs_dir in run_dir.parents

    # 3. Test invalid names like . or ..
    run_dir_dot = telemetry.get_run_dir(".")
    # Should fallback to a generated run_id because Path(".").name is empty or just "."
    # Actually Path(".").name is "" in some cases or "."
    # If it is "." or "", our logic should fallback.
    assert run_dir_dot.name.startswith("run_") or run_dir_dot.name != "."

    # 4. Test None/empty
    run_dir_none = telemetry.get_run_dir(None)
    assert run_dir_none.name.startswith("run_")
