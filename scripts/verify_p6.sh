#!/usr/bin/env bash
# Phase 6: Post-Merge Trust Verification Script
set -euo pipefail

log() { echo -e "\033[0;32m[TRUST]\033[0m $*"; }
warn() { echo -e "\033[0;33m[WARN]\033[0m $*"; }
error() { echo -e "\033[0;31m[ERROR]\033[0m $*"; }

log "Starting Zero-Trust Verification..."

# Determine python and pytest from venv if available, otherwise use system
if [ -n "${VIRTUAL_ENV:-}" ] && command -v pytest &>/dev/null; then
    PYTEST="pytest"
else
    PYTEST="python3 -m pytest"
fi

# 1. Build and Extension Check
log "1. Verifying Environment..."
if [ ! -f "heidi_cpp.cpython-312-x86_64-linux-gnu.so" ] && [ ! -f "heidi_cpp.so" ]; then
    warn "C++ extension not found. Reinstalling..."
    python3 setup_cpp.py build_ext --inplace
fi

# 2. Schema Lock Verification
log "2. Verifying Journal Schema Hard-Lock..."
$PYTEST -q tests/test_schema_lock.py || { error "Schema Lock violated!"; exit 1; }

# 3. Path Containment Verification
log "3. Verifying Path Containment (Symlink Escapes)..."
$PYTEST -q tests/test_sec_redteam.py || { error "Path Containment bypass detected!"; exit 1; }

# 4. Signature & Manifest Stability
log "4. Verifying Signature Determinism (Float rejection)..."
$PYTEST -q tests/test_signature.py || { error "Signature stability failure!"; exit 1; }

# 5. Keystore Hardening
log "5. Verifying Keystore Encryption & Tamper Detection..."
$PYTEST -q tests/test_keystore.py || { error "Keystore compromised!"; exit 1; }

# 6. Finalizer End-to-End
log "6. Verifying Finalizer (verified/ Sink Isolation)..."
$PYTEST -q tests/test_finalizer.py || { error "Finalizer isolation failure!"; exit 1; }

# 7. REAL Mode Gatekeeper
log "7. Verifying REAL Mode Gatekeeper..."
$PYTEST -q tests/test_doctor.py || { error "Gatekeeper bypass detected!"; exit 1; }

log "===================================================="
log "TRUST VERIFIED: Heidi Engine Phase 6 Invariants ACTIVE"
log "===================================================="
