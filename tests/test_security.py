import os
from pathlib import Path
import pytest
from heidi_engine.telemetry import get_run_dir as get_run_dir_telemetry
from heidi_engine.dashboard import get_run_dir as get_run_dir_dashboard

def test_get_run_dir_sanitization_telemetry():
    # Test absolute path traversal
    # In a vulnerable version, Path("/base") / "/etc" becomes Path("/etc")
    # We want it to stay under Path("/base") / "runs"

    dangerous_id = "/etc"
    run_dir = get_run_dir_telemetry(dangerous_id)

    # It should be something like .../runs/etc, not /etc
    assert str(run_dir) != "/etc"
    assert "runs" in run_dir.parts
    assert run_dir.name == "etc"

    # Test parent directory traversal
    dangerous_id = ".."
    run_dir = get_run_dir_telemetry(dangerous_id)
    # We want it to be .../runs/.. (sanitized to something else) OR just not escape runs/
    # If we use .name, Path("..").name is ".."
    # So we might need more than just .name if we want to block ".."

    assert ".." not in run_dir.parts[-1]

def test_get_run_dir_sanitization_dashboard():
    dangerous_id = "/etc"
    run_dir = get_run_dir_dashboard(dangerous_id)

    assert str(run_dir) != "/etc"
    assert "runs" in run_dir.parts
    assert run_dir.name == "etc"

    dangerous_id = ".."
    run_dir = get_run_dir_dashboard(dangerous_id)
    assert ".." not in run_dir.parts[-1]
