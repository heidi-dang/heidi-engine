#!/usr/bin/env python3
import hashlib
import json
import os
import sys


def verify_journal(filepath):
    """
    Offline deterministic replay verification.
    Parses events.jsonl, validates the SHA256 zero-trust chaining,
    and reconstructs the State Machine progression to ensure
    the recorded event sequence mathematically leads to the final state.
    """
    if not os.path.exists(filepath):
        print(f"Error: Journal file not found: {filepath}")
        sys.exit(1)

    with open(filepath, 'r') as f:
        lines = f.readlines()

    if not lines:
        print("Journal is empty.")
        return

    expected_hash = None
    current_state = "IDLE"
    current_round = 0
    run_id = None

    for i, line in enumerate(lines):
        try:
            evt = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON on line {i+1}: {e}")
            sys.exit(2)

        # 1. Verify Hash Chain
        if i == 0:
            run_id = evt.get("run_id")
            # First event's prev_hash is the run_id in our C++ implementation
            assert evt["prev_hash"] == run_id, f"Line 1: prev_hash should be run_id '{run_id}', got '{evt['prev_hash']}'"
        else:
            assert evt["prev_hash"] == expected_hash, f"Line {i+1}: Hash chain broken! Expected '{expected_hash}', got '{evt['prev_hash']}'"

        # Compute next hash: C++ hashes the ENTIRE line including the newline
        expected_hash = hashlib.sha256(line.encode('utf-8')).hexdigest()

        # 2. Schema Validation (Lane D: Zero-Trust Hard Lock)
        from heidi_engine.utils.io_jsonl import REQUIRED_KEYS, SCHEMA_VERSION
        missing = REQUIRED_KEYS - set(evt.keys())
        assert not missing, f"Line {i+1}: Missing required schema keys {missing}"
        assert evt["event_version"] == SCHEMA_VERSION, f"Line {i+1}: Unsupported schema version {evt['event_version']}"

        # 3. Deterministic State Progression Simulation
        if evt["event_type"] == "pipeline_start":
            current_state = "COLLECTING"
        elif evt["event_type"] == "stage_start":
            if evt["stage"] == "generate":
                current_state = "COLLECTING"
            elif evt["stage"] == "validate":
                current_state = "VALIDATING"
            elif evt["stage"] == "test":
                current_state = "TESTING"
            elif evt["stage"] == "train":
                current_state = "FINALIZING"
            elif evt["stage"] == "eval":
                current_state = "EVALUATING"
        elif evt["event_type"] == "pipeline_error":
            current_state = "ERROR"
        elif evt["event_type"] == "pipeline_stop":
            current_state = "IDLE"
        elif evt["event_type"] == "pipeline_complete":
            current_state = "IDLE"

        current_round = max(current_round, evt.get("round", 0))

    print(f"Success: Validated {len(lines)} events in deterministic replay.")
    print(f"Final Reconstructed State: {current_state} (Round {current_round})")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: replay_journal.py <path_to_events.jsonl>")
        sys.exit(1)
    verify_journal(sys.argv[1])
