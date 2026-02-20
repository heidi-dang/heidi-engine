import os
import json
from pathlib import Path

# Provide env variables for C++ Core to pick up
os.environ["RUN_ID"] = "test_cpp_run_123"
os.environ["OUT_DIR"] = "/tmp/heidi_cpp_test_dir"

# Clean up
out_dir = Path(os.environ["OUT_DIR"])
if out_dir.exists():
    for f in out_dir.iterdir():
        f.unlink()
out_dir.mkdir(parents=True, exist_ok=True)

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

import heidi_cpp

core = heidi_cpp.Core()
core.init()

# Start pipeline
core.start("full")

# One tick to simulate generation and validation
core.tick()

# Stop
core.shutdown()

print("C++ Core ran successfully.")

# Read outputs
events_file = out_dir / "events.jsonl"
state_file = out_dir / "state.json"

if events_file.exists():
    print(f"\n--- {events_file.name} ---")
    with open(events_file) as f:
        for line in f:
            print(line.strip())

if state_file.exists():
    print(f"\n--- {state_file.name} ---")
    with open(state_file) as f:
        print(f.read())
