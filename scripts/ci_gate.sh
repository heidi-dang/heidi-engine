#!/usr/bin/env bash
# Workstream 14: CI-style build and test gate
set -euo pipefail

log() { echo -e "\033[0;34m[GATE]\033[0m $*"; }
error() { echo -e "\033[0;31m[ERROR]\033[0m $*"; }

log "1. Running Python compilation check..."
python3 -m compileall -q . || { error "Python compilation failed!"; exit 1; }

log "2. Building C++ targets..."
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j$(nproc) || { error "C++ build failed!"; exit 1; }

log "3. Reinstalling Python extension..."
python3 setup_cpp.py build_ext --inplace --force

log "4. Execution Gtest suite..."
./build/cpp_core_tests || { error "C++ unit tests failed!"; exit 1; }

log "5. Running Pytest suite..."
pytest -q tests/test_perf_baseline.py tests/test_budget_guardrails.py tests/test_sec_redteam.py || { error "Pytest suite failed!"; exit 1; }

log "SUCCESS: All gates passed."
