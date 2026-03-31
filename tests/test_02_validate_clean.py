import importlib.util
import os
import pytest
from typing import Any, Dict

# Dynamically load the script since it starts with a digit
script_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "02_validate_clean.py")
spec = importlib.util.spec_from_file_location("validate_clean", script_path)
vc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vc)

class TestValidateClean:
    def test_detect_secrets_basic(self):
        # Using a pattern that should match according to SECRET_PATTERNS in 02_validate_clean.py
        # ghp_[a-zA-Z0-9]{36}
        token = "ghp_" + "a" * 36
        sample = {"output": f"My key is {token}"}
        has_secrets, secrets = vc.detect_secrets(sample)
        assert has_secrets is True
        assert any("github_token" in s for s in secrets)

    def test_detect_secrets_openai(self):
        # sk-[a-zA-Z0-9]{48,}
        key = "sk-" + "a" * 48
        sample = {"output": f"My key is {key}"}
        has_secrets, secrets = vc.detect_secrets(sample)
        assert has_secrets is True
        assert any("openai_key" in s for s in secrets)

    def test_detect_secrets_none(self):
        sample = {"output": "This is a clean string with no secrets."}
        has_secrets, secrets = vc.detect_secrets(sample)
        assert has_secrets is False
        assert len(secrets) == 0

    def test_detect_secrets_mixed_fields(self):
        # bearer\s+[\w\-]{20,}
        token = "Bearer " + "a" * 20
        sample = {
            "instruction": token,
            "output": "Clean output"
        }
        has_secrets, secrets = vc.detect_secrets(sample)
        assert has_secrets is True
        assert any("instruction:bearer_token" in s for s in secrets)

    def test_fuzzy_hash_stability(self):
        sample1 = {"instruction": "Hello world", "output": "This is a test."}
        sample2 = {"instruction": "hello world", "output": "this is a test."}

        hash1 = vc.fuzzy_hash(sample1)
        hash2 = vc.fuzzy_hash(sample2)

        assert hash1 == hash2

    def test_fuzzy_hash_whitespace_insensitivity(self):
        sample1 = {"instruction": "Hello world", "output": "This is a test."}
        sample2 = {"instruction": "Hello  world", "output": "This  is  a  test."}

        hash1 = vc.fuzzy_hash(sample1)
        hash2 = vc.fuzzy_hash(sample2)

        assert hash1 == hash2

    def test_fuzzy_hash_different(self):
        sample1 = {"instruction": "Hello world", "output": "This is a test."}
        sample2 = {"instruction": "Goodbye world", "output": "That was a test."}

        hash1 = vc.fuzzy_hash(sample1)
        hash2 = vc.fuzzy_hash(sample2)

        assert hash1 != hash2
