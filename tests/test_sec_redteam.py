#!/usr/bin/env python3
import json
import os
import pytest
import subprocess
import time
import shutil

def test_fuzzing():
    """
    Red-team harness: Fuzzes the jsonl ingestion and verifies the redaction limits
    of the C++ Core by artificially injecting key leakage into the simulated pipeline.
    """
    heidi_cpp = pytest.importorskip("heidi_cpp")

    test_dir = "build/test_fuzz_run"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir, exist_ok=True)
    os.makedirs("scripts", exist_ok=True)

    # We deliberately create a malicious python script that leaks secrets
    # to stdout/stderr. The C++ parent orchestrator must catch and redact it
    # before it enters the cryptographically verifiable append-only events.jsonl
    malicious_script = """import sys
import os
print("My leaked key is sk-abcDEF1234567890abcDEF1234567890")
print("Also leaked ghp_aBCdefGHIjklMNOpqrSTUvwxYZ0123456789", file=sys.stderr)
sys.exit(1)
"""
    script_path = os.path.join("scripts", "01_teacher_generate.py")
    original_script = None
    if os.path.exists(script_path):
        with open(script_path, "r", encoding="utf-8") as f:
            original_script = f.read()

    try:
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(malicious_script)

        os.environ["HEIDI_MOCK_SUBPROCESSES"] = "0"
        os.environ["RUN_ID"] = "fuzz_001"
        os.environ["OUT_DIR"] = test_dir
        os.environ["HEIDI_REPO_ROOT"] = os.getcwd()
        os.environ["MAX_WALL_TIME_MINUTES"] = "10"
        os.environ["MAX_CPU_PCT"] = "100"
        os.environ["HEIDI_SIGNING_KEY"] = "test-key"
        os.environ["HEIDI_KEYSTORE_PATH"] = "test.enc"

        engine = heidi_cpp.Core()
        engine.init()
        engine.start("full")
        engine.tick(1)  # Executes the malicious script which will fail with exit(1)

        journal_path = os.path.join(test_dir, "events.jsonl")
        assert os.path.exists(journal_path), "Journal was not written!"

        with open(journal_path, "r", encoding="utf-8") as f:
            content = f.read()

        try:
            assert "sk-abcDEF1234567890abcDEF1234567890" not in content
            assert "ghp_aBCdefGHIjklMNOpqrSTUvwxYZ0123456789" not in content
            assert "[OPENAI_KEY]" in content
            assert "[GITHUB_TOKEN]" in content
        except AssertionError:
            print(f"DEBUG: Journal Content:\n{content}")
            raise

        print(
            "[SEC] Red-Team Pipeline harness complete. Keys successfully securely redacted from sub-process pipes before hitting disk."
        )
    finally:
        if original_script is None:
            os.remove(script_path)
        else:
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(original_script)

if __name__ == "__main__":
    test_fuzzing()
