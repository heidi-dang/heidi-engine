import time
import os
import shutil
from pathlib import Path
from heidi_engine.telemetry import init_telemetry, get_state, save_state

def bench_get_state():
    run_id = "bench_run"
    init_telemetry(run_id=run_id, force=True)

    # Warm up
    get_state(run_id)

    iterations = 1000
    start_time = time.time()
    for _ in range(iterations):
        get_state(run_id)
    end_time = time.time()

    avg_time = (end_time - start_time) / iterations
    print(f"Average get_state time: {avg_time*1000:.4f} ms")

if __name__ == "__main__":
    bench_get_state()
