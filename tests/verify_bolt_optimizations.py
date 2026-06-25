import re
import hashlib
import timeit
from collections import Counter
from typing import Any, Dict, List, Tuple

# --- ORIGINAL LOGIC ---
SECRET_PATTERNS = [
    (r'(?i)(api[_-]?key|apikey|secret[_-]?key)\s*[:=]\s*["\']?[\w\-]{20,}', "api_key"),
    (r"(?i)bearer\s+[\w\-]{20,}", "bearer_token"),
    (r'(?i)token\s*[:=]\s*["\']?[\w\-]{20,}', "token"),
    (r"AKIA[0-9A-Z]{16}", "aws_access_key"),
    (r'(?i)aws[_-]?secret[_-]?access[_-]?key\s*[:=]\s*["\']?[\w\/+]{40}', "aws_secret"),
    (r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----", "private_key"),
    (r"-----BEGIN\s+OPENSSH\s+PRIVATE\s+KEY-----", "ssh_private_key"),
    (r"(?i)(mongodb|postgres|mysql|redis):\/\/[\w:@\/.-]+", "db_url"),
    (r"(?i)postgresql://[\w:@\/.-]+", "postgres_url"),
    (r"ghp_[a-zA-Z0-9]{36}", "github_token"),
    (r"glpat-[a-zA-Z0-9\-]{20,}", "gitlab_token"),
    (r"sk-[a-zA-Z0-9]{48,}", "openai_key"),
    (r'["\'][\w+\/]{40,}["\']', "high_entropy"),
    (r'(?i)password\s*[:=]\s*["\'][^"\']{8,}["\']', "password"),
    (r'(?i)pwd\s*[:=]\s*["\'][^"\']{8,}["\']', "password"),
]
SECRET_CHECK_FIELDS = ["instruction", "input", "output", "response", "completion"]

def detect_secrets_original(sample: Dict[str, Any]) -> Tuple[bool, List[str]]:
    found_secrets = []
    for field in SECRET_CHECK_FIELDS:
        if field not in sample:
            continue
        text = str(sample[field])
        for pattern, secret_type in SECRET_PATTERNS:
            if re.search(pattern, text):
                found_secrets.append(f"{field}:{secret_type}")
    return len(found_secrets) > 0, found_secrets

def fuzzy_hash_original(sample: Dict[str, Any], n: int = 5) -> str:
    text = (sample.get("instruction", "") + sample.get("output", "")).lower()
    text = re.sub(r"\s+", "", text)
    if len(text) < n: return text
    ngrams = [text[i : i + n] for i in range(len(text) - n + 1)]
    counter = Counter(ngrams)
    fingerprint = "".join(sorted([ng for ng, _ in counter.most_common(10)]))
    return hashlib.sha256(fingerprint.encode()).hexdigest()

# --- OPTIMIZED LOGIC (from scripts/02_validate_clean.py) ---
_SECRET_PATTERNS_COMPILED = [(re.compile(p), t) for p, t in SECRET_PATTERNS]
_SECRET_KEYWORDS = {"api", "key", "secret", "bearer", "token", "akia", "begin", "private", "mongodb", "postgres", "mysql", "redis", "ghp_", "glpat-", "sk-", "password", "pwd"}

def detect_secrets_optimized(sample: Dict[str, Any]) -> Tuple[bool, List[str]]:
    found_secrets = []
    for field in SECRET_CHECK_FIELDS:
        text = sample.get(field)
        if text is None: continue
        text = str(text)
        text_lower = text.lower()
        has_keyword = any(kw in text_lower for kw in _SECRET_KEYWORDS)
        has_long_quote = '"' in text or "'" in text
        if not (has_keyword or has_long_quote): continue
        for pattern, secret_type in _SECRET_PATTERNS_COMPILED:
            if pattern.search(text):
                found_secrets.append(f"{field}:{secret_type}")
    return len(found_secrets) > 0, found_secrets

def fuzzy_hash_optimized(sample: Dict[str, Any], n: int = 5) -> str:
    text = (sample.get("instruction", "") + sample.get("output", "")).lower()
    text = "".join(text.split())
    if len(text) < n: return text
    ngrams = [text[i : i + n] for i in range(len(text) - n + 1)]
    counter = Counter(ngrams)
    fingerprint = "".join(sorted([ng for ng, _ in counter.most_common(10)]))
    return hashlib.sha256(fingerprint.encode()).hexdigest()

# --- VERIFICATION ---
test_samples = [
    {
        "name": "Clean Sample",
        "sample": {
            "instruction": "Write a python function to add two numbers.",
            "input": "def add(a, b):\n    return a + b",
            "output": "Here is the code:\n\n```python\ndef add(a, b):\n    return a + b\n```"
        }
    },
    {
        "name": "Sample with Secret",
        "sample": {
            "instruction": "Explain this code",
            "input": "api_key = 'sk-123456789012345678901234567890123456789012345678'",
            "output": "This code sets an API key."
        }
    },
    {
        "name": "Sample with complex whitespace",
        "sample": {
            "instruction": "  Find   bugs  \n in this   code  ",
            "input": "def foo():\n\tprint('hello')\n    return True",
            "output": "The code looks  fine.   "
        }
    },
    {
        "name": "High entropy string without keyword",
        "sample": {
            "instruction": "What is this?",
            "input": "x = \"mypasswordwasneverthislongbutthislookslikeone\"",
            "output": "Actually, let's use: 'A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7R8S9T0'"
        }
    }
]

print("Verifying Correctness...")
for ts in test_samples:
    name = ts["name"]
    sample = ts["sample"]

    # Verify detect_secrets
    res_orig, list_orig = detect_secrets_original(sample)
    res_opt, list_opt = detect_secrets_optimized(sample)

    if res_orig != res_opt or list_orig != list_opt:
        print(f"FAILED: {name}")
        print(f"  Original:  {res_orig}, {list_orig}")
        print(f"  Optimized: {res_opt}, {list_opt}")
        # DEBUG: check pattern search manually
        if res_orig:
            print("  Original matches found:")
            for field in SECRET_CHECK_FIELDS:
                if field in sample:
                    text = str(sample[field])
                    for pattern, secret_type in SECRET_PATTERNS:
                        if re.search(pattern, text):
                            print(f"    {field}:{secret_type} matches '{text}' with '{pattern}'")

    assert res_orig == res_opt, f"detect_secrets result mismatch for {name}"
    assert list_orig == list_opt, f"detect_secrets list mismatch for {name}"

    # Verify fuzzy_hash
    hash_orig = fuzzy_hash_original(sample)
    hash_opt = fuzzy_hash_optimized(sample)
    assert hash_orig == hash_opt, f"fuzzy_hash mismatch for {name}"

    print(f"  [OK] {name}")

print("\nMeasuring Performance...")
n = 10000
clean_sample = test_samples[0]["sample"]
secret_sample = test_samples[1]["sample"]

t_orig_clean = timeit.timeit(lambda: detect_secrets_original(clean_sample), number=n)
t_opt_clean = timeit.timeit(lambda: detect_secrets_optimized(clean_sample), number=n)
print(f"detect_secrets (Clean, {n} iterations):")
print(f"  Original:  {t_orig_clean:.4f}s")
print(f"  Optimized: {t_opt_clean:.4f}s")
print(f"  Speedup:   {t_orig_clean/t_opt_clean:.2f}x")

t_orig_secret = timeit.timeit(lambda: detect_secrets_original(secret_sample), number=n)
t_opt_secret = timeit.timeit(lambda: detect_secrets_optimized(secret_sample), number=n)
print(f"detect_secrets (Secret, {n} iterations):")
print(f"  Original:  {t_orig_secret:.4f}s")
print(f"  Optimized: {t_opt_secret:.4f}s")
print(f"  Speedup:   {t_orig_secret/t_opt_secret:.2f}x")

t_orig_fuzzy = timeit.timeit(lambda: fuzzy_hash_original(clean_sample), number=n)
t_opt_fuzzy = timeit.timeit(lambda: fuzzy_hash_optimized(clean_sample), number=n)
print(f"fuzzy_hash ({n} iterations):")
print(f"  Original:  {t_orig_fuzzy:.4f}s")
print(f"  Optimized: {t_opt_fuzzy:.4f}s")
print(f"  Speedup:   {t_orig_fuzzy/t_opt_fuzzy:.2f}x")

print("\n[ALL VERIFICATIONS PASSED]")
