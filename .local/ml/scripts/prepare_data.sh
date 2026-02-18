#!/usr/bin/env bash
# Wrapper: validate + dedupe + split into train/val for local workflow (hardened)
set -euo pipefail

usage() {
  echo "Usage: $0 path/to/raw.jsonl [--val-ratio 0.1]"
  exit 2
}

if [ "$#" -lt 1 ]; then
  usage
fi

RAW_PATH=$1
VAL_RATIO=0.1
shift || true
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --val-ratio) VAL_RATIO=$2; shift 2;;
    *) echo "Unknown arg: $1"; usage;;
  esac
done

if [ ! -f "$RAW_PATH" ]; then
  echo "ERROR: raw data not found: $RAW_PATH" >&2
  exit 3
fi

mkdir -p .local/ml/data/raw .local/ml/data/clean .local/ml/data/train .local/ml/data/eval
cp -f "$RAW_PATH" .local/ml/data/raw/raw.jsonl

raw_count=$(wc -l < .local/ml/data/raw/raw.jsonl || true)
if [ -z "$raw_count" ] || [ "$raw_count" -eq 0 ]; then
  echo "ERROR: raw input is empty" >&2
  exit 4
fi

echo "Raw samples: $raw_count"

# Sign records for local workflow (security requirement)
python .local/ml/scripts/sign_data.py .local/ml/data/raw/raw.jsonl

# Validate & clean (uses existing repo script)
python scripts/02_validate_clean.py --input .local/ml/data/raw/raw.jsonl --output .local/ml/data/clean/clean.jsonl

if [ ! -f .local/ml/data/clean/clean.jsonl ]; then
  echo "ERROR: cleaning failed - clean.jsonl not produced" >&2
  exit 5
fi

clean_count=$(wc -l < .local/ml/data/clean/clean.jsonl || true)
echo "Cleaned samples: $clean_count"

# Split holdout (deterministic)
python .local/ml/scripts/split_holdout.py --input .local/ml/data/clean/clean.jsonl --val-ratio "$VAL_RATIO" --seed 42

train_count=$(wc -l < .local/ml/data/train/train.jsonl || echo 0)
val_count=$(wc -l < .local/ml/data/eval/val.jsonl || echo 0)

# Redaction check (fail-fast)
python .local/ml/scripts/redaction_check.py --file .local/ml/data/train/train.jsonl --file .local/ml/data/eval/val.jsonl

echo "Summary:"
echo "  raw:  $raw_count"
echo "  clean:$clean_count"
echo "  train:$train_count"
echo "  val:  $val_count (holdout ratio: $VAL_RATIO)"

exit 0
