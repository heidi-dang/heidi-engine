#!/usr/bin/env python3
"""
scripts/train_only.sh - Launch QLoRA training on a specific dataset.

Usage:
  ./scripts/train_only.sh --data path/to/dataset.jsonl --out-dir ./trained_output

Options:
  --data FILE           Path to JSONL dataset (required)
  --out-dir DIR         Output directory (default: ./trained_output)
  --base-model MODEL    Base model (default: microsoft/phi-2)
  --steps N             Training steps (default: 500)
  --lr RATE             Learning rate (default: 2e-4)
  --val-ratio RATIO     Validation split ratio (default: 0.1)
  --batch-size N        Batch size (default: 1)
  --grad-accum N        Gradient accumulation steps (default: 8)
  --lora-r N            LoRA rank (default: 64)
  --seq-len N           Sequence length (default: 2048)
  --seed N              Random seed (default: 42)
"""

import argparse
import os
import random
import subprocess
import sys
from pathlib import Path

# Defaults
DEFAULT_BASE_MODEL = "microsoft/phi-2"
DEFAULT_STEPS = 500
DEFAULT_LR = 2e-4
DEFAULT_VAL_RATIO = 0.1
DEFAULT_BATCH_SIZE = 1
DEFAULT_GRAD_ACCUM = 8
DEFAULT_LORA_R = 64
DEFAULT_SEQ_LEN = 2048
DEFAULT_SEED = 42

def main():
    parser = argparse.ArgumentParser(description="Launch QLoRA training on a specific dataset.")
    parser.add_argument("--data", required=True, help="Path to JSONL dataset")
    parser.add_argument("--out-dir", default="./trained_output", help="Output directory")
    parser.add_argument("--base-model", default=DEFAULT_BASE_MODEL, help="Base model")
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS, help="Training steps")
    parser.add_argument("--lr", type=float, default=DEFAULT_LR, help="Learning rate")
    parser.add_argument("--val-ratio", type=float, default=DEFAULT_VAL_RATIO, help="Validation ratio")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="Batch size")
    parser.add_argument("--grad-accum", type=int, default=DEFAULT_GRAD_ACCUM, help="Gradient accumulation")
    parser.add_argument("--lora-r", type=int, default=DEFAULT_LORA_R, help="LoRA rank")
    parser.add_argument("--seq-len", type=int, default=DEFAULT_SEQ_LEN, help="Sequence length")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed")
    
    args = parser.parse_args()
    
    # Paths
    script_dir = Path(__file__).parent.absolute()
    project_root = script_dir.parent
    data_path = Path(args.data).absolute()
    out_dir = Path(args.out_dir).absolute()
    
    if not data_path.exists():
        print(f"[ERROR] Data file not found: {data_path}")
        sys.exit(1)
        
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Split Train/Val
    print(f"[INFO] Splitting dataset: {data_path}")
    
    # Read lines
    with open(data_path, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
    
    random.seed(args.seed)
    random.shuffle(lines)
    
    total = len(lines)
    val_size = int(total * args.val_ratio)
    if val_size < 1: val_size = 1 # ensure at least 1 validation sample
    train_size = total - val_size
    
    train_lines = lines[:train_size]
    val_lines = lines[train_size:]
    
    train_file = out_dir / "train.jsonl"
    val_file = out_dir / "val.jsonl"
    
    with open(train_file, 'w') as f:
        f.write('\n'.join(train_lines) + '\n')
        
    with open(val_file, 'w') as f:
        f.write('\n'.join(val_lines) + '\n')
        
    print(f"       Train: {len(train_lines)} samples -> {train_file}")
    print(f"       Val:   {len(val_lines)} samples -> {val_file}")
    
    # 2. Run Training
    print(f"\n[INFO] Starting Training...")
    print(f"       Steps: {args.steps}")
    print(f"       Model: {args.base_model}")
    print(f"       LoRA:  r={args.lora_r}")
    
    train_cmd = [
        "python3", str(script_dir / "04_train_qlora.py"),
        "--data", str(train_file),
        "--val-data", str(val_file),
        "--output", str(out_dir / "adapter"),
        "--base-model", args.base_model,
        "--seq-len", str(args.seq_len),
        "--batch-size", str(args.batch-size),
        "--grad-accum", str(args.grad_accum),
        "--train-steps", str(args.steps),
        "--save-steps", str(max(50, args.steps // 5)),
        "--eval-steps", str(max(50, args.steps // 5)),
        "--lora-r", str(args.lora_r),
        "--lr", str(args.lr),
        "--seed", str(args.seed)
    ]
    
    try:
        subprocess.run(train_cmd, check=True)
    except subprocess.CalledProcessError:
        print("[ERROR] Training failed.")
        sys.exit(1)
        
    # 3. Run Evaluation
    print(f"\n[INFO] Starting Evaluation...")
    eval_out = out_dir / "eval_report.json"
    
    eval_cmd = [
        "python3", str(script_dir / "05_eval.py"),
        "--adapter", str(out_dir / "adapter" / "final"),
        "--data", str(val_file),
        "--output", str(eval_out),
        "--base-model", args.base_model,
        "--seq-len", str(args.seq_len),
        "--temperature", "0.1",
        "--max-new-tokens", "512"
    ]
    
    try:
        subprocess.run(eval_cmd, check=True)
    except subprocess.CalledProcessError:
        print("[WARN] Evaluation failed (or no metrics reported).")

    print(f"\n[SUCCESS] Training pipeline complete!")
    print(f"          Adapter: {out_dir / 'adapter' / 'final'}")
    print(f"          Report:  {eval_out}")

if __name__ == "__main__":
    main()
