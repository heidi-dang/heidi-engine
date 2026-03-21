
import time
import re
import sys
import os
from pathlib import Path

# Add current dir to path to import heidi_engine
sys.path.append(os.getcwd())

from heidi_engine.telemetry import redact_secrets, load_pricing_config, emit_event, init_telemetry, AUTOTRAIN_DIR, get_state, save_state

def benchmark_redact_secrets():
    print("Benchmarking redact_secrets...")
    text_no_secrets = "This is a normal log message without any secrets in it. It should be fast."
    text_with_secrets = "ghp_1234567890abcdefghijklmnopqrstuvwxyz and sk-1234567890abcdefghijklmnopqrstuvwxyz1234567890 and some other stuff."

    start = time.time()
    for _ in range(10000):
        redact_secrets(text_no_secrets)
    end = time.time()
    print(f"No secrets (10k calls): {end - start:.4f}s")

    start = time.time()
    for _ in range(10000):
        redact_secrets(text_with_secrets)
    end = time.time()
    print(f"With secrets (10k calls): {end - start:.4f}s")

def benchmark_pricing_config():
    print("\nBenchmarking load_pricing_config...")
    # Ensure run dir exists
    run_id = "bench_run"
    init_telemetry(run_id=run_id)

    # Force a cache hit by ensuring pricing.json exists
    pricing_file = Path(AUTOTRAIN_DIR) / "runs" / run_id / "pricing.json"
    pricing_file.write_text('{"gpt-4o": {"input": 1.0, "output": 2.0}}')

    # Warm up
    load_pricing_config()

    start = time.time()
    for _ in range(10000):
        load_pricing_config()
    end = time.time()
    print(f"load_pricing_config (10k calls): {end - start:.4f}s")

def benchmark_state_cache():
    print("\nBenchmarking state caching...")
    run_id = "bench_run_state"
    init_telemetry(run_id=run_id)

    # Warm up
    state = get_state(run_id)

    start = time.time()
    for _ in range(10000):
        # This calls get_state which should hit the cache after the first call
        get_state(run_id)
    end = time.time()
    print(f"get_state cache hit (10k calls): {end - start:.4f}s")

    # Benchmark write-through
    start = time.time()
    for i in range(1000):
        state["counters"]["teacher_generated"] = i
        save_state(state, run_id) # Should update cache
        get_state(run_id)         # Should hit cache
    end = time.time()
    print(f"save_state + get_state (1k pairs): {end - start:.4f}s")

if __name__ == "__main__":
    benchmark_redact_secrets()
    benchmark_pricing_config()
    benchmark_state_cache()
