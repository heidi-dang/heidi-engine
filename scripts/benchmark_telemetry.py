import time
import os
import shutil
import tempfile
from heidi_engine.telemetry import emit_event, get_state, init_telemetry, AUTOTRAIN_DIR

def benchmark():
    # Setup temp directory for telemetry
    tmpdir = tempfile.mkdtemp()
    os.environ["AUTOTRAIN_DIR"] = tmpdir

    run_id = "bench_run"
    init_telemetry(run_id=run_id)

    print("Benchmarking get_state...")
    start = time.perf_counter()
    iterations = 1000
    for _ in range(iterations):
        get_state(run_id)
    end = time.perf_counter()
    print(f"get_state: {(end - start) / iterations * 1000:.4f} ms per call")

    print("\nBenchmarking emit_event (which calls estimate_cost -> load_pricing_config)...")
    start = time.perf_counter()
    for i in range(iterations):
        emit_event("progress", f"Progress {i}", usage_delta={"input_tokens": 100, "output_tokens": 50}, model="gpt-4o-mini")
    end = time.perf_counter()
    print(f"emit_event: {(end - start) / iterations * 1000:.4f} ms per call")

    shutil.rmtree(tmpdir)

if __name__ == "__main__":
    benchmark()
