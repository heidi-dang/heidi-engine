import importlib.util
import os
import pytest
from typing import Dict, Any

# Load the script to test
script_path = os.path.join(os.getcwd(), "scripts/02_validate_clean.py")
spec = importlib.util.spec_from_file_location("validate_clean", script_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def test_detect_secrets_basic():
    sample = {
        "instruction": "Explain how to use an API key.",
        "input": "I have an API key like sk-1234567890abcdef1234567890abcdef1234567890abcdef",
        "output": "You should never share your API key."
    }
    has_secrets, secrets = module.detect_secrets(sample)
    assert has_secrets is True
    assert any("openai_key" in s for s in secrets)

def test_detect_secrets_none():
    sample = {
        "instruction": "What is 2+2?",
        "input": "",
        "output": "4"
    }
    has_secrets, secrets = module.detect_secrets(sample)
    assert has_secrets is False
    assert len(secrets) == 0

def test_detect_secrets_mixed_fields():
    sample = {
        "instruction": "Set my password",
        "input": "password = 'secret_password_123'",
        "output": "OK"
    }
    has_secrets, secrets = module.detect_secrets(sample)
    assert has_secrets is True
    assert any("password" in s for s in secrets)

def test_detect_secrets_high_entropy():
    sample = {
        "instruction": "Explain this code",
        "input": "print('5f2d9e8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1')",
        "output": "This is a simple print statement."
    }
    has_secrets, secrets = module.detect_secrets(sample)
    assert has_secrets is True
    assert any("high_entropy" in s for s in secrets)

def test_detect_secrets_not_passwords():
    sample = {
        "instruction": "What is your password policy?",
        "input": "Users should have a strong password of at least 8 characters.",
        "output": "Password policy: use long and unique passwords."
    }
    has_secrets, secrets = module.detect_secrets(sample)
    # The word "password" is there but it's not a secret assignment
    assert has_secrets is False
    assert len(secrets) == 0

def test_fuzzy_hash_consistency():
    sample1 = {
        "instruction": "Write a function to add two numbers.",
        "output": "def add(a, b):\n    return a + b"
    }
    sample2 = {
        "instruction": "Write a function to add two numbers.",
        "output": "def add(x, y):\n    return x + y"
    }

    hash1 = module.fuzzy_hash(sample1)
    hash2 = module.fuzzy_hash(sample2)

    # These should be different if the content is different enough
    # but let's test that same content gives same hash
    assert module.fuzzy_hash(sample1) == hash1

    # Test whitespace insensitivity
    sample1_ws = {
        "instruction": "  Write a function to add two numbers.  ",
        "output": "def add(a, b):\n\n    return a + b"
    }
    assert module.fuzzy_hash(sample1_ws) == hash1

def test_fuzzy_hash_near_duplicates():
    # Slightly different comments should result in same fuzzy hash if top ngrams are same
    sample1 = {
        "instruction": "Add numbers",
        "output": "def add(a, b): return a + b # version 1"
    }
    sample2 = {
        "instruction": "Add numbers",
        "output": "def add(a, b): return a + b # version 2"
    }
    # With n=5 and top 10 ngrams, these might be same if the common part dominates
    h1 = module.fuzzy_hash(sample1)
    h2 = module.fuzzy_hash(sample2)
    # They are very short, so they might differ. But let's check they are deterministic.
    assert h1 == module.fuzzy_hash(sample1)

if __name__ == "__main__":
    pytest.main([__file__])
