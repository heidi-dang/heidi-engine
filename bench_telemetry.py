import time
import os
import tempfile
import json
from pathlib import Path
from heidi_engine import telemetry

def bench_pricing():
    with tempfile.TemporaryDirectory() as tmp_dir:
        telemetry.AUTOTRAIN_DIR = tmp_dir
        run_id = "bench_run"
        telemetry.init_telemetry(run_id=run_id, force=True)

        # Create a pricing.json
        pricing_file = Path(tmp_dir) / "runs" / run_id / "pricing.json"
        with open(pricing_file, "w") as f:
            json.dump({"gpt-4": {"input": 30.0, "output": 60.0}}, f)

        start = time.perf_counter()
        for _ in range(1000):
            telemetry.load_pricing_config()
        end = time.perf_counter()
        print(f"load_pricing_config x 1000: {end - start:.4f}s")

def bench_redact():
    text = "This is a log line with an API key: sk-1234567890abcdefghijklmnopqrstuvwxyz1234567890"
    start = time.perf_counter()
    for _ in range(1000):
        telemetry.redact_secrets(text)
    end = time.perf_counter()
    print(f"redact_secrets x 1000 (with secret): {end - start:.4f}s")

    text_no_secret = "This is a normal log line without any secrets."
    start = time.perf_counter()
    for _ in range(10000):
        telemetry.redact_secrets(text_no_secret)
    end = time.perf_counter()
    print(f"redact_secrets x 10000 (no secret): {end - start:.4f}s")

if __name__ == "__main__":
    bench_pricing()
    bench_redact()

def bench_save_state():
    state = {
        "run_id": "bench_run",
        "status": "running",
        "counters": {"c1": 1, "c2": 2},
        "usage": {"u1": 10, "u2": 20},
        "updated_at": "2024-03-20T12:00:00Z"
    }
    with tempfile.TemporaryDirectory() as tmp_dir:
        telemetry.AUTOTRAIN_DIR = tmp_dir
        run_id = "bench_run"
        telemetry.init_telemetry(run_id=run_id, force=True)

        start = time.perf_counter()
        for _ in range(1000):
            telemetry.save_state(state, run_id=run_id)
        end = time.perf_counter()
        print(f"save_state x 1000: {end - start:.4f}s")

if __name__ == "__main__":
    bench_pricing()
    bench_redact()
    bench_save_state()
