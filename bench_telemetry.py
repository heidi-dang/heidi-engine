
import time
import os
import shutil
from pathlib import Path
from heidi_engine.telemetry import get_state, init_telemetry, emit_event, AUTOTRAIN_DIR

def bench():
    # Setup
    run_id = "bench_run"
    if Path(AUTOTRAIN_DIR).exists():
        shutil.rmtree(AUTOTRAIN_DIR)

    init_telemetry(run_id=run_id)

    # Warm up
    get_state(run_id)

    start = time.perf_counter()
    n = 1000
    for _ in range(n):
        get_state(run_id)
    end = time.perf_counter()

    avg_ms = (end - start) * 1000 / n
    print(f"get_state average time: {avg_ms:.4f} ms")

    start = time.perf_counter()
    for i in range(100):
        emit_event("progress", f"Message {i}", run_id=run_id)
    end = time.perf_counter()
    avg_event_ms = (end - start) * 1000 / 100
    print(f"emit_event average time: {avg_event_ms:.4f} ms")

if __name__ == "__main__":
    bench()
