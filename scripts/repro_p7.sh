#!/usr/bin/env bash
set -euo pipefail

REPO="heidi-dang/heidi-engine"
WORKDIR="/tmp/heidi_phase7_$(date +%s)"
RUNTIME="$WORKDIR/runtime" # Use workdir for isolation

echo "[p7] clean workspace: $WORKDIR"
rm -rf "$WORKDIR"
mkdir -p "$WORKDIR/repo"
cd "$WORKDIR"

echo "[p7] clone (clean)"
git clone --filter=blob:none --no-tags "https://github.com/${REPO}.git" repo
cd repo
git submodule update --init --recursive
HEAD_SHA="$(git rev-parse HEAD)"
echo "HEAD_SHA=$HEAD_SHA"

echo "[p7] python env"
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -U pip wheel setuptools pybind11
python3 -m pip install -e ".[dev]" || python3 -m pip install -e .

# baseline gate
log() { echo -e "\033[0;35m[p7]\033[0m $*"; }
error() { echo -e "\033[0;31m[ERROR]\033[0m $*"; }

log "baseline verify_p6.sh"
chmod +x scripts/verify_p6.sh
./scripts/verify_p6.sh

# adversarial lane
mkdir -p "$RUNTIME/pending" "$RUNTIME/verified" "$RUNTIME/tmp"

log "1) REAL-mode refusal (Fail-Closed check)"
# Attempt to initialize C++ Core in REAL mode without required env vars
# It should set state to ERROR and remain idle/fail-closed.
( python3 -c "import heidi_cpp; import json; c = heidi_cpp.Core(); c.start('real'); s=json.loads(c.get_status_json()); exit(0 if s.get('state') == 'ERROR' else 1)" ) && log "PASSED: REAL mode refused start (Fail-Closed state reached)." || { error "REAL mode did NOT reach ERROR state without keys!"; exit 1; }

log "2) pending->trainer access (must refuse)"
echo '{"id":"1","instruction":"i","input":"in","output":"out","metadata":{}}' > "$RUNTIME/pending/attack.jsonl"
if python3 scripts/04_train_qlora.py --data "$RUNTIME/pending/attack.jsonl" --output "$RUNTIME/tmp/out" ; then
  error "trainer accepted pending data outside verified/ boundary"
  exit 1
else
  log "Trainer correctly refused unverified data via Boundary Control."
fi

log "3) symlink escape (must refuse)"
ln -sf /etc/passwd "$RUNTIME/pending/attack_symlink"
if python3 scripts/02_validate_clean.py --input "$RUNTIME/pending/attack_symlink" --output "$RUNTIME/tmp/clean.jsonl" ; then
  error "verify accepted symlink escape"
  exit 1
else
  log "Validator correctly blocked symlink escape outside root."
fi

log "4) replay soak (50x) deterministic chain"
# Generate a valid journal first
export OUT_DIR="$RUNTIME/tmp"
export RUN_ID="soak-$(date +%s)"
python3 -c "import heidi_cpp; c = heidi_cpp.Core(); c.init(); c.start('collect'); c.tick(10); c.shutdown()"
J_FILE="$OUT_DIR/events.jsonl"
# Replay it 50 times
for i in $(seq 1 50); do
  python3 scripts/replay_journal.py "$J_FILE" >/dev/null || { error "Replay failed at iter $i"; exit 1; }
done
log "50x Replay Soak PASSED."

log "5) test soak (10x)"
for i in $(seq 1 10); do
  pytest -q --disable-warnings || { error "Tests failed at iter $i"; exit 1; }
done
log "10x Test Soak PASSED."

echo "[p7] OK: Phase 7 lane completed on $HEAD_SHA"
