import time
import os
import shutil
from heidi_engine.telemetry import init_telemetry, emit_event, get_state, AUTOTRAIN_DIR

def bench_telemetry():
    run_id = "bench_run"
    run_dir = os.path.join(AUTOTRAIN_DIR, "runs", run_id)
    if os.path.exists(run_dir):
        shutil.rmtree(run_dir)

    init_telemetry(run_id=run_id)

    start_time = time.perf_counter()
    iterations = 1000
    for i in range(iterations):
        # emit_event calls get_state internally
        emit_event("progress", f"Message {i}", stage="bench", round_num=1)

    end_time = time.perf_counter()
    duration = end_time - start_time
    print(f"Total time for {iterations} emit_event calls: {duration:.4f}s")
    print(f"Average time per call: {duration/iterations*1000:.4f}ms")

if __name__ == "__main__":
    bench_telemetry()
