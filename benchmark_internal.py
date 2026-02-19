
import time
import os
import json
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(os.getcwd())

from heidi_engine import telemetry

def benchmark():
    os.environ["AUTOTRAIN_DIR"] = str(Path(os.getcwd()) / ".local_test")
    run_id = telemetry.init_telemetry(force=True)

    iterations = 10000

    # Baseline: get_state (direct disk read)
    start_time = time.perf_counter()
    for _ in range(iterations):
        telemetry.get_state(run_id)
    end_time = time.perf_counter()
    baseline_time = end_time - start_time
    print(f"get_state (Baseline): {baseline_time:.4f}s total, {(baseline_time/iterations)*1e6:.4f}µs per call")

    # Optimized: _state_cache.get
    # Ensure TTL is high enough
    telemetry._state_cache._ttl = 1.0
    start_time = time.perf_counter()
    for _ in range(iterations):
        telemetry._state_cache.get(run_id)
    end_time = time.perf_counter()
    optimized_time = end_time - start_time
    print(f"_state_cache.get: {optimized_time:.4f}s total, {(optimized_time/iterations)*1e6:.4f}µs per call")

    improvement = (baseline_time - optimized_time) / baseline_time * 100
    print(f"Improvement: {improvement:.2f}%")

if __name__ == "__main__":
    benchmark()
