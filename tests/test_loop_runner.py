import os
import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from heidi_engine.loop_runner import PythonLoopRunner
from heidi_engine import telemetry

@pytest.fixture
def mock_telemetry(monkeypatch):
    """Disable actual telemetry file writing for tests."""
    monkeypatch.setattr(telemetry, "init_telemetry", MagicMock(return_value="test_run_123"))
    monkeypatch.setattr(telemetry, "emit_event", MagicMock())
    monkeypatch.setattr(telemetry, "set_status", MagicMock())
    monkeypatch.setattr(telemetry, "check_stop_requested", MagicMock(return_value=False))
    monkeypatch.setattr(telemetry, "check_pause_requested", MagicMock(return_value=False))

@pytest.fixture
def temp_out_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("OUT_DIR", str(tmp_path))
    monkeypatch.setenv("ROUNDS", "1")
    monkeypatch.setenv("RUN_ID", "test_run_123")
    return tmp_path

@patch('subprocess.run')
def test_python_loop_runner_full_mode(mock_run, temp_out_dir, mock_telemetry):
    # Setup mock subprocess to succeed
    mock_run.return_value = MagicMock(returncode=0)
    
    runner = PythonLoopRunner()
    runner.start(mode="full")
    
    # State transitions: COLLECTING -> VALIDATING -> FINALIZING -> EVALUATING -> IDLE
    assert runner.get_status()["state"] == "COLLECTING"
    
    runner.tick()
    assert runner.get_status()["state"] == "VALIDATING"
    
    runner.tick()
    assert runner.get_status()["state"] == "FINALIZING"
    
    runner.tick()
    assert runner.get_status()["state"] == "EVALUATING"
    
    runner.tick()
    assert runner.get_status()["state"] == "IDLE"
    
    # Check that scripts were "called"
    assert mock_run.call_count == 4
    calls = mock_run.mock_calls
    
    gen_call = str(calls[0])
    assert "01_teacher_generate.py" in gen_call
    
    val_call = str(calls[1])
    assert "02_validate_clean.py" in val_call

    train_call = str(calls[2])
    assert "04_train_qlora.py" in train_call

    eval_call = str(calls[3])
    assert "05_eval.py" in eval_call

    # Verify telemetry interactions
    telemetry.emit_event.assert_called()


@patch('subprocess.run')
def test_python_loop_runner_collect_mode(mock_run, temp_out_dir, mock_telemetry, monkeypatch):
    # Setup mock subprocess to succeed
    mock_run.return_value = MagicMock(returncode=0)
    
    runner = PythonLoopRunner()
    runner.start(mode="collect")
    
    # State transitions: COLLECTING -> VALIDATING -> IDLE
    assert runner.get_status()["state"] == "COLLECTING"
    
    runner.tick()
    assert runner.get_status()["state"] == "VALIDATING"

    runner.tick()
    assert runner.get_status()["state"] == "IDLE"

    # Only 2 steps should have run
    assert mock_run.call_count == 2
    
    # Trigger train now
    runner.action_train_now()
    assert runner.get_status()["state"] == "FINALIZING"
    
    runner.tick()
    assert runner.get_status()["state"] == "EVALUATING"
    
    runner.tick()
    assert runner.get_status()["state"] == "IDLE"
    
    # Now the other 2 steps should have run
    assert mock_run.call_count == 4

@patch('subprocess.run')
def test_python_loop_runner_with_tests(mock_run, temp_out_dir, mock_telemetry, monkeypatch):
    monkeypatch.setenv("RUN_UNIT_TESTS", "1")
    mock_run.return_value = MagicMock(returncode=0)
    
    runner = PythonLoopRunner()
    runner.start(mode="full")
    
    assert runner.get_status()["state"] == "COLLECTING"
    runner.tick()
    
    assert runner.get_status()["state"] == "VALIDATING"
    runner.tick()
    
    assert runner.get_status()["state"] == "TESTING"
    runner.tick()
    
    assert runner.get_status()["state"] == "FINALIZING"
    runner.tick()
    
    assert runner.get_status()["state"] == "EVALUATING"
    runner.tick()
    
    assert runner.get_status()["state"] == "IDLE"

    assert mock_run.call_count == 5
    tests_call = str(mock_run.mock_calls[2])
    assert "03_unit_test_gate.py" in tests_call

