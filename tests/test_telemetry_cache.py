
import os
import json
import time
import pytest
from pathlib import Path
from heidi_engine import telemetry

def test_state_cache_functional():
    run_id = "test_cache_run"
    telemetry.init_telemetry(run_id=run_id, force=True)

    # First call - cache miss
    state1 = telemetry.get_state()
    assert state1['run_id'] == run_id

    # Second call - should be a hit
    state2 = telemetry.get_state()
    assert state1 == state2

    # Invalidate cache
    telemetry.StateCache.get_instance().invalidate()

    # Third call - should be a miss but return same data
    state3 = telemetry.get_state()
    assert state1 == state3

def test_save_state_invalidates_cache():
    run_id = "test_invalidate_run"
    telemetry.init_telemetry(run_id=run_id, force=True)

    state1 = telemetry.get_state()
    assert state1['counters']['teacher_generated'] == 0

    # Update state and save
    state1['counters']['teacher_generated'] = 42
    telemetry.save_state(state1, run_id)

    # Should be invalidated and read new value
    state2 = telemetry.get_state()
    assert state2['counters']['teacher_generated'] == 42

def test_cache_validation_on_disk_change():
    run_id = "test_disk_change_run"
    telemetry.init_telemetry(run_id=run_id, force=True)

    state1 = telemetry.get_state()

    # Modify file on disk directly
    state_file = telemetry.get_state_path(run_id)
    with open(state_file, 'r') as f:
        data = json.load(f)
    data['counters']['teacher_generated'] = 777

    # Ensure mtime changes by sleeping a bit if necessary,
    # but usually file write changes it.
    time.sleep(0.01)
    with open(state_file, 'w') as f:
        json.dump(data, f)

    # Should detect disk change and return updated value even if TTL hasn't expired
    state2 = telemetry.get_state()
    assert state2['counters']['teacher_generated'] == 777
