import json
import time

from heidi_engine import telemetry


def test_state_cache_invalidation(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTRAIN_DIR", str(tmp_path))
    # Reset internal global state for testing
    monkeypatch.setattr(telemetry, "RUN_ID", "")
    monkeypatch.setattr(telemetry, "_initialized", False)

    run_id = telemetry.init_telemetry(config={"BASE_MODEL": "microsoft/phi-2"})

    # 1. Initial get should populate cache
    state1 = telemetry.get_state(run_id)
    # The status will be 'running' because init_telemetry sets it to 'running'
    # Actually init_telemetry calls save_state which sets 'running'
    assert state1["status"] == "running"

    # 2. Update state via save_state should invalidate cache
    state1["status"] = "completed"
    telemetry.save_state(state1, run_id)

    # 3. Next get should see the update (because cache was invalidated)
    state2 = telemetry.get_state(run_id)
    assert state2["status"] == "completed"


def test_state_cache_ttl(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTRAIN_DIR", str(tmp_path))
    monkeypatch.setattr(telemetry, "RUN_ID", "")
    monkeypatch.setattr(telemetry, "_initialized", False)

    # Use a short TTL for testing
    monkeypatch.setattr(telemetry._state_cache, "_ttl", 0.1)

    run_id = telemetry.init_telemetry(config={"BASE_MODEL": "microsoft/phi-2"})

    state = telemetry.get_state(run_id)
    assert state["status"] == "running"

    # Manually modify the file on disk bypassing telemetry.save_state
    state_file = telemetry.get_state_path(run_id)
    with open(state_file, "r") as f:
        data = json.load(f)
    data["status"] = "completed"
    with open(state_file, "w") as f:
        json.dump(data, f)

    # Immediate get should still return cached (TTL hasn't expired)
    assert telemetry.get_state(run_id)["status"] == "running"

    # Wait for TTL
    time.sleep(0.15)

    # Now it should detect the file change via metadata validation
    assert telemetry.get_state(run_id)["status"] == "completed"
