import os
import json
import pytest
from pathlib import Path
from heidi_engine.telemetry import (
    init_telemetry, get_state, update_counters, save_state,
    get_gpu_summary, get_last_event_ts, emit_event, flush_events
)

def test_state_cache_invalidation(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTRAIN_DIR", str(tmp_path))
    run_id = "test_cache"
    init_telemetry(run_id=run_id, force=True)

    # Initial state
    state1 = get_state(run_id)
    assert state1["counters"]["teacher_generated"] == 0

    # Update state via official API (should invalidate cache)
    update_counters({"teacher_generated": 10}, run_id=run_id)

    state2 = get_state(run_id)
    assert state2["counters"]["teacher_generated"] == 10

def test_state_cache_invalidation_none(tmp_path, monkeypatch):
    # Test that invalidate(None) correctly resolves to the active run_id
    monkeypatch.setenv("AUTOTRAIN_DIR", str(tmp_path))
    monkeypatch.setenv("RUN_ID", "test_none_run")
    init_telemetry(force=True)

    # Fill cache
    get_state()

    # Update via None run_id
    update_counters({"teacher_generated": 42}) # update_counters calls save_state(..., run_id=None)

    # Should get fresh value
    state = get_state()
    assert state["counters"]["teacher_generated"] == 42

def test_cache_mutation_isolation(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTRAIN_DIR", str(tmp_path))
    run_id = "test_mutation"
    init_telemetry(run_id=run_id, force=True)

    state = get_state(run_id)
    state["counters"]["teacher_generated"] = 999

    # Calling get_state again should NOT return 999
    state2 = get_state(run_id)
    assert state2["counters"]["teacher_generated"] == 0

    # Manual file modification (bypass cache if TTL expires)
    # Since default TTL is 0.5s, we might need to wait or mock time if we want to test TTL
    # But here we just test that official updates work.

def test_gpu_summary_caching():
    # Calling twice should return same object (or copy) and be fast
    res1 = get_gpu_summary()
    res2 = get_gpu_summary()
    assert res1 == res2

def test_last_event_ts_caching(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOTRAIN_DIR", str(tmp_path))
    run_id = "test_ts"
    init_telemetry(run_id=run_id, force=True)

    emit_event("test", "msg1", run_id=run_id)
    flush_events()
    ts1 = get_last_event_ts(run_id)
    assert ts1 is not None

    # Emit another event
    emit_event("test", "msg2", run_id=run_id)
    flush_events()

    # Should still get ts1 due to 1s TTL
    ts2 = get_last_event_ts(run_id)
    assert ts2 == ts1
