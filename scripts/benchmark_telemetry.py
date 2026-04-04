import time
import os
import shutil
from heidi_engine.telemetry import emit_event, init_telemetry, get_state, AUTOTRAIN_DIR

def benchmark_telemetry():
    run_id = "bench_run"
    run_dir = os.path.join(AUTOTRAIN_DIR, "runs", run_id)
    if os.path.exists(run_dir):
        shutil.rmtree(run_dir)

    init_telemetry(run_id=run_id)

    start_time = time.time()
    n = 100
    for i in range(n):
        emit_event(
            "progress",
            f"Message {i}",
            counters_delta={"teacher_generated": 1},
            usage_delta={"input_tokens": 100, "output_tokens": 50},
            model="gpt-4o-mini"
        )
    end_time = time.time()

    avg_time = (end_time - start_time) / n
    print(f"Average time per emit_event (with deltas): {avg_time*1000:.4f} ms")

    start_time = time.time()
    for i in range(n):
        get_state(run_id)
    end_time = time.time()
    avg_get_state = (end_time - start_time) / n
    print(f"Average time per get_state: {avg_get_state*1000:.4f} ms")

if __name__ == "__main__":
    benchmark_telemetry()
