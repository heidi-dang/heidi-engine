import json
import os
import sys
from typing import Any, Dict, List


SCHEMA_VERSION = "1.0"
REQUIRED_KEYS = {
    "event_version", "ts", "run_id", "round", "stage", "level", 
    "event_type", "message", "counters_delta", "usage_delta", 
    "artifact_paths", "prev_hash"
}

def load_jsonl(path: str) -> List[Dict[str, Any]]:
    """
    Load samples from JSONL file with Phase 6 Zero-Trust validation.
    """
    samples = []

    with open(path, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                sample = json.loads(line)
                
                # Zero-Trust Validation (Lane D)
                missing = REQUIRED_KEYS - set(sample.keys())
                if missing:
                    print(f"[FATAL] Line {line_num}: Missing keys: {missing}", file=sys.stderr)
                    sys.exit(1)
                
                if sample["event_version"] != SCHEMA_VERSION:
                    print(f"[FATAL] Line {line_num}: Unsupported schema version {sample['event_version']}", file=sys.stderr)
                    sys.exit(1)
                
                samples.append(sample)
            except json.JSONDecodeError as e:
                print(f"[FATAL] Line {line_num}: JSON parse error: {e}", file=sys.stderr)
                sys.exit(1)

    return samples


def save_jsonl(samples: List[Dict[str, Any]], path: str) -> None:
    """
    Save samples to JSONL file.

    HOW IT WORKS:
        - Writes one JSON object per line
        - Creates parent directories if needed
    """
    dirname = os.path.dirname(path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)

    with open(path, "w") as f:
        for sample in samples:
            f.write(json.dumps(sample) + "\n")
