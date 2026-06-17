
import pytest
import os
from pathlib import Path
from heidi_engine.telemetry import get_run_dir as get_run_dir_telemetry, AUTOTRAIN_DIR as TEL_BASE
from heidi_engine.dashboard import get_run_dir as get_run_dir_dashboard, AUTOTRAIN_DIR as DASH_BASE

def test_get_run_dir_sanitization():
    evil_paths = [
        "/tmp/evil",
        "../traversal",
        "../../etc/passwd",
        ".",
        "..",
        "./relative",
    ]

    for evil_id in evil_paths:
        # Telemetry check
        run_dir_tel = get_run_dir_telemetry(evil_id)
        # It should be under AUTOTRAIN_DIR/runs
        assert Path(TEL_BASE) in run_dir_tel.parents
        assert "runs" in [p.name for p in run_dir_tel.parents]
        assert run_dir_tel.name not in ["..", "."]

        # Dashboard check
        run_dir_dash = get_run_dir_dashboard(evil_id)
        assert Path(DASH_BASE) in run_dir_dash.parents
        assert "runs" in [p.name for p in run_dir_dash.parents]
        assert run_dir_dash.name not in ["..", "."]

if __name__ == "__main__":
    test_get_run_dir_sanitization()
