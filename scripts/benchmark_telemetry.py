import time
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.getcwd())

from heidi_engine import telemetry

def benchmark_emit_event(n=100):
    # Initialize telemetry
    run_id = telemetry.init_telemetry(force=True)

    start_time = time.time()
    for i in range(n):
        telemetry.emit_event(
            event_type="progress",
            message=f"Processing item {i}",
            usage_delta={"input_tokens": 100, "output_tokens": 50},
            model="gpt-4o-mini"
        )
    end_time = time.time()

    total_time = end_time - start_time
    avg_time = total_time / n
    print(f"Emitted {n} events with usage_delta.")
    print(f"Total time: {total_time:.4f}s")
    print(f"Average time per event: {avg_time*1000:.4f}ms")

if __name__ == "__main__":
    benchmark_emit_event()
