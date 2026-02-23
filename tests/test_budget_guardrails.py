import pytest

heidi_cpp = pytest.importorskip("heidi_cpp")
import time
import json
import os
import shutil
from unittest import mock

def test_engine_throttles_high_cpu_spike():
    """
    Simulates a running environment where max_cpu_pct is mocked impossibly low.
    The C++ Core should emit 'pipeline_throttled' and pause execution until 
    max_wall_time_minutes expires or the system recovers.
    """
    test_dir = "build/test_budget_run"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir, exist_ok=True)

    # We CANNOT use MOCK_SUBPROCESSES here because that completely bypasses
    # the sampler and governor checks entirely for raw polling performance.
    # Instead, we will configure the system to use a dummy script and an impossible CPU constraint.
    os.environ["HEIDI_MOCK_SUBPROCESSES"] = "0"
    os.environ["RUN_ID"] = "budget_001"
    os.environ["OUT_DIR"] = test_dir
    os.environ["ROUNDS"] = "1"
    os.environ["HEIDI_REPO_ROOT"] = os.getcwd()
    os.environ["HEIDI_SIGNING_KEY"] = "test-key"
    os.environ["HEIDI_KEYSTORE_PATH"] = "test.enc"
    
    # Create dummy script so it doesn't actually train things
    os.makedirs("scripts", exist_ok=True)
    script_path = os.path.join("scripts", "01_teacher_generate.py")
    original_script = None
    if os.path.exists(script_path):
        with open(script_path, "r", encoding="utf-8") as f:
            original_script = f.read()
    with open(script_path, "w", encoding="utf-8") as f:
        f.write("print('dummy')")
    
    # Force extreme budget bounds (0% CPU allowed means it will instantly throttle)
    os.environ["MAX_CPU_PCT"] = "0.0"
    # Set a tiny global timeout (e.g. 0 minutes -> 0 seconds) to ensure the fail-closed loop aborts immediately
    os.environ["MAX_WALL_TIME_MINUTES"] = "0"

    engine = heidi_cpp.Core()
    engine.init("mock_config.yaml")

    engine.start("full")
    status_json = engine.tick(1) # Should transition COLLECTING -> evaluating teacher generate 
    
    state_dict = json.loads(status_json)
    
    # Verify Journal contains our pipeline_throttled and pipeline_error events
    journal_path = os.path.join(test_dir, "events.jsonl")
    assert os.path.exists(journal_path), "Journal was not written!"
    
    throttled_found = False
    error_found = False
    
    with open(journal_path, "r") as f:
        for line in f:
            evt = json.loads(line)
            if evt["event_type"] == "pipeline_throttled":
                assert "CPU spiked" in evt["message"]
                throttled_found = True
            if evt["event_type"] == "pipeline_error":
                assert "wall time limits waiting for resources" in evt["message"]
                error_found = True
                
    assert throttled_found, "Pipeline did not emit throttled event on 0% boundary."
    assert error_found, "Pipeline did not emit wall budget timeout error."
    
    # Verify State aborted tightly
    assert state_dict["state"] == "ERROR", "Pipeline did not cleanly halt into ERROR state"
    
    # Cleanup
    shutil.rmtree(test_dir)
    if original_script is None:
        os.remove(script_path)
    else:
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(original_script)
