import pytest
from heidi_engine import dashboard

def test_get_default_state_structure():
    """Test that get_default_state returns the expected structure with default values."""
    state = dashboard.get_default_state()

    assert isinstance(state, dict)
    assert "run_id" in state
    assert "status" in state
    assert "current_round" in state
    assert "current_stage" in state
    assert "stop_requested" in state
    assert "pause_requested" in state
    assert "counters" in state
    assert "usage" in state

    assert state["status"] == "unknown"
    assert state["current_round"] == 0
    assert state["current_stage"] == "initializing"
    assert state["stop_requested"] is False
    assert state["pause_requested"] is False

    # Check counters
    counters = state["counters"]
    assert counters["teacher_generated"] == 0
    assert counters["teacher_failed"] == 0
    assert counters["raw_written"] == 0
    assert counters["validated_ok"] == 0
    assert counters["rejected_schema"] == 0
    assert counters["rejected_secret"] == 0
    assert counters["rejected_dedupe"] == 0
    assert counters["test_pass"] == 0
    assert counters["test_fail"] == 0
    assert counters["train_step"] == 0
    assert counters["train_loss"] == 0.0
    assert counters["eval_json_parse_rate"] == 0.0
    assert counters["eval_format_rate"] == 0.0

    # Check usage
    usage = state["usage"]
    assert usage["requests_sent"] == 0
    assert usage["input_tokens"] == 0
    assert usage["output_tokens"] == 0
    assert usage["rate_limits_hit"] == 0
    assert usage["retries"] == 0
    assert usage["estimated_cost_usd"] == 0.0

def test_get_default_state_with_global_run_id(monkeypatch):
    """Test that get_default_state uses the global run_id if set."""
    test_run_id = "test-run-123"
    monkeypatch.setattr(dashboard, "run_id", test_run_id)

    state = dashboard.get_default_state()
    assert state["run_id"] == test_run_id

def test_get_default_state_without_global_run_id(monkeypatch):
    """Test that get_default_state defaults to 'unknown' if global run_id is None."""
    monkeypatch.setattr(dashboard, "run_id", None)

    state = dashboard.get_default_state()
    assert state["run_id"] == "unknown"
