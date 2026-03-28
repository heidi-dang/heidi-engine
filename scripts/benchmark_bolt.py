import time
import sys
import os
import importlib.util

# Ensure we can import from the scripts directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Handle the fact that 02_validate_clean.py starts with a digit
spec = importlib.util.spec_from_file_location("validate_clean", "scripts/02_validate_clean.py")
validate_clean = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_clean)
detect_secrets = validate_clean.detect_secrets
fuzzy_hash = validate_clean.fuzzy_hash

def run_benchmarks():
    base_samples = [
        {"instruction": "Write a python function", "input": "def hello(): print('hello')", "output": "Here is the code:\n\n```python\ndef hello():\n    print('hello')\n```"},
        {"instruction": "My secret key is sk-123456789012345678901234567890123456789012345678", "input": "", "output": "REDACTED"},
        {"instruction": "A sample with a high-entropy string \"SGVsbG8gd29ybGQhIFRoaXMgaXMgYSBzZWNyZXQgdGVzdCBzdHJpbmcgdGhhdCBzaG91bGQgYmUgZGV0ZWN0ZWQu\"", "input": "", "output": "REDACTED"},
        {"instruction": "Tell me a joke", "input": "", "output": "Why did the chicken cross the road? " * 20},
    ]
    samples = base_samples * 1000

    print("Benchmarking detect_secrets (Optimized)...")
    start = time.time()
    for s in samples:
        detect_secrets(s)
    print(f"Time: {time.time() - start:.4f}s")

    print("\nBenchmarking fuzzy_hash (Optimized)...")
    start = time.time()
    for s in samples:
        fuzzy_hash(s)
    print(f"Time: {time.time() - start:.4f}s")

    # Correctness check
    print("\nVerifying Correctness...")
    s1 = {"instruction": "My key is sk-123456789012345678901234567890123456789012345678", "input": "", "output": ""}
    s2 = {"instruction": "High entropy string: \"SGVsbG8gd29ybGQhIFRoaXMgaXMgYSBzZWNyZXQgdGVzdCBzdHJpbmcgdGhhdCBzaG91bGQgYmUgZGV0ZWN0ZWQu\"", "input": "", "output": ""}
    s3 = {"instruction": "This is a clean string", "input": "", "output": ""}

    # Check if detect_secrets detects the patterns
    detect1, _ = detect_secrets(s1)
    detect2, _ = detect_secrets(s2)
    detect3, _ = detect_secrets(s3)

    assert detect1 == True, "Failed to detect sk- key"
    assert detect2 == True, "Failed to detect high-entropy string"
    assert detect3 == False, "Incorrectly detected secret in clean string"
    print("[OK] Correctness verified!")

if __name__ == "__main__":
    run_benchmarks()
