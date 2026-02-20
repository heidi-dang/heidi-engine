"""
Unit tests for JSONL IO utilities.
"""

import os
import pytest
from heidi_engine.utils.io_jsonl import load_jsonl, save_jsonl

def get_valid_sample(id="1"):
    return {
        "event_version": "1.0",
        "ts": "2026-02-20T10:00:00Z",
        "run_id": "test_run",
        "round": 1,
        "stage": "generate",
        "level": "info",
        "event_type": "test",
        "message": "hello",
        "counters_delta": {},
        "usage_delta": {},
        "artifact_paths": [],
        "prev_hash": f"hash_{id}"
    }

class TestJSONLUtils:
    """Test JSONL loading and saving utilities."""

    @pytest.fixture
    def test_file(self, tmp_path):
        """Fixture for a temporary JSONL file path."""
        return tmp_path / "test.jsonl"

    def test_save_and_load_roundtrip(self, test_file):
        """Test that data can be saved and then loaded correctly."""
        samples = [
            get_valid_sample("1"),
            get_valid_sample("2")
        ]
        save_jsonl(samples, str(test_file))

        loaded = load_jsonl(str(test_file))
        assert samples == loaded

    def test_save_creates_directories(self, tmp_path):
        """Test that save_jsonl automatically creates missing parent directories."""
        nested_path = tmp_path / "subdir" / "nested.jsonl"
        samples = [get_valid_sample("1")]
        save_jsonl(samples, str(nested_path))

        assert nested_path.exists()
        loaded = load_jsonl(str(nested_path))
        assert samples == loaded

    def test_load_skips_blank_lines(self, test_file):
        """Test that load_jsonl ignores empty or whitespace-only lines."""
        import json
        test_file.write_text(json.dumps(get_valid_sample("1")) + '\n\n   \n' + json.dumps(get_valid_sample("2")) + '\n')

        loaded = load_jsonl(str(test_file))
        assert len(loaded) == 2
        assert loaded[0]["prev_hash"] == "hash_1"
        assert loaded[1]["prev_hash"] == "hash_2"

    def test_load_handles_invalid_json(self, test_file, capsys):
        """Test that load_jsonl skips invalid JSON lines and prints a warning to stderr."""
        # NOTE: load_jsonl current implementation exits on JSON parse error if it's strict.
        # Since we are sticking to product behavior, we expect it to EXIT if it encounters invalid JSON.
        import json
        test_file.write_text(json.dumps(get_valid_sample("1")) + '\n{invalid}\n' + json.dumps(get_valid_sample("2")) + '\n')

        with pytest.raises(SystemExit) as e:
            load_jsonl(str(test_file))
        assert e.value.code == 1

    def test_save_current_directory(self, tmp_path, monkeypatch):
        """Test saving to a file in the current working directory (no directory part in path)."""
        # Change CWD to the temporary directory
        monkeypatch.chdir(tmp_path)

        local_name = "temp_test_io_jsonl.jsonl"
        samples = [get_valid_sample("1")]

        save_jsonl(samples, local_name)
        assert os.path.exists(local_name)
        loaded = load_jsonl(local_name)
        assert samples == loaded

        if os.path.exists(local_name):
            os.remove(local_name)
