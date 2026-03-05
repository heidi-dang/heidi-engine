import os
import time
import pytest
from heidi_engine import telemetry

def test_state_cache_functionality():
    run_id = telemetry.init_telemetry(force=True)
    state_path = telemetry.get_state_path(run_id)

    # Initial state
    state1 = telemetry.get_state(run_id)
    assert state1["run_id"] == run_id

    # Update state - should invalidate cache
    telemetry.update_counters({"teacher_generated": 1}, run_id=run_id)
    state2 = telemetry.get_state(run_id)
    assert state2["counters"]["teacher_generated"] == 1

    # TTL check - wait for TTL (0.5s)
    time.sleep(0.6)
    state3 = telemetry.get_state(run_id)
    assert state3["counters"]["teacher_generated"] == 1

def test_gpu_cache():
    # Call twice, second should be cached
    summary1 = telemetry.get_gpu_summary()
    summary2 = telemetry.get_gpu_summary()
    assert summary1 == summary2

def test_event_ts_cache():
    run_id = telemetry.init_telemetry(force=True)
    telemetry.emit_event("test", "test message", run_id=run_id)
    telemetry.flush_events()

    ts1 = telemetry.get_last_event_ts(run_id)
    assert ts1 is not None

    ts2 = telemetry.get_last_event_ts(run_id)
    assert ts1 == ts2
