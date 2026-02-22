
import os
import shutil
from pathlib import Path
import pytest
from heidi_engine.telemetry import get_run_dir, _rotate_events_log

def test_get_run_dir_traversal():
    """Test that get_run_dir is hardened against path traversal."""
    dummy_dir = Path("/tmp/heidi_test_telemetry")
    if dummy_dir.exists():
        shutil.rmtree(dummy_dir)
    dummy_dir.mkdir(parents=True)

    # We need to monkeypatch AUTOTRAIN_DIR in the module if possible,
    # but here we'll just use the env var and hope it re-evaluates or we can work around it.
    # Actually, heidi_engine.telemetry.AUTOTRAIN_DIR is set at import time.
    import heidi_engine.telemetry
    original_autotrain_dir = heidi_engine.telemetry.AUTOTRAIN_DIR
    heidi_engine.telemetry.AUTOTRAIN_DIR = str(dummy_dir)

    try:
        # Malicious run_id
        malicious_id = "../../malicious"
        run_dir = get_run_dir(malicious_id)

        # Should be sanitized to 'malicious' and stay within dummy_dir/runs
        expected_base = (dummy_dir / "runs").resolve()
        assert expected_base in run_dir.resolve().parents
        assert run_dir.name == "malicious"

        # Test with dot
        dot_id = "."
        run_dir = get_run_dir(dot_id)
        assert run_dir.name == "default_run"

    finally:
        heidi_engine.telemetry.AUTOTRAIN_DIR = original_autotrain_dir
        shutil.rmtree(dummy_dir)

def test_rotate_events_log_security(capsys):
    """Test that _rotate_events_log prevents rotation outside of runs directory."""
    dummy_dir = Path("/tmp/heidi_test_rotate_sec")
    if dummy_dir.exists():
        shutil.rmtree(dummy_dir)
    dummy_dir.mkdir(parents=True)
    (dummy_dir / "runs").mkdir()

    import heidi_engine.telemetry
    original_autotrain_dir = heidi_engine.telemetry.AUTOTRAIN_DIR
    heidi_engine.telemetry.AUTOTRAIN_DIR = str(dummy_dir)

    try:
        # Create a file outside of dummy_dir/runs
        outside_file = Path("/tmp/outside_events_test.jsonl")
        outside_file.touch()

        _rotate_events_log(outside_file)

        # Check that an error was printed to stderr
        captured = capsys.readouterr()
        assert "Security violation" in captured.err

        # Verify no rotation occurred
        assert not Path("/tmp/outside_events_test.jsonl.1").exists()

        outside_file.unlink()
    finally:
        heidi_engine.telemetry.AUTOTRAIN_DIR = original_autotrain_dir
        shutil.rmtree(dummy_dir)
