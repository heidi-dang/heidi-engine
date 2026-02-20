#!/usr/bin/env python3
"""Deterministic train/val split for cleaned JSONL data.

Usage:
  python split_holdout.py --input clean.jsonl --val-ratio 0.1 --seed 42
  python split_holdout.py --in clean.jsonl --holdout 0.1 --out-train train.jsonl --out-eval val.jsonl

Writes:
  default: .local/ml/data/train/train.jsonl
           .local/ml/data/eval/val.jsonl
"""

import argparse
import json
import random
import subprocess
import sys
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", "--in", dest="input", required=True)
    p.add_argument("--val-ratio", "--holdout", dest="val_ratio", type=float, default=0.1)
    p.add_argument("--out-train", dest="out_train", default="./verified/ml/data/train/train.jsonl")
    p.add_argument("--out-eval", dest="out_eval", default=".local/ml/data/eval/val.jsonl")
    p.add_argument("--seed", dest="seed", type=int, default=42)
    p.add_argument(
        "--no-redaction-check",
        dest="no_redaction",
        action="store_true",
        help="Skip redaction check",
    )
    return p.parse_args()


def main():
    args = parse_args()
    inp = Path(args.input)
    if not inp.exists():
        print("Input file not found:", inp, file=sys.stderr)
        sys.exit(2)

    with inp.open() as f:
        samples = [json.loads(line) for line in f if line.strip()]

    if len(samples) == 0:
        print("No samples in input file.", file=sys.stderr)
        sys.exit(3)

    random.Random(args.seed).shuffle(samples)
    n = max(1, int(len(samples) * args.val_ratio))
    val = samples[:n]
    train = samples[n:]

    out_train = Path(args.out_train)
    out_eval = Path(args.out_eval)
    out_train.parent.mkdir(parents=True, exist_ok=True)
    out_eval.parent.mkdir(parents=True, exist_ok=True)

    with out_train.open("w") as f:
        for s in train:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    with out_eval.open("w") as f:
        for s in val:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    print(f"Wrote {len(train)} train and {len(val)} val samples (holdout={args.val_ratio})")

    if not args.no_redaction:
        # Run redaction check script if present
        redaction_script = Path(".local/ml/scripts/redaction_check.py")
        if redaction_script.exists():
            subprocess.run(
                [
                    sys.executable,
                    str(redaction_script),
                    "--file",
                    str(out_train),
                    "--file",
                    str(out_eval),
                ],
                check=True,
            )
        else:
            print("Warning: redaction_check.py not found — skipping redaction check")


if __name__ == "__main__":
    main()
