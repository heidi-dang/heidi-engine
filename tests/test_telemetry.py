import json
import time

import pytest

import heidi_engine.telemetry
from heidi_engine.telemetry import (
    _state_cache,
    emit_event,
    flush_events,
    get_gpu_summary,
    get_last_event_ts,
    get_state,
    init_telemetry,
    save_state,
)


@pytest.fixture
def clean_telemetry(tmp_path, monkeypatch):
    """Sets up a clean telemetry environment for testing."""
    monkeypatch.setenv("AUTOTRAIN_DIR", str(tmp_path))
    monkeypatch.setattr(heidi_engine.telemetry, "AUTOTRAIN_DIR", str(tmp_path))
    run_id = "test_run_telemetry"
    init_telemetry(run_id=run_id, force=True)
    # Ensure cache is clean
    _state_cache.invalidate()
    return run_id, tmp_path


class TestTelemetryCaching:
    """Test suite for telemetry caching and performance optimizations."""

    def test_get_state_caching(self, clean_telemetry):
        """Verify that get_state uses StateCache."""
        run_id, tmp_path = clean_telemetry

        # First call - should read from disk
        state1 = get_state(run_id)
        assert state1["run_id"] == run_id

        # Modify file on disk directly
        state_file = tmp_path / "runs" / run_id / "state.json"
        with open(state_file, "r") as f:
            data = json.load(f)
        data["status"] = "modified_on_disk"
        with open(state_file, "w") as f:
            json.dump(data, f)

        # Second call - should return cached version (status "running" or whatever it was)
        state2 = get_state(run_id)
        # Note: Resolve status might have changed it to something else but not "modified_on_disk"
        assert state2["status"] != "modified_on_disk"

        # Invalidate cache
        _state_cache.invalidate()

        # Third call - should return modified version
        state3 = get_state(run_id)
        assert state3["status"] == "modified_on_disk"

    def test_save_state_invalidates_cache(self, clean_telemetry):
        """Verify that save_state invalidates the cache."""
        run_id, _ = clean_telemetry

        state = get_state(run_id)
        state["status"] = "original"
        save_state(state, run_id)

        assert get_state(run_id)["status"] == "original"

        state["status"] = "updated"
        save_state(state, run_id)

        # Should get "updated" because save_state invalidated the cache
        assert get_state(run_id)["status"] == "updated"

    def test_get_last_event_ts_caching(self, clean_telemetry, monkeypatch):
        """Verify that get_last_event_ts uses caching."""
        run_id, tmp_path = clean_telemetry

        emit_event("test_type", "test message", run_id=run_id)
        flush_events()

        ts1 = get_last_event_ts(run_id)
        assert ts1 is not None

        # Manually add another event directly to disk
        events_file = tmp_path / "runs" / run_id / "events.jsonl"
        with open(events_file, "a") as f:
            f.write(json.dumps({"ts": "2024-01-01T00:00:00Z", "event_type": "manual"}) + "\n")

        # Should still return ts1 due to caching
        ts2 = get_last_event_ts(run_id)
        assert ts2 == ts1

        # Monkeypatch TTL to 0 to force refresh
        monkeypatch.setattr(heidi_engine.telemetry, "HEIDI_EVENT_TS_TTL_S", 0.0)

        ts3 = get_last_event_ts(run_id)
        assert ts3 == "2024-01-01T00:00:00Z"

    def test_get_last_event_ts_small_file(self, clean_telemetry, monkeypatch):
        """Verify that get_last_event_ts safely handles small files."""
        run_id, tmp_path = clean_telemetry
        events_file = tmp_path / "runs" / run_id / "events.jsonl"

        # Very small file (less than 500 bytes)
        small_event = {"ts": "small_ts", "event_type": "test"}
        events_file.write_text(json.dumps(small_event) + "\n")

        # Monkeypatch TTL to 0 to force fresh read
        monkeypatch.setattr(heidi_engine.telemetry, "HEIDI_EVENT_TS_TTL_S", 0.0)

        # Should not raise error and return small_ts
        ts = get_last_event_ts(run_id)
        assert ts == "small_ts"

    def test_get_gpu_summary_caching(self, monkeypatch):
        """Verify that get_gpu_summary uses caching."""
        # Reset cache
        monkeypatch.setattr(heidi_engine.telemetry, "_gpu_cache", {"data": {}, "last_check": 0})

        # First call
        get_gpu_summary()

        # Modify cache directly to see if it's used
        monkeypatch.setattr(
            heidi_engine.telemetry,
            "_gpu_cache",
            {"data": {"fake": "gpu"}, "last_check": time.time()},
        )

        res2 = get_gpu_summary()
        assert res2 == {"fake": "gpu"}
