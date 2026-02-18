#!/usr/bin/env bash
# Simple wrapper to run QLoRA trainer with .local layout defaults (hardened + CI smoke)
set -euo pipefail

usage() {
  cat <<EOF
Usage: $0 [--out-dir DIR] [--base-model MODEL] [--data PATH|--train PATH] [--val-data PATH|--eval PATH] [--train-steps N] [--smoke-cpu]
Examples:
  $0 --train .local/ml/data/train/train.jsonl --val-data .local/ml/data/eval/val.jsonl --out-dir .local/ml/runs/run-1
  $0 --smoke-cpu --train-steps 2
EOF
  exit 2
}

OUT_DIR=".local/ml/runs/$(date +%Y%m%d-%H%M%S)"
BASE_MODEL="microsoft/phi-2"
DATA=".local/ml/data/train/train.jsonl"
VAL_DATA=".local/ml/data/eval/val.jsonl"
TRAIN_STEPS=500
SMOKE_CPU=0

while [[ "$#" -gt 0 ]]; do
  case $1 in
    --out-dir) OUT_DIR=$2; shift 2;;
    --base-model) BASE_MODEL=$2; shift 2;;
    --data|--train) DATA=$2; shift 2;;
    --val-data|--eval) VAL_DATA=$2; shift 2;;
    --train-steps) TRAIN_STEPS=$2; shift 2;;
    --smoke-cpu) SMOKE_CPU=1; shift;;
    --help) usage;;
    *) echo "Unknown arg: $1"; usage;;
  esac
done

# Validate input files
if [ ! -f "$DATA" ]; then
  echo "ERROR: training data not found: $DATA" >&2
  exit 3
fi
if [ ! -f "$VAL_DATA" ]; then
  echo "ERROR: validation data not found: $VAL_DATA" >&2
  exit 4
fi

train_count=$(wc -l < "$DATA" || echo 0)
val_count=$(wc -l < "$VAL_DATA" || echo 0)
if [ "$train_count" -eq 0 ]; then
  echo "ERROR: training data is empty" >&2
  exit 5
fi

mkdir -p "$OUT_DIR"

if [ "$SMOKE_CPU" -eq 1 ]; then
  echo "Running CPU-only smoke training (CI-friendly)"
  export CUDA_VISIBLE_DEVICES=""
  BASE_MODEL="sshleifer/tiny-gpt2"
  # tiny, CPU-friendly settings for CI/smoke tests
  python scripts/04_train_qlora.py \
    --data "$DATA" \
    --val-data "$VAL_DATA" \
    --output "$OUT_DIR" \
    --base-model "$BASE_MODEL" \
    --train-steps "${TRAIN_STEPS:-2}" \
    --quant-bits 0 \
    --batch-size 1 \
    --lora-r 8 \
    --lora-target-modules c_attn,c_proj \
    --seq-len 512 \
    --no-provenance
else
  python scripts/04_train_qlora.py \
    --data "$DATA" \
    --val-data "$VAL_DATA" \
    --output "$OUT_DIR" \
    --base-model "$BASE_MODEL" \
    --train-steps "$TRAIN_STEPS"
fi

echo "Training finished — adapter saved under $OUT_DIR"
echo "Summary: train=${train_count}, val=${val_count}, out=${OUT_DIR}"
