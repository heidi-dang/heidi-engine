"""
Unit tests for JSONL IO utilities.
"""

import os
import json
import pytest
from heidi_engine.utils.io_jsonl import (
    load_jsonl,
    load_jsonl_strict,
    load_jsonl_best_effort,
    save_jsonl,
    REQUIRED_KEYS,
    SCHEMA_VERSION
)

class TestJSONLUtils:
    """Test JSONL loading and saving utilities."""

    @pytest.fixture
    def test_file(self, tmp_path):
        """Fixture for a temporary JSONL file path."""
        return tmp_path / "test.jsonl"

    def test_save_and_load_roundtrip(self, test_file):
        """Test that data can be saved and then loaded correctly."""
        samples = [
            {"id": "1", "text": "hello"},
            {"id": "2", "text": "world"}
        ]
        save_jsonl(samples, str(test_file))

        # use best_effort for general data
        loaded = load_jsonl_best_effort(str(test_file))
        assert samples == loaded

    def test_save_creates_directories(self, tmp_path):
        """Test that save_jsonl automatically creates missing parent directories."""
        nested_path = tmp_path / "subdir" / "nested.jsonl"
        samples = [{"a": 1}]
        save_jsonl(samples, str(nested_path))

        assert nested_path.exists()
        loaded = load_jsonl_best_effort(str(nested_path))
        assert samples == loaded

    def test_load_skips_blank_lines(self, test_file):
        """Test that load_jsonl ignores empty or whitespace-only lines."""
        test_file.write_text('{"id": 1}\n\n   \n{"id": 2}\n')

        loaded = load_jsonl_best_effort(str(test_file))
        assert len(loaded) == 2
        assert loaded[0]["id"] == 1
        assert loaded[1]["id"] == 2

    def test_load_handles_invalid_json(self, test_file, capsys):
        """Test that load_jsonl skips invalid JSON lines and prints a warning to stderr."""
        test_file.write_text('{"id": 1}\n{invalid}\n{"id": 2}\n')

        loaded = load_jsonl_best_effort(str(test_file))

        assert len(loaded) == 2
        assert loaded[0]["id"] == 1
        assert loaded[1]["id"] == 2

        captured = capsys.readouterr()
        assert "[WARN] Line 2: JSON parse error" in captured.err

    def test_save_current_directory(self, tmp_path, monkeypatch):
        """Test saving to a file in the current working directory (no directory part in path)."""
        # Change CWD to the temporary directory
        monkeypatch.chdir(tmp_path)

        local_name = "temp_test_io_jsonl.jsonl"
        samples = [{"test": "data"}]

        save_jsonl(samples, local_name)
        assert os.path.exists(local_name)
        loaded = load_jsonl_best_effort(local_name)
        assert samples == loaded

        if os.path.exists(local_name):
            os.remove(local_name)

    def test_load_jsonl_strict_success(self, test_file):
        """Test that load_jsonl_strict succeeds with valid journal data."""
        valid_journal_entry = {k: "val" for k in REQUIRED_KEYS}
        valid_journal_entry["event_version"] = SCHEMA_VERSION
        valid_journal_entry["round"] = 1

        save_jsonl([valid_journal_entry], str(test_file))

        loaded = load_jsonl_strict(str(test_file))
        assert len(loaded) == 1
        assert loaded[0]["event_version"] == SCHEMA_VERSION

    def test_load_jsonl_strict_fails_missing_keys(self, test_file):
        """Test that load_jsonl_strict exits on missing keys."""
        invalid_entry = {"event_version": SCHEMA_VERSION}
        save_jsonl([invalid_entry], str(test_file))

        with pytest.raises(SystemExit) as e:
            load_jsonl_strict(str(test_file))
        assert e.value.code == 1

    def test_load_jsonl_alias_is_strict(self, test_file):
        """Verify that load_jsonl is an alias to load_jsonl_strict."""
        assert load_jsonl is load_jsonl_strict
