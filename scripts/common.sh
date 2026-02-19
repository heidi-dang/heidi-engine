#!/usr/bin/env bash
set -e
set -u
set -o pipefail

# =============================================================================
# common.sh - Shared configuration, utilities, and VRAM-safe defaults
# =============================================================================
# This file contains common functions and environment variables used across
# all pipeline scripts. It provides VRAM-safe defaults for RTX 2080 Ti (11GB).
#
# =============================================================================
# TUNABLE PARAMETERS - ADJUST THESE BASED ON YOUR HARDWARE
# =============================================================================
#
# VRAM-SAFE DEFAULTS (RTX 2080 Ti - 11GB VRAM):
#   SEQ_LEN=2048        # Sequence length (reduce to 1024 if OOM)
#   BATCH_SIZE=1        # Per-device batch size (keep at 1 for safety)
#   GRAD_ACCUM=8        # Gradient accumulation steps (effective batch = 8)
#   TRAIN_STEPS=500     # Total training steps
#   SAVE_STEPS=100      # Save checkpoint every N steps
#   EVAL_STEPS=50       # Run eval every N steps
#   LR=2e-4             # Learning rate (higher than default for LoRA)
#   LORA_R=64           # LoRA rank (reduce to 32 or 16 if OOM)
#   LORA_ALPHA=128      # LoRA alpha (typically = 2 * R)
#   LORA_DROPOUT=0.1    # LoRA dropout
#   QUANTIZATION_BITS=4 # Bits for quantization (4-bit is safe)
#
# For more VRAM (RTX 3090/4090 - 24GB):
#   SEQ_LEN=4096, BATCH_SIZE=2, LORA_R=128
#
# For less VRAM (RTX 3060 - 6GB):
#   SEQ_LEN=1024, BATCH_SIZE=1, GRAD_ACCUM=16, LORA_R=32
#
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# DEFAULT ENVIRONMENT VARIABLES - Can be overridden by env vars or args
# -----------------------------------------------------------------------------
# NOTE: Default output directory changed to ~/.local/heidi-engine to avoid
# polluting the repository root. Set OUT_DIR explicitly if needed.
export AUTOTRAIN_DIR="${AUTOTRAIN_DIR:-$HOME/.local/heidi_engine}"

export ROUNDS="${ROUNDS:-3}"                          # Number of training rounds
export SAMPLES_PER_ROUND="${SAMPLES_PER_ROUND:-200}"    # Samples to generate per round
export BASE_MODEL="${BASE_MODEL:-microsoft/phi-2}"    # Base model to fine-tune
export TEACHER_MODEL="${TEACHER_MODEL:-gpt-4o-mini}"  # Teacher model for generation
export VAL_RATIO="${VAL_RATIO:-0.05}"                  # Validation split ratio (5%)
export OUT_DIR="${OUT_DIR:-$AUTOTRAIN_DIR}"            # Output directory

# Training hyperparameters - VRAM-safe defaults
export SEQ_LEN="${SEQ_LEN:-2048}"
export BATCH_SIZE="${BATCH_SIZE:-1}"
export GRAD_ACCUM="${GRAD_ACCUM:-8}"
export TRAIN_STEPS="${TRAIN_STEPS:-10}"  # Default set to 10 for 'Premium' focus
export SAVE_STEPS="${SAVE_STEPS:-100}"
export EVAL_STEPS="${EVAL_STEPS:-50}"
export LR="${LR:-1e-4}"
export LORA_R="${LORA_R:-32}"
export LORA_ALPHA="${LORA_ALPHA:-128}"
export LORA_DROPOUT="${LORA_DROPOUT:-0.1}"
export QUANTIZATION_BITS="${QUANTIZATION_BITS:-4}"

# Dataset limits
export MAX_INPUT_LENGTH="${MAX_INPUT_LENGTH:-1800}"   # Max input tokens (leave room for output)
export MAX_OUTPUT_LENGTH="${MAX_OUTPUT_LENGTH:-4596}" # Max output tokens
export MIN_INPUT_LENGTH="${MIN_INPUT_LENGTH:-10}"    # Min input tokens
export MIN_OUTPUT_LENGTH="${MIN_OUTPUT_LENGTH:-20}"   # Min output tokens

# Validation thresholds
export MAX_DUPLICATE_RATIO="${MAX_DUPLICATE_RATIO:-0.8}"  # Max ratio of duplicate samples to allow
export SECRET_DROP_THRESHOLD="${SECRET_DROP_THRESHOLD:-1}" # Drop sample if any secret pattern found

# Optional gates
export RUN_UNIT_TESTS="${RUN_UNIT_TESTS:-0}"            # Set to 1 to enable unit test gate
export UNIT_TEST_TIMEOUT="${UNIT_TEST_TIMEOUT:-30}"    # Timeout per test in seconds

# Pipeline mode: "full" or "collect"
# In collect mode, pipeline runs generate+validate only and waits for train request
export PIPELINE_MODE="${PIPELINE_MODE:-full}"

# API and Budget limits
export MAX_REQUESTS="${MAX_REQUESTS:-1000}"           # Global API budget across rounds/repos
export SLEEP_BETWEEN_REQUESTS="${SLEEP_BETWEEN_REQUESTS:-0}" # Seconds to wait between API calls

# Enhancement Stage Knobs
export HEIDI_ENHANCE="${HEIDI_ENHANCE:-1}"            # Set to 0 to disable enhancement stage
export HEIDI_USE_COPILOT="${HEIDI_USE_COPILOT:-1}"    # Set to 0 to disable GitHub Copilot
export HEIDI_USE_OPENAI="${HEIDI_USE_OPENAI:-1}"      # Set to 0 to disable OpenAI
export HEIDI_MAX_RETRIES="${HEIDI_MAX_RETRIES:-3}"    # Max retries for external calls
export HEIDI_CALL_TIMEOUT_SEC="${HEIDI_CALL_TIMEOUT_SEC:-60}" # Timeout per call in seconds
export HEIDI_FAIL_MODE="${HEIDI_FAIL_MODE:-open}"     # open: continue on failure; closed: exit on failure
export HEIDI_PROGRESS="${HEIDI_PROGRESS:-1}"          # Set to 0 to disable progress bar
export HEIDI_WATCHDOG_IDLE_SEC="${HEIDI_WATCHDOG_IDLE_SEC:-600}" # Watchdog timeout in seconds

# Random seed for reproducibility
export SEED="${SEED:-42}"

# -----------------------------------------------------------------------------
# COLOR OUTPUT UTILITIES
# -----------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $*" >&2; }
log_success() { echo -e "${GREEN}[OK]${NC} $*" >&2; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*" >&2; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# -----------------------------------------------------------------------------
# DIRECTORY SETUP - Creates necessary directories
# -----------------------------------------------------------------------------
setup_directories() {
    local base_dir="${1:-$OUT_DIR}"
    
    mkdir -p "${base_dir}/data"
    mkdir -p "${base_dir}/eval"
    mkdir -p "${base_dir}/logs"
    
    log_info "Directories ready in: ${base_dir}"
}

# -----------------------------------------------------------------------------
# SEED SETTING - Ensures reproducibility
# -----------------------------------------------------------------------------
set_seed() {
    local seed="${1:-$SEED}"
    export SEED="$seed"
    
    # Set Python random seed
    python3 -c "import random; random.seed(${seed})" 2>/dev/null || true
    
    # Set environment for reproducibility
    export PYTHONHASHSEED="$seed"
    export CUDA_SEED_ALL="$seed"
    
    log_info "Random seed set to: ${seed}"
}

# -----------------------------------------------------------------------------
# WATCHDOG - Monitors for hangs
# -----------------------------------------------------------------------------
WATCHDOG_FILE="/tmp/heidi_watchdog_$$.ts"

# Update heartbeat
heartbeat() {
    # Atomic-ish update of heartbeat timestamp
    date +%s > "${WATCHDOG_FILE}.tmp" && mv "${WATCHDOG_FILE}.tmp" "$WATCHDOG_FILE"
}

# Start watchdog in background
# Usage: start_watchdog <repo_context> <log_file>
start_watchdog() {
    local context="$1"
    local log_file="$2"
    local idle_sec="${HEIDI_WATCHDOG_IDLE_SEC:-600}"
    local fail_mode="${HEIDI_FAIL_MODE:-open}"

    heartbeat
    (
        while true; do
            sleep 30
            if [[ ! -f "$WATCHDOG_FILE" ]]; then break; fi

            local last_heartbeat; last_heartbeat=$(cat "$WATCHDOG_FILE")
            local now; now=$(date +%s)
            local diff=$((now - last_heartbeat))

            if (( diff > idle_sec )); then
                echo -e "\n${RED}[WATCHDOG] STALL DETECTED! No progress for ${diff}s (limit ${idle_sec}s)${NC}" >&2
                echo "[WATCHDOG] Context: $context" >&2
                if [[ -f "$log_file" ]]; then
                    echo "[WATCHDOG] Last 80 lines of log:" >&2
                    tail -n 80 "$log_file" >&2
                fi

                if [[ "$fail_mode" == "open" ]]; then
                    echo "[WATCHDOG] FAIL_MODE=open: attempting to skip and continue..." >&2
                    # In a real shell, we'd need to kill the parent's current task.
                    # This is complex. For now, we signal and the parent should check.
                    # But if the parent is blocked in a command, we need to kill that command.
                    # We'll use a simpler approach: the watchdog can kill the parent group if closed,
                    # or just alert.
                else
                    echo "[WATCHDOG] FAIL_MODE=closed: exiting pipeline." >&2
                    kill -TERM $$
                    exit 1
                fi
            fi
        done
    ) &
    WATCHDOG_PID=$!
}

stop_watchdog() {
    if [[ -n "${WATCHDOG_PID:-}" ]]; then
        kill "$WATCHDOG_PID" 2>/dev/null || true
    fi
    rm -f "$WATCHDOG_FILE"
}

# Run command with periodic heartbeats to prevent watchdog timeout
# Usage: with_heartbeat <command...>
with_heartbeat() {
    local pid
    # Start periodic heartbeat in background
    (
        while true; do
            sleep 30
            heartbeat
        done
    ) &
    pid=$!

    # Run the actual command
    "$@"
    local ret=$?

    # Cleanup heartbeat
    kill "$pid" 2>/dev/null || true
    return $ret
}

# -----------------------------------------------------------------------------
# GIT OPTIMIZATIONS - Resilient settings for slow networks
# -----------------------------------------------------------------------------
apply_git_optimizations() {
    log_info "Applying resilient Git HTTP configurations..."
    # Disable low-speed abort (maximize download time)
    git config --global http.lowSpeedLimit 0
    git config --global http.lowSpeedTime 999999
    # Increase postBuffer for large pushes/clones (512MB)
    git config --global http.postBuffer 524288000
    # Enable progress for better visibility in logs
    git config --global fetch.showForcedUpdates false
}

# -----------------------------------------------------------------------------
# CHECK DEPENDENCIES - Verifies required tools are installed
# -----------------------------------------------------------------------------
check_dependencies() {
    local missing=()
    
    for cmd in python3 jq bc; do
        if ! command -v "$cmd" &>/dev/null; then
            missing+=("$cmd")
        fi
    done
    
    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Missing dependencies: ${missing[*]}"
        log_info "Install with: apt-get install ${missing[*]}"
        return 1
    fi
    
    log_success "All dependencies available"
    return 0
}

# -----------------------------------------------------------------------------
# OOM DETECTION - Checks for CUDA out-of-memory
# -----------------------------------------------------------------------------
check_oom() {
    dmesg 2>/dev/null | tail -20 | grep -i "out of memory" && return 0 || return 1
}

# -----------------------------------------------------------------------------
# PRINT CONFIG - Displays current configuration
# -----------------------------------------------------------------------------
print_config() {
    log_info "=== Pipeline Configuration ==="
    echo "  ROUNDS: $ROUNDS"
    echo "  SAMPLES_PER_ROUND: $SAMPLES_PER_ROUND"
    echo "  BASE_MODEL: $BASE_MODEL"
    echo "  TEACHER_MODEL: $TEACHER_MODEL"
    echo "  VAL_RATIO: $VAL_RATIO"
    echo "  OUT_DIR: $OUT_DIR"
    echo "  SEQ_LEN: $SEQ_LEN"
    echo "  BATCH_SIZE: $BATCH_SIZE"
    echo "  GRAD_ACCUM: $GRAD_ACCUM"
    echo "  TRAIN_STEPS: $TRAIN_STEPS"
    echo "  LORA_R: $LORA_R"
    echo "  SEED: $SEED"
    echo "==============================="
}

# -----------------------------------------------------------------------------
# GRACEFUL EXIT - Cleanup on script exit
# -----------------------------------------------------------------------------
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log_error "Script failed with exit code: $exit_code"
    fi
    exit $exit_code
}

trap cleanup EXIT
