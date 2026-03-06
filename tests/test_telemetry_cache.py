import time

from heidi_engine.telemetry import (
    emit_event,
    flush_events,
    get_gpu_summary,
    get_last_event_ts,
    get_state,
    init_telemetry,
    save_state,
)


def test_state_cache_hit_miss():
    run_id = init_telemetry(force=True)

    # First call - cache miss, should load from disk
    state1 = get_state(run_id)
    assert state1["run_id"] == run_id

    # Second call - cache hit
    state2 = get_state(run_id)
    assert state2 == state1


def test_state_cache_invalidation():
    run_id = init_telemetry(force=True)
    state = get_state(run_id)

    # Update state and save (should invalidate cache)
    state["current_stage"] = "test_stage"
    save_state(state, run_id)

    # Should get new state from disk
    new_state = get_state(run_id)
    assert new_state["current_stage"] == "test_stage"


def test_state_cache_ttl():
    run_id = init_telemetry(force=True)
    get_state(run_id)  # Fill cache

    # Wait for TTL (0.5s) to expire
    time.sleep(0.6)

    # Should be a cache miss and reload from disk
    state = get_state(run_id)
    assert state["run_id"] == run_id


def test_gpu_cache():
    # Fill cache
    get_gpu_summary()

    # Should be cache hit
    start = time.perf_counter()
    for _ in range(10):
        get_gpu_summary()
    end = time.perf_counter()

    # Even if nvidia-smi is missing, it should be very fast from cache
    assert (end - start) < 0.1


def test_event_ts_cache():
    run_id = init_telemetry(force=True)
    emit_event("test", "test message", run_id=run_id)
    flush_events()  # Flush to disk so get_last_event_ts can read it

    # Fill cache
    ts1 = get_last_event_ts(run_id)
    assert ts1 is not None

    # Should be cache hit
    ts2 = get_last_event_ts(run_id)
    assert ts2 == ts1
