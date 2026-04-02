import time
import re
import hashlib
from collections import Counter
import importlib.util
import sys
import os

# Load the script dynamically
spec = importlib.util.spec_from_file_location("validate_clean", "scripts/02_validate_clean.py")
vc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vc)

def benchmark_secrets(n_iterations=1000):
    clean_sample = {
        "instruction": "Explain the concept of recursion in programming.",
        "input": "What is recursion?",
        "output": "Recursion is a process in which a function calls itself as a subroutine."
    }
    secret_sample = {
        "instruction": "How to use this key?",
        "input": "sk-1234567890abcdefghijklmnopqrstuvwxyz1234567890",
        "output": "Just pass it to the API."
    }

    start = time.perf_counter()
    for _ in range(n_iterations):
        vc.detect_secrets(clean_sample)
    end = time.perf_counter()
    clean_time = (end - start) / n_iterations

    start = time.perf_counter()
    for _ in range(n_iterations):
        vc.detect_secrets(secret_sample)
    end = time.perf_counter()
    secret_time = (end - start) / n_iterations

    return clean_time, secret_time

def benchmark_fuzzy_hash(n_iterations=100):
    sample = {
        "instruction": "Write a python function to calculate fibonacci numbers." * 10,
        "output": "def fib(n):\n    if n <= 1: return n\n    return fib(n-1) + fib(n-2)" * 10
    }

    start = time.perf_counter()
    for _ in range(n_iterations):
        vc.fuzzy_hash(sample)
    end = time.perf_counter()

    return (end - start) / n_iterations

if __name__ == "__main__":
    print("Running Baseline Benchmark...")
    c_time, s_time = benchmark_secrets()
    print(f"detect_secrets (clean): {c_time*1000:.4f}ms")
    print(f"detect_secrets (secret): {s_time*1000:.4f}ms")

    f_time = benchmark_fuzzy_hash()
    print(f"fuzzy_hash: {f_time*1000:.4f}ms")
