import time
import os
import shutil
from heidi_engine.telemetry import get_state, init_telemetry

# Set up a dummy run
test_dir = "/tmp/heidi_bench_state_again"
if os.path.exists(test_dir):
    shutil.rmtree(test_dir)
os.environ["AUTOTRAIN_DIR"] = test_dir
init_telemetry("bench_run")

# Warm up
get_state()

start = time.time()
for _ in range(1000):
    get_state()
end = time.time()
print(f"1000 calls to get_state: {end - start:.4f}s")
