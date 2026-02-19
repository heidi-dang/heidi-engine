
import time
import threading
import urllib.request
import os
import json
import sys
from pathlib import Path

# Add current directory to path so we can import heidi_engine
sys.path.append(os.getcwd())

from heidi_engine import telemetry

def benchmark():
    # Initialize telemetry
    # We need to make sure AUTOTRAIN_DIR is set to something local
    os.environ["AUTOTRAIN_DIR"] = str(Path(os.getcwd()) / ".local_test")
    run_id = telemetry.init_telemetry(force=True)

    # Start server
    port = 7780
    telemetry.start_http_server(port=port)
    time.sleep(2) # Wait for server to start

    url = f"http://127.0.0.1:{port}/status"

    iterations = 500
    start_time = time.perf_counter()
    for _ in range(iterations):
        with urllib.request.urlopen(url) as response:
            data = response.read()
            json.loads(data)
    end_time = time.perf_counter()

    total_time = end_time - start_time
    print(f"Total time for {iterations} requests: {total_time:.4f}s")
    print(f"Average time per request: {(total_time / iterations) * 1000:.4f}ms")

if __name__ == "__main__":
    benchmark()
