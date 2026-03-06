import json
import os
import time

from heidi_engine.telemetry import get_state, init_telemetry, save_state


def test_state_cache_invalidation():
    run_id = "test_cache_run"
    init_telemetry(run_id=run_id, force=True)

    # First call - reads from disk
    state1 = get_state(run_id)
    state1["status"] = "test_status"

    # Save - should invalidate cache
    save_state(state1, run_id)

    # Second call - should read the new value (not the old cached one)
    state2 = get_state(run_id)
    assert state2["status"] == "test_status"


def test_state_cache_ttl():
    run_id = "test_ttl_run"
    init_telemetry(run_id=run_id, force=True)

    # Fill cache
    get_state(run_id)

    # Manually modify file on disk
    state_file = os.path.expanduser(f"~/.local/heidi_engine/runs/{run_id}/state.json")
    with open(state_file, "r") as f:
        data = json.load(f)
    data["status"] = "modified_on_disk"
    with open(state_file, "w") as f:
        json.dump(data, f)

    # Should still get old status from cache
    assert get_state(run_id)["status"] != "modified_on_disk"

    # Wait for TTL (0.5s)
    time.sleep(0.6)

    # Should now get new status
    assert get_state(run_id)["status"] == "modified_on_disk"
