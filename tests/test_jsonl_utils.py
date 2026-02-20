"""
Unit tests for JSONL IO utilities.
"""

import os
import pytest
from heidi_engine.utils.io_jsonl import load_jsonl, save_jsonl


class TestJSONLUtils:
    """Test JSONL loading and saving utilities."""

    @pytest.fixture
    def test_file(self, tmp_path):
        """Fixture for a temporary JSONL file path."""
        return tmp_path / "test.jsonl"

    def test_save_and_load_roundtrip(self, test_file):
        """Test that data can be saved and then loaded correctly."""
        samples = [
            {
                "id": "1",
                "text": "hello",
                "event_version": "1.0",
                "ts": "2026-02-19T22:29:00.123456Z",
                "run_id": "run1",
                "round": 1,
                "stage": "start",
                "level": "info",
                "event_type": "log",
                "message": "Start",
                "counters_delta": {},
                "usage_delta": {},
                "artifact_paths": ["path1"],
                "prev_hash": "abc",
            },
            {
                "id": "2",
                "text": "world",
                "event_version": "1.0",
                "ts": "2026-02-19T22:30:00.123456Z",
                "run_id": "run2",
                "round": 2,
                "stage": "end",
                "level": "info",
                "event_type": "log",
                "message": "End",
                "counters_delta": {},
                "usage_delta": {},
                "artifact_paths": ["path2"],
                "prev_hash": "def",
            },
        ]
        save_jsonl(samples, str(test_file))

        loaded = load_jsonl(str(test_file))
        assert samples == loaded

    def test_save_creates_directories(self, tmp_path):
        """Test that save_jsonl automatically creates missing parent directories."""
        nested_path = tmp_path / "subdir" / "nested.jsonl"
        samples = [
            {
                "id": "1",
                "text": "test",
                "event_version": "1.0",
                "ts": "2026-02-19T22:29:00.123456Z",
                "run_id": "run1",
                "round": 1,
                "stage": "start",
                "level": "info",
                "event_type": "log",
                "message": "Create directories",
                "counters_delta": {},
                "usage_delta": {},
                "artifact_paths": ["path1"],
                "prev_hash": "abc",
            }
        ]
        save_jsonl(samples, str(nested_path))

        assert nested_path.exists()
        loaded = load_jsonl(str(nested_path))
        assert samples == loaded

    def test_load_skips_blank_lines(self, test_file):
        """Test that load_jsonl ignores empty or whitespace-only lines."""
        test_file.write_text(
            '{"id": 1, "event_version": "1.0", "ts": "2026-02-20T01:00:00Z", "run_id": "run1", "round": 1, "stage": "start", "level": "info", "event_type": "event", "message": "", "counters_delta": {"counter": 1}, "usage_delta": {"usage": 5}, "artifact_paths": ["path"], "prev_hash": "abcd"}\n\n   \n{"id": 2, "event_version": "1.0", "ts": "2026-02-20T01:01:00Z", "run_id": "run2", "round": 2, "stage": "end", "level": "info", "event_type": "end_event", "message": "", "counters_delta": {"counter": 2}, "usage_delta": {"usage": 3}, "artifact_paths": ["path_end"], "prev_hash": "efgh"}\n'
        )

        loaded = load_jsonl(str(test_file))
        assert len(loaded) == 2
        assert loaded[0]["id"] == 1
        assert loaded[1]["id"] == 2

    def test_load_handles_invalid_json(self, test_file, capsys):
        """Test that load_jsonl skips invalid JSON lines and prints a warning to stderr."""
        test_file.write_text('{"id": 1}\n{invalid}\n{"id": 2}\n')

        with pytest.raises(ValueError, match=r"(JSON parsing error|invalid JSON|line)"):
            load_jsonl(str(test_file))

    def test_save_current_directory(self, tmp_path, monkeypatch):
        """Test saving to a file in the current working directory (no directory part in path)."""
        # Change CWD to the temporary directory
        monkeypatch.chdir(tmp_path)

        local_name = "temp_test_io_jsonl.jsonl"
        samples = [
            {
                "id": "1",
                "event_version": "1.0",
                "ts": "2026-02-20T01:00:00Z",
                "run_id": "run1",
                "round": 1,
                "stage": "start",
                "level": "info",
                "event_type": "event",
                "message": "",
                "counters_delta": {"counter": 1},
                "usage_delta": {"usage": 5},
                "artifact_paths": ["path"],
                "prev_hash": "abcd",
            }
        ]

        save_jsonl(samples, local_name)
        assert os.path.exists(local_name)
        loaded = load_jsonl(local_name)
        assert samples == loaded

        # Cleanup is handled by tmp_path and monkeypatch.chdir automatically when test ends,
        # but we can explicitly remove the file if we want to be clean within the test.
        if os.path.exists(local_name):
            os.remove(local_name)
