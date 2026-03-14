
import time
import tempfile
import json
from heidi_engine import telemetry

def benchmark():
    with tempfile.TemporaryDirectory() as tmp_dir:
        telemetry.AUTOTRAIN_DIR = tmp_dir
        run_id = "bench_run"
        telemetry.init_telemetry(run_id)

        state = telemetry.get_state(run_id)

        # Benchmark save_state (now with write-through and no indent)
        start = time.perf_counter()
        for i in range(100):
            state["counters"]["teacher_generated"] = i
            telemetry.save_state(state, run_id)
        t_save = (time.perf_counter() - start) / 100

        # Benchmark get_state (should be 100% cache hit)
        start = time.perf_counter()
        for i in range(1000):
            telemetry.get_state(run_id)
        t_get = (time.perf_counter() - start) / 1000

        print(f"Average save_state: {t_save * 1000:.4f}ms")
        print(f"Average get_state (cache hit): {t_get * 1000:.4f}ms")

if __name__ == "__main__":
    benchmark()
