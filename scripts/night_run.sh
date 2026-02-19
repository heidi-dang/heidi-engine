#!/usr/bin/env bash
set -e
set -u
set -o pipefail

# =============================================================================
# scripts/night_run.sh - One-command Night Runner (Sleep Mode)
# =============================================================================
#
# PURPOSE:
#     Starts a complete monitoring environment for collect mode (sleep mode).
#     Run this before bed; press "feed" when ready to train.
#
# USAGE:
#     ./scripts/night_run.sh [OPTIONS]
#
# OPTIONS:
#     --help, -h         Show this help
#     --rounds N         Number of rounds (default: 10)
#     --samples N        Samples per round (default: 50)
#
# FEATURES:
#     - Creates tmux session with 4 panes:
#       1. loop.sh in collect mode (generate + validate only)
#       2. Dashboard (real-time monitoring)
#       3. Menu (interactive control)
#       4. Tail events (live event stream)
#     - Exports AUTOTRAIN_DIR and OUT_DIR automatically
#     - Survives terminal close (tmux detached)
#
# REQUIREMENTS:
#     - tmux (recommended) or runs in background if tmux unavailable
#
# "SLEEP MODE" WORKFLOW:
#     1. Run: ./scripts/night_run.sh --rounds 10
#     2. Go to sleep
#     3. Pipeline collects data overnight (generate + validate)
#     4. In the morning, press 'f' in dashboard or use menu to "feed"
#     5. Pipeline proceeds to training while you sleep
#
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Default settings
ROUNDS="${ROUNDS:-10}"
SAMPLES="${SAMPLES:-50}"
SESSION_NAME="heidi-night"

# Set up directories
export AUTOTRAIN_DIR="${AUTOTRAIN_DIR:-$HOME/.local/heidi_engine}"
export OUT_DIR="${OUT_DIR:-$AUTOTRAIN_DIR}"

show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Start night runner (sleep mode) for collect-only pipeline.

OPTIONS:
    --help, -h         Show this help
    --rounds N         Number of rounds (default: $ROUNDS)
    --samples N        Samples per round (default: $SAMPLES)

EXAMPLES:
    # Start with defaults
    $0

    # Custom rounds
    $0 --rounds 20

ENVIRONMENT:
    AUTOTRAIN_DIR   Output directory (default: ~/.local/heidi-engine)
    OUT_DIR         Same as AUTOTRAIN_DIR

EOF
}

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --rounds)
            ROUNDS="$2"
            shift 2
            ;;
        --samples)
            SAMPLES="$2"
            shift 2
            ;;
        *)
            echo "Unknown: $1"
            show_help
            exit 1
            ;;
    esac
done

echo "=============================================="
echo "HEIDI NIGHT RUNNER (Sleep Mode)"
echo "=============================================="
echo ""
echo "AUTOTRAIN_DIR: $AUTOTRAIN_DIR"
echo "ROUNDS: $ROUNDS"
echo "SAMPLES: $SAMPLES"
echo ""
echo "This will create a tmux session with:"
echo "  - loop.sh (collect mode): Generate + validate only"
echo "  - Dashboard: Real-time monitoring"
echo "  - Menu: Interactive control"
echo "  - Tail events: Live event stream"
echo ""
echo "To train: Press 'f' in dashboard or use menu"
echo ""

# Create directories
mkdir -p "$AUTOTRAIN_DIR/data"
mkdir -p "$AUTOTRAIN_DIR/eval"

# Check for tmux
if command -v tmux &>/dev/null; then
    echo "Using tmux..."
    
    # Kill existing session if any
    tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true
    
    # Create new session
    tmux new-session -d -s "$SESSION_NAME" -c "$PROJECT_ROOT"
    
    # Split into 4 panes
    tmux split-window -h -t "$SESSION_NAME"
    tmux split-window -v -t "$SESSION_NAME"
    tmux split-window -v -t "$SESSION_NAME:0.1"
    
    # Pane 0: loop.sh in collect mode
    tmux send-keys -t "$SESSION_NAME:0.0" \
        "./scripts/loop.sh --mode collect --rounds $ROUNDS --samples $SAMPLES" C-m
    
    # Pane 1: Dashboard
    tmux send-keys -t "$SESSION_NAME:0.1" \
        "source .venv/bin/activate && python -m heidi_engine.dashboard" C-m
    
    # Pane 2: Menu
    tmux send-keys -t "$SESSION_NAME:0.2" \
        "python scripts/menu.py" C-m
    
    # Pane 3: Tail events
    tmux send-keys -t "$SESSION_NAME:0.3" \
        "tail -f $AUTOTRAIN_DIR/runs/*/events.jsonl 2>/dev/null || echo 'Waiting for events...'" C-m
    
    # Select first pane
    tmux select-pane -t "$SESSION_NAME:0.0"
    
    # Attach to session
    echo ""
    echo "Starting tmux session: $SESSION_NAME"
    echo "Commands:"
    echo "  Ctrl+b then d  - Detach (leave running)"
    echo "  Ctrl+b then q  - Show pane numbers"
    echo "  Ctrl+b then <n> - Switch to pane n"
    echo ""
    tmux attach -t "$SESSION_NAME"
    
else
    echo "tmux not found, running in background..."
    echo "NOTE: Install tmux for full experience with multiple panes"
    echo ""
    
    # Run loop in background
    nohup ./scripts/loop.sh --mode collect --rounds "$ROUNDS" --samples "$SAMPLES" \
        > "$AUTOTRAIN_DIR/loop.log" 2>&1 &
    LOOP_PID=$!
    echo "Loop PID: $LOOP_PID"
    
    # Run dashboard in background
    source .venv/bin/activate
    nohup python -m heidi_engine.dashboard > "$AUTOTRAIN_DIR/dashboard.log" 2>&1 &
    DASH_PID=$!
    echo "Dashboard PID: $DASH_PID"
    
    # Tail events in background
    nohup tail -f "$AUTOTRAIN_DIR/runs/"*/events.jsonl 2>/dev/null \
        > "$AUTOTRAIN_DIR/events.log" 2>&1 &
    TAIL_PID=$!
    echo "Tail PID: $TAIL_PID"
    
    echo ""
    echo "Running in background. Logs in $AUTOTRAIN_DIR/"
    echo "To stop: kill $LOOP_PID $DASH_PID $TAIL_PID"
fi
