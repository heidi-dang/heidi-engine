#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# dashboard.sh - One-click Dashboard Deployment
# =============================================================================
#
# PURPOSE:
#     Launches the Heidi Engine real-time dashboard.
#     Automatically handles dependencies (rich) and environment setup.
#
# USAGE:
#     ./scripts/dashboard.sh [OPTIONS]
#
# =============================================================================

# Resolve project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Check python
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] python3 could not be found."
    exit 1
fi

# Check dependencies
echo "[INFO] Checking dependencies..."
python3 -c "import rich" 2>/dev/null || {
    echo "[INFO] Installing 'rich' library..."
    pip install rich
}

python3 -c "import psutil" 2>/dev/null || {
    echo "[INFO] Installing 'psutil' (optional) for system stats..."
    pip install psutil || true
}

# Set environment
export AUTOTRAIN_DIR="${AUTOTRAIN_DIR:-$HOME/.local/heidi_engine}"
export PYTHONPATH="$PROJECT_ROOT:${PYTHONPATH:-}"

echo "=============================================="
echo "HEIDI ENGINE DASHBOARD"
echo "=============================================="
echo "Refresh Rate: ${DASHBOARD_REFRESH_RATE:-2} Hz"
echo "Data Dir:     $AUTOTRAIN_DIR"
echo ""
echo "Press 'q' to quit."
echo "=============================================="

# Run dashboard module
python3 -m heidi_engine.dashboard "$@"
