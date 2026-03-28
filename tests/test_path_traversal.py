
import os
import pytest
from pathlib import Path
from heidi_engine.telemetry import get_run_dir, init_telemetry, get_run_id

def test_run_id_sanitization_basename():
    """Test that run_id is sanitized using basename."""
    os.environ["AUTOTRAIN_DIR"] = "/tmp/heidi_test"
    # Set a traversal ID in environment
    os.environ["RUN_ID"] = "../../etc/passwd"

    # Force re-evaluation of RUN_ID by clearing global if necessary (not really possible without reload)
    # But get_run_id will read from environment if RUN_ID global is empty
    import heidi_engine.telemetry
    heidi_engine.telemetry.RUN_ID = ""

    run_id = get_run_id()
    assert run_id == "passwd"

    run_dir = get_run_dir()
    assert "etc" not in str(run_dir)
    assert run_dir.name == "passwd"

def test_run_id_sanitization_dangerous_fallback():
    """Test that dangerous or empty run_id falls back to a safe one."""
    os.environ["AUTOTRAIN_DIR"] = "/tmp/heidi_test"

    # Test with ".."
    import heidi_engine.telemetry
    heidi_engine.telemetry.RUN_ID = ".."

    run_dir = get_run_dir()
    assert run_dir.name.startswith("safe_run_")
    assert run_dir.name != ".."

def test_init_telemetry_sanitization():
    """Test that init_telemetry sanitizes the provided run_id."""
    autotrain_dir = "/tmp/heidi_test"
    os.environ["AUTOTRAIN_DIR"] = autotrain_dir

    import heidi_engine.telemetry
    heidi_engine.telemetry.AUTOTRAIN_DIR = autotrain_dir
    heidi_engine.telemetry._initialized = False

    # Try initializing with traversal ID
    final_id = init_telemetry(run_id="../../../tmp/traversal_test")

    assert "tmp" not in final_id
    assert final_id == "traversal_test"

    run_dir = get_run_dir(final_id)
    assert run_dir.name == "traversal_test"
    # Ensure it's inside the autotrain_dir/runs folder
    assert run_dir.is_relative_to(Path(autotrain_dir) / "runs")
