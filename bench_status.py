import time
import os
import shutil
from heidi_engine.telemetry import (
    init_telemetry,
    emit_event,
    get_gpu_summary,
    get_last_event_ts,
    AUTOTRAIN_DIR,
    get_run_id,
    flush_events
)

def bench_status():
    run_id = get_run_id()
    init_telemetry(run_id=run_id)

    # Emit an event so get_last_event_ts has something to read
    emit_event("test", "test message")
    flush_events()

    print("Testing get_gpu_summary performance...")
    start = time.perf_counter()
    for _ in range(100):
        get_gpu_summary()
    end = time.perf_counter()
    print(f"Time for 100 get_gpu_summary calls: {(end-start)*1000:.4f}ms")

    print("\nTesting get_last_event_ts performance...")
    start = time.perf_counter()
    for _ in range(100):
        get_last_event_ts(run_id)
    end = time.perf_counter()
    print(f"Time for 100 get_last_event_ts calls: {(end-start)*1000:.4f}ms")

if __name__ == "__main__":
    bench_status()
