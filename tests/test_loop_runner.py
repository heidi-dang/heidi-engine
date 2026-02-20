import os
import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from heidi_engine.loop_runner import PythonLoopRunner
try:
    from heidi_engine.loop_runner import CppLoopRunner
except ImportError:
    CppLoopRunner = None
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

def get_runner_classes():
    runners = [PythonLoopRunner]
    # We always include CppLoopRunner in the params if it was defined (even as dummy)
    # but the fixture will skip it if the extension is missing.
    from heidi_engine.loop_runner import CppLoopRunner as CppLR
    runners.append(CppLR)
    return runners

@pytest.fixture(params=get_runner_classes())
def runner_class(request, monkeypatch):
    if "CppLoopRunner" in str(request.param):
        try:
            import heidi_cpp
        except ImportError:
            pytest.skip("heidi_cpp extension not found. Skipping CppLoopRunner tests.")
        monkeypatch.setenv("HEIDI_MOCK_SUBPROCESSES", "1")
    return request.param

@patch('subprocess.run')
def test_loop_runner_full_mode(mock_run, temp_out_dir, mock_telemetry, runner_class):
    # Setup mock subprocess to succeed
    mock_run.return_value = MagicMock(returncode=0)
    
    runner = runner_class()
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
    
    # Check that scripts were "called" if using Python
    if "PythonLoopRunner" in str(runner_class):
        assert mock_run.call_count == 4
        telemetry.emit_event.assert_called()

@patch('subprocess.run')
def test_loop_runner_collect_mode(mock_run, temp_out_dir, mock_telemetry, monkeypatch, runner_class):
    # Setup mock subprocess to succeed
    mock_run.return_value = MagicMock(returncode=0)
    
    runner = runner_class()
    runner.start(mode="collect")
    
    # State transitions: COLLECTING -> VALIDATING -> IDLE
    assert runner.get_status()["state"] == "COLLECTING"
    
    runner.tick()
    assert runner.get_status()["state"] == "VALIDATING"

    runner.tick()
    assert runner.get_status()["state"] == "IDLE"

    # Only 2 steps should have run
    if "PythonLoopRunner" in str(runner_class):
        assert mock_run.call_count == 2
    
    # Trigger train now
    runner.action_train_now()
    assert runner.get_status()["state"] == "FINALIZING"
    
    runner.tick()
    assert runner.get_status()["state"] == "EVALUATING"
    
    runner.tick()
    assert runner.get_status()["state"] == "IDLE"
    
    # Now the other 2 steps should have run
    if "PythonLoopRunner" in str(runner_class):
        assert mock_run.call_count == 4

@patch('subprocess.run')
def test_loop_runner_with_tests(mock_run, temp_out_dir, mock_telemetry, monkeypatch, runner_class):
    monkeypatch.setenv("RUN_UNIT_TESTS", "1")
    mock_run.return_value = MagicMock(returncode=0)
    
    runner = runner_class()
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

    if "PythonLoopRunner" in str(runner_class):
        assert mock_run.call_count == 5
        tests_call = str(mock_run.mock_calls[2])
        assert "03_unit_test_gate.py" in tests_call
