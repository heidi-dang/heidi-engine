import pytest
import os
import time
import json
from pathlib import Path
from heidi_engine.telemetry import (
    get_state,
    save_state,
    init_telemetry,
    get_run_id,
    StateCache,
    HEIDI_STATUS_TTL_S
)

class TestTelemetryCache:
    @pytest.fixture
    def run_id(self):
        return init_telemetry(run_id="test_cache_run", force=True)

    def test_state_cache_invalidation_on_save(self, run_id):
        # Initial state
        state1 = get_state(run_id)
        state1["counters"]["test"] = 10
        save_state(state1, run_id)

        # Should be in cache now
        cached_state = get_state(run_id)
        assert cached_state["counters"]["test"] == 10

        # Modify state again
        state2 = get_state(run_id)
        state2["counters"]["test"] = 20
        save_state(state2, run_id)

        # Should NOT be stale (cache should have been invalidated)
        new_state = get_state(run_id)
        assert new_state["counters"]["test"] == 20

    def test_state_cache_ttl(self, run_id):
        # Initial state
        state = get_state(run_id)
        state["counters"]["test"] = 100
        save_state(state, run_id)

        # Get and verify
        assert get_state(run_id)["counters"]["test"] == 100

        # Manually modify file on disk to simulate external change
        state_file = Path(os.path.expanduser("~/.local/heidi_engine")) / "runs" / run_id / "state.json"
        with open(state_file, "r") as f:
            data = json.load(f)
        data["counters"]["test"] = 200
        with open(state_file, "w") as f:
            json.dump(data, f)

        # Should still return cached value due to TTL and no save_state call
        # (Assuming we call it within 0.5s)
        assert get_state(run_id)["counters"]["test"] == 100

        # Wait for TTL to expire
        time.sleep(HEIDI_STATUS_TTL_S + 0.1)

        # Now it should pick up the change
        assert get_state(run_id)["counters"]["test"] == 200

    def test_state_cache_mtime_validation(self, run_id):
        # Initial state
        state = get_state(run_id)
        state["counters"]["test"] = 300
        save_state(state, run_id)

        # Get and verify
        assert get_state(run_id)["counters"]["test"] == 300

        # Force TTL to expire
        time.sleep(HEIDI_STATUS_TTL_S + 0.1)

        # Call get_state, should still return 300 because mtime hasn't changed
        assert get_state(run_id)["counters"]["test"] == 300

        # Now touch the file
        state_file = Path(os.path.expanduser("~/.local/heidi_engine")) / "runs" / run_id / "state.json"
        os.utime(state_file, None)

        # Manually modify content but keep same size if possible, or just modify
        with open(state_file, "r") as f:
            data = json.load(f)
        data["counters"]["test"] = 400
        with open(state_file, "w") as f:
            json.dump(data, f)

        # Wait for TTL to expire so it checks metadata
        time.sleep(HEIDI_STATUS_TTL_S + 0.1)

        # Should pick up the change because mtime changed
        assert get_state(run_id)["counters"]["test"] == 400
