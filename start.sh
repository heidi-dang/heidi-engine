#!/bin/bash
# =============================================================================
# Heidi Engine - Interactive Start Script
# =============================================================================
# This script sets up the environment and launches both the Heidi Daemon 
# and the Real-Time Terminal Dashboard.
# =============================================================================

set -e

# Default values
DEFAULT_PROVIDER="copilot"
DEFAULT_MODEL="gpt-5-mini"
DEFAULT_OUT_DIR="./autotrain_repos"
DEFAULT_SAMPLES=50
PARALLEL_DEFAULT=8

# Simple CLI parsing: allow `--parallel N` or `-p N` to override interactive default
PARALLEL=${PARALLEL:-}
while [[ $# -gt 0 ]]; do
    case "$1" in
        --parallel|-p)
            PARALLEL="$2"
            shift 2
            ;;
        --parallel=*)
            PARALLEL="${1#*=}"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--parallel N]"
            exit 0
            ;;
        *)
            break
            ;;
    esac
done

echo "----------------------------------------------------"
echo "  Heidi Engine: Interactive Setup & Launch"
echo "----------------------------------------------------"

# 1. Prompt for Configuration
# Only prompt if the vars are not already set (supports non-interactive env usage)
if [ -z "${RIG_NAME:-}" ]; then
    read -p "Enter Rig Name [default: manual_rig]: " RIG_NAME
fi
RIG_NAME=${RIG_NAME:-manual_rig}

if [ -z "${GITHUB_PAT:-}" ]; then
    read -s -p "Enter GitHub PAT (for repo discovery/cloning): " GITHUB_PAT
    echo
fi

if [ -z "${HEIDI_PROVIDER:-}" ]; then
    read -p "Select Provider [default: $DEFAULT_PROVIDER]: " HEIDI_PROVIDER
fi
HEIDI_PROVIDER=${HEIDI_PROVIDER:-$DEFAULT_PROVIDER}

if [ -z "${TEACHER_MODEL:-}" ]; then
    read -p "Select Teacher Model [default: $DEFAULT_MODEL]: " TEACHER_MODEL
fi
TEACHER_MODEL=${TEACHER_MODEL:-$DEFAULT_MODEL}

if [ -z "${SAMPLES_PER_ROUND:-}" ]; then
    read -p "Samples per Round [default: $DEFAULT_SAMPLES]: " SAMPLES_PER_ROUND
fi
SAMPLES_PER_ROUND=${SAMPLES_PER_ROUND:-$DEFAULT_SAMPLES}

if ! [[ "$SAMPLES_PER_ROUND" =~ ^[0-9]+$ ]]; then
        echo "[WARN] Invalid samples input '$SAMPLES_PER_ROUND'. Defaulting to $DEFAULT_SAMPLES."
        SAMPLES_PER_ROUND=$DEFAULT_SAMPLES
fi

# Interactive prompt for parallelism if not provided via CLI or env
if [ -z "${PARALLEL:-}" ]; then
    read -p "Parallel workers [default: $PARALLEL_DEFAULT]: " PARALLEL
fi
PARALLEL=${PARALLEL:-$PARALLEL_DEFAULT}

if [ -z "${COLLECT_ONLY:-}" ]; then
    read -p "Collect Data Only? (y/n) [default: y]: " COLLECT_ONLY
fi
COLLECT_ONLY=${COLLECT_ONLY:-y}

# 2. Export Environment Variables
export RIG_NAME
export GITHUB_PAT
export HEIDI_PROVIDER
export TEACHER_MODEL
export SAMPLES_PER_ROUND
mkdir -p "$DEFAULT_OUT_DIR"
export AUTOTRAIN_DIR="$(realpath "$DEFAULT_OUT_DIR")"

# Azure OpenAI configuration (optional)
read -p "Azure OpenAI Endpoint [default: none]: " AZURE_ENDPOINT
if [ -n "$AZURE_ENDPOINT" ]; then
    read -s -p "Azure OpenAI API Key: " AZURE_API_KEY
    echo
    read -p "Azure Deployment Name [default: gpt-4.1]: " AZURE_DEPLOYMENT
    AZURE_DEPLOYMENT=${AZURE_DEPLOYMENT:-gpt-4.1}
    export AZURE_OPENAI_ENDPOINT="$AZURE_ENDPOINT"
    export AZURE_OPENAI_API_KEY="$AZURE_API_KEY"
    export AZURE_OPENAI_DEPLOYMENT="$AZURE_DEPLOYMENT"
fi

# OpenAI API key (alternative)
read -s -p "OpenAI API Key (optional): " OPENAI_KEY
if [ -n "$OPENAI_KEY" ]; then
    export OPENAI_API_KEY="$OPENAI_KEY"
fi

echo "[DEBUG] Exported RIG_NAME=$RIG_NAME"
echo "[DEBUG] Exported HEIDI_PROVIDER=$HEIDI_PROVIDER"
echo "[DEBUG] Exported AUTOTRAIN_DIR=$AUTOTRAIN_DIR"

if [[ "$COLLECT_ONLY" == "y" || "$COLLECT_ONLY" == "Y" ]]; then
    export PIPELINE_MODE="collect"
    DAEMON_ARGS="--collect"
    # SPEED OPTIMIZATION: Use chosen parallelism for background tasks
    export HEIDI_JOB_COMMAND="./scripts/run_enhanced.sh --repos $SAMPLES_PER_ROUND --parallel ${PARALLEL:-$PARALLEL_DEFAULT}"
else
    export PIPELINE_MODE="full"
    DAEMON_ARGS=""
fi

# 3. Proxy Initialization (Total Masking)
echo "[INFO] Initializing proxy masking..."
if [[ -x "./proxy/get_proxy.sh" ]]; then
    GLOBAL_PROXY=$(./proxy/get_proxy.sh)
    if [[ -n "$GLOBAL_PROXY" ]]; then
        export http_proxy="$GLOBAL_PROXY"
        export https_proxy="$GLOBAL_PROXY"
        export all_proxy="$GLOBAL_PROXY"
        export HTTP_PROXY="$GLOBAL_PROXY"
        export HTTPS_PROXY="$GLOBAL_PROXY"
        export ALL_PROXY="$GLOBAL_PROXY"
        # Crucial: Don't proxy traffic to the VM itself or the WireGuard network
        # Includes: Localhost, VM LAN (172.31.0.0/20), WireGuard (10.7.0.0/24), 
        # and standard private ranges just in case.
        INTERNAL_IPS="127.0.0.1,localhost,0.0.0.0,10.7.0.0/24,10.66.66.0/24,172.16.0.0/12,192.168.0.0/16,10.0.0.0/8"
        export no_proxy="$INTERNAL_IPS"
        export NO_PROXY="$INTERNAL_IPS"
        echo "[SUCCESS] Global proxy set: $GLOBAL_PROXY"
        echo "[INFO] Internal traffic bypassing proxy: $INTERNAL_IPS"
    else
        echo "[WARN] No proxies found in proxy/.env. Running with direct IP."
    fi
else
    echo "[WARN] Proxy rotator script not found. Running with direct IP."
fi

# 4. Validation & Setup
if [ ! -f "./build/bin/heidid" ]; then
    echo "[ERROR] heidid binary not found. Please run ./scripts/build-heidid.sh first."
    exit 1
fi

mkdir -p "$AUTOTRAIN_DIR"
echo "Creating repos.txt with current directory if it doesn't exist..."
if [ ! -f "repos.txt" ]; then
    echo "$(pwd)" > repos.txt
fi

# 4. Launch Heidi Daemon in background
echo "[INFO] Starting heidid in background..."
# Build daemon args safely into an array to avoid word-splitting issues
DAEMON_CMD=("./build/bin/heidid" "--provider" "$HEIDI_PROVIDER")
if [ -n "${DAEMON_ARGS:-}" ]; then
    # split DAEMON_ARGS into words
    read -r -a _parts <<< "$DAEMON_ARGS"
    for p in "${_parts[@]}"; do
        DAEMON_CMD+=("$p")
    done
fi
"${DAEMON_CMD[@]}" > daemon_output.log 2>&1 &
DAEMON_PID=$!

# Register cleanup to kill daemon when dashboard quits
trap 'echo "[INFO] Stopping daemon..."; if [ -n "${DAEMON_PID:-}" ]; then kill "${DAEMON_PID}" >/dev/null 2>&1 || true; fi; exit' INT TERM EXIT

echo "[SUCCESS] Heidi Daemon started (PID: $DAEMON_PID)."
echo "----------------------------------------------------"
echo "  Launching Dashboard... (Press 'q' to stop all)"
echo "----------------------------------------------------"

# 5. Launch Dashboard
echo "[INFO] Waiting for daemon to initialize run directory..."
MAX_WAIT=120
WAITED=0
while [ ! -d "$AUTOTRAIN_DIR/runs/$RIG_NAME" ]; do
    sleep 1
    WAITED=$((WAITED + 1))
    if [ "$WAITED" -ge "$MAX_WAIT" ]; then
        echo "[ERROR] Daemon failed to initialize directory in $MAX_WAIT seconds."
        echo "Check daemon_output.log for details."
        if [ -n "${DAEMON_PID:-}" ]; then kill "$DAEMON_PID" >/dev/null 2>&1 || true; fi
        exit 1
    fi
done

python3 heidi_engine/dashboard.py
