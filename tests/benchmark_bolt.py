
import time
import re
import sys
import os
from typing import Any, Dict, List, Tuple
from collections import Counter
import hashlib

# Import the functions to benchmark
# Since these are scripts with numeric prefixes, we need to import them carefully
import importlib.util

def import_from_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

telemetry = import_from_path("telemetry", "heidi_engine/telemetry.py")
validate_clean = import_from_path("validate_clean", "scripts/02_validate_clean.py")

def benchmark_fuzzy_hash():
    print("\n--- Benchmarking fuzzy_hash whitespace removal ---")
    sample = {
        "instruction": "Explain this code" * 100,
        "output": "def hello():\n    print('world')\n" * 500
    }

    # Old implementation (re.sub)
    def old_fuzzy_hash(sample, n=5):
        text = (sample.get("instruction", "") + sample.get("output", "")).lower()
        text = re.sub(r"\s+", "", text)
        if len(text) < n: return text
        ngrams = [text[i : i + n] for i in range(len(text) - n + 1)]
        counter = Counter(ngrams)
        fingerprint = "".join(sorted([ng for ng, _ in counter.most_common(10)]))
        return hashlib.sha256(fingerprint.encode()).hexdigest()

    iterations = 100

    start = time.time()
    for _ in range(iterations):
        old_fuzzy_hash(sample)
    old_time = time.time() - start
    print(f"Old (re.sub): {old_time:.4f}s")

    start = time.time()
    for _ in range(iterations):
        validate_clean.fuzzy_hash(sample)
    new_time = time.time() - start
    print(f"New (split/join): {new_time:.4f}s")
    print(f"Speedup: {old_time/new_time:.2f}x")

def benchmark_detect_secrets():
    print("\n--- Benchmarking detect_secrets (pre-compiled regex) ---")
    sample = {
        "instruction": "Tell me a secret",
        "input": "User input here",
        "output": "Here is a fake key: sk-1234567890abcdef1234567890abcdef1234567890abcdef"
    }

    iterations = 1000

    # Simulate old way (re-compiling or re-searching from string patterns)
    SECRET_PATTERNS = validate_clean.SECRET_PATTERNS
    SECRET_CHECK_FIELDS = validate_clean.SECRET_CHECK_FIELDS

    start = time.time()
    for _ in range(iterations):
        found_secrets = []
        for field in SECRET_CHECK_FIELDS:
            text = str(sample.get(field, ""))
            for pattern, secret_type in SECRET_PATTERNS:
                if re.search(pattern, text):
                    found_secrets.append(f"{field}:{secret_type}")
    old_time = time.time() - start
    print(f"Old (re.search with strings): {old_time:.4f}s")

    start = time.time()
    for _ in range(iterations):
        validate_clean.detect_secrets(sample)
    new_time = time.time() - start
    print(f"New (pre-compiled): {new_time:.4f}s")
    print(f"Speedup: {old_time/new_time:.2f}x")

def benchmark_pricing_cache():
    print("\n--- Benchmarking pricing config cache ---")

    # Warm up cache
    telemetry.load_pricing_config()

    iterations = 5000

    # Time with cache
    start = time.time()
    for _ in range(iterations):
        telemetry.load_pricing_config()
    cache_time = time.time() - start
    print(f"With Cache: {cache_time:.4f}s")

    # Time without cache (simulated by clearing it and forcing a reload)
    # But wait, we can't easily disable it. Let's just measure the hit performance.
    # A disk read would be orders of magnitude slower.
    print(f"Cache hit performance: {iterations/cache_time:.0f} calls/sec")

if __name__ == "__main__":
    benchmark_fuzzy_hash()
    benchmark_detect_secrets()
    benchmark_pricing_cache()
