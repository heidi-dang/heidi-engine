import json
import os
import time
from pathlib import Path

import pytest

from heidi_engine.telemetry import (
    emit_event,
    flush_events,
    get_gpu_summary,
    get_last_event_ts,
    get_state,
    init_telemetry,
    save_state,
)


@pytest.fixture
def run_id():
    rid = "test_cache_run"
    init_telemetry(run_id=rid, force=True)
    return rid


def test_state_cache(run_id):
    # Initial state
    state1 = get_state(run_id)
    assert state1["run_id"] == run_id

    # Update state manually (bypass save_state to check cache)
    state_file = Path(os.path.expanduser("~/.local/heidi_engine")) / "runs" / run_id / "state.json"
    with open(state_file, "r") as f:
        data = json.load(f)
    data["custom_field"] = "new_value"
    with open(state_file, "w") as f:
        json.dump(data, f)

    # get_state should still return cached value because TTL hasn't expired
    # and we haven't called save_state in this process to invalidate it.
    # Actually, get_state validates mtime_ns.
    # If we wrote to the file, mtime_ns changed.
    # Wait, let's check if my implementation re-validates mtime_ns.
    # Yes it does:
    # if stat_info.st_mtime_ns == mtime_ns and stat_info.st_size == size: return cached_state

    # So if I wait a bit for filesystem to update mtime (if it's low resolution)
    time.sleep(0.1)

    state2 = get_state(run_id)
    # Since we modified the file, it should NOT be from cache (mtime changed)
    assert state2.get("custom_field") == "new_value"


def test_state_cache_ttl(run_id):
    state1 = get_state(run_id)

    # Modify cache entry expire_at manually for testing if possible?
    # Better just wait.

    # save_state should invalidate cache
    state1["manual"] = "update"
    save_state(state1, run_id)

    # This should be a cache miss but then re-cached
    state2 = get_state(run_id)
    assert state2["manual"] == "update"


def test_last_event_ts_cache(run_id):
    emit_event("test", "message 1", run_id=run_id)
    flush_events()
    ts1 = get_last_event_ts(run_id)
    assert ts1 is not None

    # Emit another event
    emit_event("test", "message 2", run_id=run_id)
    flush_events()

    # Should still return ts1 if within 1.0s TTL
    ts2 = get_last_event_ts(run_id)
    assert ts2 == ts1

    # Wait for TTL
    time.sleep(1.1)
    ts3 = get_last_event_ts(run_id)
    assert ts3 != ts1
    assert ts3 is not None


def test_gpu_summary_cache():
    # First call
    s1 = get_gpu_summary()

    # Second call (should be cached)
    s2 = get_gpu_summary()
    assert s1 == s2


def test_last_event_ts_small_file(run_id):
    # Test the fix for small files (less than 500 bytes)
    # Clear events
    events_file = (
        Path(os.path.expanduser("~/.local/heidi_engine")) / "runs" / run_id / "events.jsonl"
    )
    if events_file.exists():
        events_file.unlink()

    # Force cache invalidation
    from heidi_engine.telemetry import _event_ts_cache

    _event_ts_cache.clear()

    # Emit one small event
    emit_event("tiny", "m", run_id=run_id)
    flush_events()

    assert events_file.stat().st_size < 500

    ts = get_last_event_ts(run_id)
    assert ts is not None
