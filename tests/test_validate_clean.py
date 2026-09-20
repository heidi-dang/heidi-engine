import importlib

validate_clean = importlib.import_module("scripts.02_validate_clean")


def test_detect_secrets():
    # Clean sample
    clean_sample = {
        "instruction": "Fix Python bug",
        "input": "def add(a, b): return a + b",
        "output": "def add(a, b):\n    return a + b",
    }
    has_secrets, secrets = validate_clean.detect_secrets(clean_sample)
    assert not has_secrets
    assert secrets == []

    # Sample with OpenAI secret key matching SECRET_PATTERNS
    secret_sample = {
        "instruction": "Configure API client",
        "input": "sk-1234567890abcdef1234567890abcdef1234567890abcdef",
        "output": "client = OpenAI()",
    }
    has_secrets, secrets = validate_clean.detect_secrets(secret_sample)
    assert has_secrets
    assert any("openai_key" in s for s in secrets)


def test_fuzzy_hash():
    s1 = {"instruction": "Write   a   function", "output": "def   foo():   pass"}
    s2 = {"instruction": "Write a function", "output": "def foo(): pass"}

    # Whitespace differences should produce identical fuzzy hash
    hash1 = validate_clean.fuzzy_hash(s1)
    hash2 = validate_clean.fuzzy_hash(s2)
    assert hash1 == hash2


def test_deduplicate_samples():
    samples = [
        {"id": "1", "instruction": "Task 1", "output": "def f1(): pass"},
        {"id": "2", "instruction": "Task 1", "output": "def f1(): pass"},  # Exact duplicate
        {"id": "3", "instruction": "Task 2", "output": "def f2(): pass"},
    ]
    unique, dupes = validate_clean.deduplicate_samples(samples)
    assert len(unique) == 2
    assert dupes == 1
