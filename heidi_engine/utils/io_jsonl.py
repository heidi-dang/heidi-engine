import json
import os
import sys
from typing import Any, Dict, List


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    """
    Load samples from JSONL file.

    HOW IT WORKS:
        - Reads one JSON object per line
        - Skips empty lines
        - Reports parse errors with line numbers
    """
    samples = []

    with open(path, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                sample = json.loads(line)
                samples.append(sample)
            except json.JSONDecodeError as e:
                print(f"[WARN] Line {line_num}: JSON parse error: {e}", file=sys.stderr)
                continue

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
