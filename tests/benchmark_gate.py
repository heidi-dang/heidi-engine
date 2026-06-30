import json
import os
import time
import subprocess
import sys

def create_dummy_data(count=20):
    samples = []
    for i in range(count):
        samples.append({
            "id": f"sample_{i}",
            "instruction": "Print hello",
            "input": "",
            "output": f"```python\nimport time\nprint('hello {i}')\ntime.sleep(0.05)\n```",
            "metadata": {"task_type": "code_completion"}
        })

    os.makedirs("data", exist_ok=True)
    with open("data/benchmark_raw.jsonl", "w") as f:
        for s in samples:
            f.write(json.dumps(s) + "\n")

def run_benchmark():
    print("Running benchmark for 03_unit_test_gate.py...")
    start_time = time.time()
    result = subprocess.run([
        sys.executable, "scripts/03_unit_test_gate.py",
        "--input", "data/benchmark_raw.jsonl",
        "--output", "data/benchmark_tested.jsonl"
    ], capture_output=True, text=True)
    end_time = time.time()

    if result.returncode != 0:
        print(f"Benchmark failed: {result.stderr}")
        return

    print(f"Baseline time: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    create_dummy_data(20)
    run_benchmark()
