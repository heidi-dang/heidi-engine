import pytest
import os
import json
import subprocess
from heidi_engine.utils.io_jsonl import load_jsonl


def test_schema_violation_missing_keys(tmp_path):
    bad_jsonl = tmp_path / "bad_schema.jsonl"
    # Missing 'prev_hash'
    bad_data = {
        "event_version": "1.0",
        "ts": "2026-02-20T10:00:00Z",
        "run_id": "test_001",
        "round": 1,
        "stage": "generate",
        "level": "info",
        "event_type": "test",
        "message": "hello",
        "counters_delta": {},
        "usage_delta": {},
        "artifact_paths": [],
    }
    bad_jsonl.write_text(json.dumps(bad_data) + "\n")

    with pytest.raises(ValueError) as e:
        load_jsonl(str(bad_jsonl), is_journal=True)
    assert (
        "Missing keys" in str(e.value)
        or "schema version" in str(e.value)
        or "JSON parsing error" in str(e.value)
    )


def test_schema_violation_bad_version(tmp_path):
    bad_jsonl = tmp_path / "bad_version.jsonl"
    # Unsupported version
    bad_data = {
        "event_version": "2.0",
        "ts": "2026-02-20T10:00:00Z",
        "run_id": "test_001",
        "round": 1,
        "stage": "generate",
        "level": "info",
        "event_type": "test",
        "message": "hello",
        "counters_delta": {},
        "usage_delta": {},
        "artifact_paths": [],
        "prev_hash": "abc",
    }
    bad_jsonl.write_text(json.dumps(bad_data) + "\n")

    with pytest.raises(ValueError) as e:
        load_jsonl(str(bad_jsonl), is_journal=True)
    assert "Unsupported schema version" in str(e.value) or "JSON parsing error" in str(e.value)


def test_schema_violation_oversized(tmp_path):
    bad_jsonl = tmp_path / "garbage.jsonl"
    bad_jsonl.write_text("not a json\n")

    with pytest.raises(ValueError) as e:
        load_jsonl(str(bad_jsonl), is_journal=True)
    assert "JSON parsing error" in str(e.value)
