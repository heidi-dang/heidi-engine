import pytest
from pathlib import Path
from heidi_engine.telemetry import sanitize_run_id as telemetry_sanitize, get_run_dir as telemetry_get_run_dir
from heidi_engine.dashboard import sanitize_run_id as dashboard_sanitize, get_run_dir as dashboard_get_run_dir


def test_sanitize_run_id_normal():
    assert telemetry_sanitize("run_123_abc") == "run_123_abc"
    assert dashboard_sanitize("run_123_abc") == "run_123_abc"


def test_sanitize_run_id_path_traversal():
    malicious_inputs = [
        "../../etc/passwd",
        "../run_123",
        "../../..",
        "run/../../secret",
        "run_123; rm -rf /",
        "run\\..\\..\\win",
    ]
    for inp in malicious_inputs:
        cleaned_t = telemetry_sanitize(inp)
        cleaned_d = dashboard_sanitize(inp)
        assert "/" not in cleaned_t
        assert "\\" not in cleaned_t
        assert ".." not in cleaned_t
        assert "/" not in cleaned_d
        assert "\\" not in cleaned_d
        assert ".." not in cleaned_d


def test_get_run_dir_sanitizes_path():
    p = telemetry_get_run_dir("../../etc/passwd")
    assert "etc" not in str(p) or "passwd" not in str(p) or str(p).endswith("runs/etcpasswd")
    assert not str(p).startswith("/etc")

    p2 = dashboard_get_run_dir("../../etc/passwd")
    assert not str(p2).startswith("/etc")
