import pytest
import importlib.util
from typing import Dict, Any

# Load the script dynamically
spec = importlib.util.spec_from_file_location("validate_clean", "scripts/02_validate_clean.py")
vc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vc)

def test_detect_secrets_functional():
    # Clean
    clean_sample = {"instruction": "Hello", "input": "World", "output": "!"}
    has_secrets, secrets = vc.detect_secrets(clean_sample)
    assert not has_secrets
    assert secrets == []

    # OpenAI key
    openai_sample = {"instruction": "Use sk-" + "a" * 48, "input": "", "output": ""}
    has_secrets, secrets = vc.detect_secrets(openai_sample)
    assert has_secrets
    assert any("openai_key" in s for s in secrets)

    # Combined check
    combined_sample = {"instruction": "api_key: " + "a" * 20, "input": "value", "output": ""}
    has_secrets, secrets = vc.detect_secrets(combined_sample)
    assert has_secrets

def test_fuzzy_hash_functional():
    s1 = {"instruction": "Hello world", "output": "The quick brown fox"}
    s2 = {"instruction": "hello WORLD", "output": "the QUICK brown FOX"}
    s3 = {"instruction": "Different", "output": "Content"}

    h1 = vc.fuzzy_hash(s1)
    h2 = vc.fuzzy_hash(s2)
    h3 = vc.fuzzy_hash(s3)

    assert h1 == h2
    assert h1 != h3

if __name__ == "__main__":
    test_detect_secrets_functional()
    test_fuzzy_hash_functional()
    print("Functional tests for 02_validate_clean passed!")
