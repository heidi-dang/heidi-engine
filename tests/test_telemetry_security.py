
import os
import sys
import pytest
from pathlib import Path
from heidi_engine.telemetry import get_run_dir, _rotate_events_log, AUTOTRAIN_DIR

class TestTelemetrySecurity:
    """Security tests for telemetry module."""

    def test_get_run_dir_traversal(self, tmp_path):
        """Test that get_run_dir prevents path traversal."""
        # Mock AUTOTRAIN_DIR
        original_autotrain_dir = os.environ.get("AUTOTRAIN_DIR")
        os.environ["AUTOTRAIN_DIR"] = str(tmp_path)

        try:
            runs_base = (tmp_path / "runs").resolve()
            runs_base.mkdir(parents=True, exist_ok=True)

            run_id = "../evil_run"
            run_dir = get_run_dir(run_id)
            resolved_run_dir = run_dir.resolve()

            # Sanitized to "evil_run"
            assert resolved_run_dir.name == "evil_run"
            assert resolved_run_dir.parent == runs_base

            # Edge cases
            assert get_run_dir("..").name == "default_run"
            assert get_run_dir(".").name == "default_run"
            assert get_run_dir("").name == "default_run"
        finally:
            if original_autotrain_dir:
                os.environ["AUTOTRAIN_DIR"] = original_autotrain_dir
            else:
                del os.environ["AUTOTRAIN_DIR"]

    def test_rotate_events_log_traversal(self, tmp_path, capsys):
        """Test that _rotate_events_log prevents rotation outside runs directory."""
        # Mock AUTOTRAIN_DIR
        original_autotrain_dir = os.environ.get("AUTOTRAIN_DIR")
        os.environ["AUTOTRAIN_DIR"] = str(tmp_path)

        try:
            runs_base = (tmp_path / "runs").resolve()
            runs_base.mkdir(parents=True, exist_ok=True)

            # 1. Legitimate rotation
            safe_run_dir = runs_base / "safe_run"
            safe_run_dir.mkdir(exist_ok=True)
            safe_events_file = safe_run_dir / "events.jsonl"
            safe_events_file.touch()

            _rotate_events_log(safe_events_file)
            assert (safe_run_dir / "events.jsonl.1").exists()

            # 2. Malicious rotation (outside runs base)
            unsafe_file = tmp_path / "secret.txt"
            unsafe_file.touch()

            _rotate_events_log(unsafe_file)

            captured = capsys.readouterr()
            assert "Security breach attempt" in captured.err
            assert not (tmp_path / "secret.txt.1").exists()
        finally:
            if original_autotrain_dir:
                os.environ["AUTOTRAIN_DIR"] = original_autotrain_dir
            else:
                del os.environ["AUTOTRAIN_DIR"]
