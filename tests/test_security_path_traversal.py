import os
import shutil
from pathlib import Path
import pytest
from heidi_engine.telemetry import sanitize_run_id, get_run_dir

def test_sanitize_run_id():
    assert sanitize_run_id("safe_id") == "safe_id"
    assert sanitize_run_id("../../etc/passwd") == "passwd"
    assert sanitize_run_id("..") == "invalid_run_id"
    assert sanitize_run_id("") == "invalid_run_id"
    assert sanitize_run_id("/") == "invalid_run_id"
    assert sanitize_run_id("./safe") == "safe"

def test_get_run_dir_sanitization():
    malicious_id = "../../malicious"
    run_dir = get_run_dir(malicious_id)

    assert ".." not in run_dir.parts
    assert run_dir.name == "malicious"
    assert run_dir.parent.name == "runs"

def test_sanitize_run_id_edge_cases():
    assert sanitize_run_id("a/b/c") == "c"
    # Testing that it handles spaces if they are part of the name
    assert sanitize_run_id("safe id") == "safe id"
