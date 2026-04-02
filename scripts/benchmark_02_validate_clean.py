
import time
import random
import string
import importlib.util
import os
import sys
from typing import Dict, Any

# Load the script dynamically
spec = importlib.util.spec_from_file_location("validate_clean", "scripts/02_validate_clean.py")
validate_clean = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_clean)

def run_benchmark():
    num_samples = 1000
    samples = []
    for i in range(num_samples):
        samples.append({
            "instruction": "Explain how to use " + "".join(random.choices(string.ascii_letters, k=100)),
            "input": "".join(random.choices(string.ascii_letters + string.whitespace, k=500)),
            "output": "Here is the code: " + "".join(random.choices(string.ascii_letters + string.whitespace, k=1000)),
            "metadata": {"id": i}
        })

    # Add secrets to some samples
    for i in range(0, num_samples, 100):
        samples[i]["output"] += " sk-123456789012345678901234567890123456789012345678"

    print(f"--- Benchmark: scripts/02_validate_clean.py ---")
    print(f"Total samples: {num_samples}")

    # Detect Secrets
    start = time.time()
    for s in samples:
        validate_clean.detect_secrets(s)
    end = time.time()
    secret_time = end - start
    print(f"detect_secrets: {secret_time:.4f}s total ({(secret_time/num_samples)*1000:.4f}ms avg)")

    # Fuzzy Hash
    start = time.time()
    for s in samples:
        validate_clean.fuzzy_hash(s)
    end = time.time()
    fuzzy_time = end - start
    print(f"fuzzy_hash: {fuzzy_time:.4f}s total ({(fuzzy_time/num_samples)*1000:.4f}ms avg)")

    print(f"Combined time: {secret_time + fuzzy_time:.4f}s")

if __name__ == "__main__":
    run_benchmark()
