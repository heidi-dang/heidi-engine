
import os
import json
import time
import threading
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from heidi_engine import telemetry

@pytest.fixture
def temp_run_dir(tmp_path):
    run_id = "test_run"
    run_dir = tmp_path / "runs" / run_id
    run_dir.mkdir(parents=True)
    state_file = run_dir / "state.json"

    initial_state = {
        "run_id": run_id,
        "status": "running",
        "counters": telemetry.get_default_counters(),
        "usage": telemetry.get_default_usage(),
        "updated_at": "2023-01-01T00:00:00Z"
    }

    with open(state_file, "w") as f:
        json.dump(initial_state, f)

    # Mock AUTOTRAIN_DIR to use our temp path
    with patch("heidi_engine.telemetry.AUTOTRAIN_DIR", str(tmp_path)):
        yield run_id, state_file

def test_cache_ttl(temp_run_dir):
    run_id, state_file = temp_run_dir

    # Clear cache for this run_id
    telemetry._state_cache._cache.pop(run_id, None)

    # Set TTL to a reasonable value for testing
    original_ttl = telemetry._state_cache._ttl
    telemetry._state_cache._ttl = 0.5

    try:
        # First call should read from disk
        with patch("builtins.open", wraps=open) as mock_open:
            state1 = telemetry._state_cache.get(run_id)
            assert state1["run_id"] == run_id
            assert mock_open.call_count == 1

        # Second call within TTL should NOT read from disk
        with patch("builtins.open", wraps=open) as mock_open:
            state2 = telemetry._state_cache.get(run_id)
            assert state2["run_id"] == run_id
            assert mock_open.call_count == 0

        # Wait for TTL to expire
        time.sleep(0.6)

        # Third call after TTL should read from disk (or at least stat)
        with patch("builtins.open", wraps=open) as mock_open:
            state3 = telemetry._state_cache.get(run_id)
            assert state3["run_id"] == run_id
            # In our implementation, if mtime/size unchanged, it doesn't open even if TTL expired
            assert mock_open.call_count == 0
    finally:
        telemetry._state_cache._ttl = original_ttl

def test_cache_reload_on_modification(temp_run_dir):
    run_id, state_file = temp_run_dir
    telemetry._state_cache._cache.pop(run_id, None)

    # Set TTL to 0 to force stat check
    original_ttl = telemetry._state_cache._ttl
    telemetry._state_cache._ttl = 0

    try:
        # First call
        telemetry._state_cache.get(run_id)

        # Modify file
        new_state = {
            "run_id": run_id,
            "status": "completed",
            "counters": telemetry.get_default_counters(),
            "usage": telemetry.get_default_usage(),
            "updated_at": "2023-01-01T00:01:00Z"
        }
        time.sleep(0.1)
        with open(state_file, "w") as f:
            json.dump(new_state, f)

        # Second call should see modification and reload
        state = telemetry._state_cache.get(run_id)
        assert state["status"] == "completed"
    finally:
        telemetry._state_cache._ttl = original_ttl

def test_cache_serve_stale_on_error(temp_run_dir):
    run_id, state_file = temp_run_dir
    telemetry._state_cache._cache.pop(run_id, None)

    # Set TTL to 0 BEFORE first call to ensure subsequent calls check stat
    original_ttl = telemetry._state_cache._ttl
    telemetry._state_cache._ttl = 0

    # First call to populate cache
    telemetry._state_cache.get(run_id)

    try:
        # Corrupt the file
        with open(state_file, "w") as f:
            f.write("{invalid json}")

        # Force reload by changing mtime
        os.utime(state_file, (time.time() + 10, time.time() + 10))

        # Second call should fail to parse but return last good state
        state = telemetry._state_cache.get(run_id)
        assert state["run_id"] == run_id
        assert state["status"] == "running" # From initial state
        assert state["_stale"] is True
        assert "_cache_error" in state
    finally:
        telemetry._state_cache._ttl = original_ttl

def test_cache_concurrency(temp_run_dir):
    run_id, state_file = temp_run_dir
    telemetry._state_cache._cache.pop(run_id, None)

    def worker():
        for _ in range(100):
            telemetry._state_cache.get(run_id)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert run_id in telemetry._state_cache._cache
