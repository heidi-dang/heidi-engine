#!/usr/bin/env python3
import json
import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from heidi_engine.security import sign_record
except ImportError:
    print("Could not import heidi_engine.security")
    sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: sign_data.py <input_jsonl>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = input_path.with_suffix(".signed.jsonl")

    with input_path.open("r") as f_in, output_path.open("w") as f_out:
        for line in f_in:
            if not line.strip():
                continue
            record = json.loads(line)
            if "metadata" not in record:
                record["metadata"] = {}
            record["metadata"]["signature"] = sign_record(record)
            f_out.write(json.dumps(record) + "\n")

    # Replace original with signed
    os.replace(output_path, input_path)
    print(f"Signed records in {input_path}")

if __name__ == "__main__":
    main()
