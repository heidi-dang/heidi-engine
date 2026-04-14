import time
import os
import shutil
import json
from pathlib import Path

# Mock state
test_dir = Path("/tmp/heidi_bench_state_no_cache")
run_dir = test_dir / "runs" / "bench_run"
run_dir.mkdir(parents=True, exist_ok=True)
state_file = run_dir / "state.json"
with open(state_file, "w") as f:
    json.dump({"run_id": "bench_run", "status": "running"}, f)

def get_state_no_cache():
    with open(state_file) as f:
        return json.load(f)

# Warm up
get_state_no_cache()

start = time.time()
for _ in range(1000):
    get_state_no_cache()
end = time.time()
print(f"1000 calls to get_state_no_cache: {end - start:.4f}s")
