#!/usr/bin/env python3
import json
import os
import subprocess
import time
import shutil


def test_fuzzing():
    """
    Red-team harness: Fuzzes the jsonl ingestion and verifies the redaction limits
    of the C++ Core by artificially injecting key leakage into the simulated pipeline.
    """
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
    with open("scripts/01_teacher_generate.py", "w") as f:
        f.write(malicious_script)

    os.environ["HEIDI_MOCK_SUBPROCESSES"] = "0"
    os.environ["RUN_ID"] = "fuzz_001"
    os.environ["OUT_DIR"] = test_dir
    os.environ["HEIDI_REPO_ROOT"] = os.getcwd()
    os.environ["MAX_WALL_TIME_MINUTES"] = "10"
    os.environ["MAX_CPU_PCT"] = "100"
    os.environ["HEIDI_SIGNING_KEY"] = "test-key"
    os.environ["HEIDI_KEYSTORE_PATH"] = "test.enc"

    import pytest

    heidi_cpp = pytest.importorskip(
        "heidi_cpp",
        reason="C++ extension not available on this CI lane",
    )
    engine = heidi_cpp.Core()
    engine.init()
    engine.start("full")
    engine.tick(1)  # Executes the malicious script which will fail with exit(1)

    journal_path = os.path.join(test_dir, "events.jsonl")
    assert os.path.exists(journal_path), "Journal was not written!"

    # Verify Redaction
    leak_caught = False
    with open(journal_path, "r") as f:
        content = f.read()

        try:
            # Verify literal tokens are absent
            assert "sk-abcDEF1234567890abcDEF1234567890" not in content, (
                "CRITICAL VULNERABILITY: OpenAI token leaked into journal!"
            )
            assert "ghp_aBCdefGHIjklMNOpqrSTUvwxYZ0123456789" not in content, (
                "CRITICAL VULNERABILITY: GitHub token leaked into journal!"
            )

            # Verify replacement tokens are present indicating the redact mechanism worked natively
            assert "[OPENAI_KEY]" in content, "Redaction token [OPENAI_KEY] missing"
            assert "[GITHUB_TOKEN]" in content, "Redaction token [GITHUB_TOKEN] missing"
        except AssertionError as e:
            print(f"DEBUG: Journal Content:\n{content}")
            raise e

        leak_caught = True

    print(
        f"[SEC] Red-Team Pipeline harness complete. Keys successfully securely redacted from sub-process pipes before hitting disk."
    )


if __name__ == "__main__":
    test_fuzzing()
