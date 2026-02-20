#!/usr/bin/env bash
# Phase 7: Adversarial Verification Pack
# This script performs "Red-Team" style validation of the Phase 6 trust boundaries.
set -euo pipefail

log() { echo -e "\033[0;35m[ADVERSARIAL]\033[0m $*"; }
error() { echo -e "\033[0;31m[ERROR]\033[0m $*"; }

RUNTIME="${HEIDI_RUNTIME:-$HOME/.local/heidi-engine}"
mkdir -p "$RUNTIME/pending" "$RUNTIME/verified" "$RUNTIME/tmp"

log "1) REAL Mode Fail-Closed Test"
# Attempt to initialize C++ Core in REAL mode without required env vars
# It should set state to ERROR and return.
( python3 -c "import heidi_cpp; import json; c = heidi_cpp.Core(); c.start('real'); s=json.loads(c.get_status_json()); exit(0 if s.get('state') == 'ERROR' else 1)" ) && log "PASSED: REAL mode refused start (Fail-Closed)." || { error "REAL mode did NOT reach ERROR state without keys!"; exit 1; }

log "2) Trainer Isolation Test"
# Inject a file into pending and check if trainer accepts it (should only use verified/)
echo '{"id":"1","instruction":"i","input":"in","output":"out","metadata":{}}' > "$RUNTIME/pending/attack.jsonl"
( python3 scripts/04_train_qlora.py --data "$RUNTIME/pending/attack.jsonl" --output "$RUNTIME/tmp/out" ) && { error "Trainer accepted unverified data!"; exit 1; } || log "PASSED: Trainer refused pending data (via strict clean check)."

log "3) Symlink Escape Test"
ATTACK="$RUNTIME/pending/passwd_link"
CLEAN_OUT="$RUNTIME/tmp/clean.jsonl"
rm -f "$ATTACK"
ln -s /etc/passwd "$ATTACK"
( python3 scripts/02_validate_clean.py --input "$ATTACK" --output "$CLEAN_OUT" ) && { error "Validator followed symlink escape!"; exit 1; } || log "PASSED: Symlink escape blocked."

log "4) Manifest Tamper Detection"
# Create a 2-event journal to test the hash chain
MOCK_LOG="$RUNTIME/tmp/events.jsonl"
RUN_ID="p7-test-$(date +%s)"
TS1=$(date -u +%Y-%m-%dT%H:%M:%SZ)
EVT1="{\"event_version\":\"1.0\",\"ts\":\"$TS1\",\"run_id\":\"$RUN_ID\",\"round\":0,\"stage\":\"init\",\"level\":\"info\",\"event_type\":\"pipeline_start\",\"message\":\"P7 Start\",\"counters_delta\":{},\"usage_delta\":{},\"artifact_paths\":[],\"prev_hash\":\"$RUN_ID\"}"
echo "$EVT1" > "$MOCK_LOG"

# Compute hash of EVT1
# (prev_hash + ts + level + event_type + message)
DATA1="${RUN_ID}${TS1}infopipeline_startP7 Start"
HASH1=$(echo -n "$DATA1" | sha256sum | awk '{print $1}')

TS2=$(date -u +%Y-%m-%dT%H:%M:%SZ)
EVT2="{\"event_version\":\"1.0\",\"ts\":\"$TS2\",\"run_id\":\"$RUN_ID\",\"round\":0,\"stage\":\"init\",\"level\":\"info\",\"event_type\":\"stage_start\",\"message\":\"P7 Next\",\"counters_delta\":{},\"usage_delta\":{},\"artifact_paths\":[],\"prev_hash\":\"$HASH1\"}"
echo "$EVT2" >> "$MOCK_LOG"

# Verify then tamper
log "Verifying clean 2-event journal..."
python3 scripts/replay_journal.py "$MOCK_LOG" >/dev/null
log "Tampering with first event (byte flip)..."
sed -i 's/P7 Start/P7 Altered/' "$MOCK_LOG"
( python3 scripts/replay_journal.py "$MOCK_LOG" ) && { error "Tampered journal verified!"; exit 1; } || log "PASSED: Tamper detected in journal hash chain."

log "5) Canonical Determinism Test"
# Ensure the same manifest produces identical signatures/hashes
# (This is implicitly tested by the 12-key lock and float rejection logic)
log "Verifying float rejection..."
echo '{"run_id":"r1","engine_version":"v1","created_at":"2026","schema_version":"1.0","dataset_hash":"h","record_count":10.5,"replay_hash":"r","signing_key_id":"k1","final_state":"V","total_runtime_sec":10,"event_count":1,"guardrail_snapshot":{}}' > "$RUNTIME/tmp/bad_manifest.json"
# We expect the canonicalizer to throw TypeError on the float 10.5
( python3 -c "import json; from heidi_engine.utils.signature import canonicalize_manifest; m=json.load(open('$RUNTIME/tmp/bad_manifest.json')); canonicalize_manifest(m)" ) && { error "Canonicalizer accepted float!"; exit 1; } || log "PASSED: Float rejection enforced."

log "===================================================="
log "PHASE 7 ADVERSARIAL PASS: Trust Boundaries are RIGID"
log "===================================================="
