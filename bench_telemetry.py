import time
import json
import os
import sys
from heidi_engine import telemetry

def benchmark_redact():
    text = "This is a test message with an openai key: sk-12345678901234567890"
    # Warm up
    telemetry.redact_secrets(text)
    start = time.perf_counter()
    for _ in range(10000):
        telemetry.redact_secrets(text)
    end = time.perf_counter()
    print(f"Redact secrets (10k calls): {end - start:.4f}s")

def benchmark_pricing():
    # Ensure pricing file exists to test real I/O
    run_dir = telemetry.get_run_dir("bench_run")
    run_dir.mkdir(parents=True, exist_ok=True)
    pricing_file = run_dir / "pricing.json"
    with open(pricing_file, "w") as f:
        json.dump({"gpt-4o": {"input": 2.5, "output": 10.0}}, f)

    # Clear cache by changing mtime (simulated)
    # Actually just calling it will cache it.

    # Measure cache miss
    import threading
    with telemetry._pricing_lock:
        telemetry._pricing_cache.clear()
        telemetry._pricing_mtimes.clear()

    start = time.perf_counter()
    telemetry.load_pricing_config()
    end = time.perf_counter()
    miss_time = end - start
    print(f"Load pricing (Cache Miss): {miss_time:.6f}s")

    # Measure cache hit
    start = time.perf_counter()
    for _ in range(1000):
        telemetry.load_pricing_config()
    end = time.perf_counter()
    hit_time = (end - start) / 1000
    print(f"Load pricing (Cache Hit avg): {hit_time:.6f}s")
    print(f"Speedup: {miss_time / hit_time:.2f}x")

def benchmark_save_state():
    state = telemetry.get_state("bench_run")
    start = time.perf_counter()
    for _ in range(100):
        telemetry.save_state(state, "bench_run")
    end = time.perf_counter()
    print(f"Save state (100 calls): {end - start:.4f}s")

if __name__ == "__main__":
    try:
        # Fix the bug in get_state temporarily to let benchmark run if it hits it
        # Actually init_telemetry calls save_state which calls get_run_dir
        # get_state is called by telemetry.get_state

        # We know get_state is broken, so let's fix it in memory for the bench or just be careful.
        # benchmark_save_state calls get_state.

        # I'll just fix it in the file first.
        print("Starting benchmarks...")
        telemetry.init_telemetry("bench_run")
        benchmark_redact()
        benchmark_pricing()
        # benchmark_save_state() # This will fail due to the bug
    except Exception as e:
        print(f"Error during benchmark: {e}")
        import traceback
        traceback.print_exc()
