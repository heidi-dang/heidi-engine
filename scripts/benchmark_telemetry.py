import time
import os
import sys
import json
from pathlib import Path

# Add the root directory to sys.path to import heidi_engine
sys.path.append(os.getcwd())

from heidi_engine.telemetry import (
    get_state,
    init_telemetry,
    get_run_id,
    save_state,
    emit_event,
    flush_events,
    get_gpu_summary,
    get_last_event_ts
)

def benchmark(name, func, iterations=100):
    start = time.perf_counter()
    for _ in range(iterations):
        func()
    end = time.perf_counter()
    avg = (end - start) / iterations
    print(f"{name:.<30} Avg: {avg*1000:.4f} ms ({iterations} iterations)")
    return avg

def main():
    # Ensure we have a run initialized for testing
    run_id = init_telemetry(run_id="bench_run", force=True)
    print(f"Benchmarking with run_id: {run_id}")

    # Mock some data
    save_state({"run_id": run_id, "status": "running", "counters": {"test": 1}})
    emit_event("test", "benchmark message")
    flush_events()

    print("\nPerformance with caching:")
    benchmark("get_state", lambda: get_state(run_id))
    benchmark("get_gpu_summary", lambda: get_gpu_summary())
    benchmark("get_last_event_ts", lambda: get_last_event_ts())

    # Test cache effect (call multiple times)
    print("\nConsecutive calls (cache hits):")
    benchmark("get_state (cached)", lambda: get_state(run_id), iterations=1000)
    benchmark("get_gpu_summary (cached)", lambda: get_gpu_summary(), iterations=1000)
    benchmark("get_last_event_ts (cached)", lambda: get_last_event_ts(), iterations=1000)

if __name__ == "__main__":
    main()
