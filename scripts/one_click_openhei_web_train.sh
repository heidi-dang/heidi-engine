#!/usr/bin/env bash
set -euo pipefail

# =========================
# One-click OpenHei Web + Path-B Collect + Train
# =========================

# ---- User defaults (override by exporting env vars before running) ----
OPENHEI_HOST="${OPENHEI_HOST:-0.0.0.0}"      # safer default
OPENHEI_PORT="${OPENHEI_PORT:-4100}"
OPENHEI_PASSWORD=

TEACHER_MODEL="${TEACHER_MODEL:-openai/gpt-5.2}"
OPENHEI_ATTACH="${OPENHEI_ATTACH:-http://${OPENHEI_HOST}:${OPENHEI_PORT}}"
# OPENHEI_AGENT optional; leave empty unless you have a known-good agent name
OPENHEI_AGENT="${OPENHEI_AGENT:-}"

STACK="${STACK:-python}"
MAX_REPOS="${MAX_REPOS:-50}"
ROUNDS="${ROUNDS:-2}"
SAMPLES_PER_RUN="${SAMPLES_PER_RUN:-100}"      # per repo per round
MAX_REQUESTS="${MAX_REQUESTS:-10000}"          # should match repos*rounds*samples

DATASET="${DATASET:-autotrain_repos/merged_dataset.jsonl}"
OUT_DIR="${OUT_DIR:-trained_output/adapter}"
TRAIN_STEPS="${TRAIN_STEPS:-1200}"
SAVE_STEPS="${SAVE_STEPS:-100}"
EVAL_STEPS="${EVAL_STEPS:-200}"

# ---- Helpers ----
die(){ echo "ERROR: $*" >&2; exit 1; }
need(){ command -v "$1" >/dev/null 2>&1 || die "Missing command: $1"; }

wait_http() {
  local url="$1" tries="${2:-80}"
  for _ in $(seq 1 "$tries"); do
    curl -sf "$url" >/dev/null && return 0
    sleep 0.2
  done
  return 1
}

banner() {
  echo
  echo "============================================================"
  echo "$*"
  echo "============================================================"
  echo
}

# ---- Preflight ----
need openhei
need curl
need python3

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# ---- Start OpenHei Web/Server ----
export OPENHEI_SERVER_PASSWORD="$OPENHEI_PASSWORD"

banner "1) Starting OpenHei web at http://${OPENHEI_HOST}:${OPENHEI_PORT} (password set)"
LOG="/tmp/openhei-serve.log"
openhei serve --hostname "$OPENHEI_HOST" --port "$OPENHEI_PORT" >"$LOG" 2>&1 &
srv=$!
cleanup(){ kill "$srv" >/dev/null 2>&1 || true; }
trap cleanup EXIT INT TERM

# Wait for /doc to come up (OpenHei server publishes it)
DOC_URL="http://${OPENHEI_HOST}:${OPENHEI_PORT}/doc"
if ! wait_http "$DOC_URL" 80; then
  echo "OpenHei did not become ready. Last 120 log lines:"
  tail -n 120 "$LOG" || true
  exit 1
fi

echo "OpenHei is up: $DOC_URL"
echo "Log: $LOG"
echo

# ---- Configure teacher backend (Path B) ----
export TEACHER_BACKEND=openhei
export TEACHER_MODEL="$TEACHER_MODEL"
export OPENHEI_ATTACH="$OPENHEI_ATTACH"
export MAX_REQUESTS="$MAX_REQUESTS"
if [[ -n "$OPENHEI_AGENT" ]]; then
  export OPENHEI_AGENT="$OPENHEI_AGENT"
else
  unset OPENHEI_AGENT || true
fi

banner "2) Collecting dataset (~${MAX_REPOS} repos, ${ROUNDS} rounds, ${SAMPLES_PER_RUN} samples/run ≈ $((MAX_REPOS*ROUNDS*SAMPLES_PER_RUN)) total)"
./scripts/loop_repos.sh \
  --stack "$STACK" \
  --max "$MAX_REPOS" \
  --rounds "$ROUNDS" \
  --samples "$SAMPLES_PER_RUN" \
  --collect --resume --dedupe \
  --sort stars --order desc

[[ -f "$DATASET" ]] || die "Dataset not found: $DATASET"

echo "Dataset ready: $DATASET"
echo "Lines: $(wc -l < "$DATASET" || true)"
echo

banner "3) Training QLoRA (${TRAIN_STEPS} steps) -> ${OUT_DIR} (resume-safe)"

ckpt="$(ls -1d "${OUT_DIR}"/checkpoint-* 2>/dev/null | sort -V | tail -n 1 || true)"
resume_args=()
if [[ -n "$ckpt" ]]; then
  echo "Found checkpoint: $ckpt"
  resume_args=(--resume-from-checkpoint "$ckpt")
fi

python3 ./scripts/04_train_qlora.py \
  --data "$DATASET" \
  --output "$OUT_DIR" \
  --train-steps "$TRAIN_STEPS" \
  --save-steps "$SAVE_STEPS" \
  --eval-steps "$EVAL_STEPS" \
  "${resume_args[@]}"

banner "DONE ✅  Re-run this script anytime to resume/retry safely."
echo "OpenHei web is still up until this script exits."
echo "OpenHei URL: http://${OPENHEI_HOST}:${OPENHEI_PORT}"